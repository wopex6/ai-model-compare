"""Profile backup rotation, cross-worker merge, upload sniffing, retention flags."""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_compare.medical_advisor_health_context import (
    BACKUP_DIR,
    BACKUP_KEEP,
    HEALTH_DATA_DIR,
    HealthContextManager,
    HealthProfile,
    _canonicalize_lab_tables,
    _fill_test_defaults,
    merge_profiles,
)


def _user():
    return 'safety_test_' + uuid.uuid4().hex[:10]


def _cleanup(user_id):
    path = HEALTH_DATA_DIR / f'{user_id}.json'
    path.unlink(missing_ok=True)
    bdir = BACKUP_DIR / str(user_id)
    if bdir.exists():
        for f in bdir.glob('*.json'):
            f.unlink(missing_ok=True)
        try:
            bdir.rmdir()
        except OSError:
            pass
    HealthContextManager._profiles.pop(str(user_id), None)


def test_save_keeps_rotating_backups():
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['name'] = 'One'
        profile.save()
        profile.data['name'] = 'Two'
        profile.save()
        profile.data['name'] = 'Three'
        profile.save()
        bdir = BACKUP_DIR / str(user_id)
        copies = sorted(bdir.glob('*.json'))
        assert len(copies) >= 2
        # Oldest backup contains the first saved name, not the latest
        first = json.loads(copies[0].read_text(encoding='utf-8'))
        assert first['name'] == 'One'
        assert json.loads(profile.file_path.read_text(encoding='utf-8'))['name'] == 'Three'
    finally:
        _cleanup(user_id)


def test_backup_rotation_is_bounded():
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        for i in range(BACKUP_KEEP + 5):
            profile.data['name'] = f'v{i}'
            profile.save()
        copies = list((BACKUP_DIR / str(user_id)).glob('*.json'))
        assert len(copies) <= BACKUP_KEEP
    finally:
        _cleanup(user_id)


def test_foreign_write_is_merged_not_clobbered():
    """Worker A loads, worker B writes a med, worker A saves a condition:
    both changes must survive."""
    user_id = _user()
    try:
        worker_a = HealthProfile(user_id)
        worker_a.data['name'] = 'Base'
        worker_a.save()

        worker_b = HealthProfile(user_id)  # loads A's saved state
        worker_b.data.setdefault('medications', []).append(
            {'name': 'Metformin', 'added_at': datetime.now().isoformat()})
        worker_b.save()

        # A never reloaded — its save must merge B's medication, not erase it.
        worker_a.data.setdefault('conditions', []).append(
            {'name': 'T2 diabetes', 'added_at': datetime.now().isoformat()})
        worker_a.save()

        final = json.loads((HEALTH_DATA_DIR / f'{user_id}.json')
                           .read_text(encoding='utf-8'))
        med_names = [m.get('name') for m in final.get('medications', [])]
        cond_names = [c.get('name') for c in final.get('conditions', [])]
        assert 'Metformin' in med_names
        assert 'T2 diabetes' in cond_names
    finally:
        _cleanup(user_id)


def test_merge_helpers():
    base = {'medications': [{'name': 'A'}], 'name': 'x'}
    ours = {'medications': [{'name': 'A'}, {'name': 'B'}], 'name': 'x'}
    remote = {'medications': [{'name': 'A'}, {'name': 'C'}], 'name': 'y'}
    merged = merge_profiles(base, ours, remote)
    names = sorted(m['name'] for m in merged['medications'])
    assert names == ['A', 'B', 'C']
    assert merged['name'] == 'y'  # remote changed it, we did not -> remote


def test_merge_conflicting_scalar_prefers_ours():
    base = {'name': 'old'}
    ours = {'name': 'ours'}
    remote = {'name': 'theirs'}
    assert merge_profiles(base, ours, remote)['name'] == 'ours'


# --- upload content sniffing -------------------------------------------------

def test_magic_byte_check():
    import app as app_mod
    assert app_mod._file_matches_extension(b'%PDF-1.4 rest', '.pdf')
    assert app_mod._file_matches_extension(b'\x89PNG\r\n\x1a\nrest', '.png')
    assert app_mod._file_matches_extension(b'\xff\xd8\xff\xe0rest', '.jpg')
    assert app_mod._file_matches_extension(b'RIFFxxxxWEBPrest', '.webp')
    assert app_mod._file_matches_extension(b'GIF89arest', '.gif')
    assert app_mod._file_matches_extension(b'BMrest', '.bmp')
    assert not app_mod._file_matches_extension(b'not a pdf', '.pdf')
    assert not app_mod._file_matches_extension(b'%PDF-1.4', '.png')
    assert not app_mod._file_matches_extension(b'RIFFxxxxWAVE', '.webp')
    assert not app_mod._file_matches_extension(b'', '.pdf')


# --- retention flags ----------------------------------------------------------

def _profile_with_doc(days_old=400, keep=False):
    user_id = _user()
    profile = HealthProfile(user_id)
    doc = {
        'original_name': 'report.pdf',
        'stored_name': 'x_report.pdf',
        'stored_path': '',  # nonexistent -> counts as "file gone" branch, so set a real one
        'uploaded_at': (datetime.now() - timedelta(days=days_old)).isoformat(),
        'content_hash': 'abc',
        'keep_forever': keep,
    }
    return user_id, profile, doc


def test_keep_forever_survives_retention_cleanup(tmp_path):
    import app as app_mod
    user_id, profile, doc = _profile_with_doc(days_old=400, keep=True)
    real = tmp_path / 'report.pdf'
    real.write_bytes(b'%PDF-1.4')
    doc['stored_path'] = str(real)
    profile.data['uploaded_documents'] = [doc]
    profile.data['upload_settings'] = {'retention_days': 30}
    try:
        removed = app_mod._cleanup_expired_uploaded_documents(profile)
        assert removed == 0
        assert real.exists()
        assert profile.data['uploaded_documents'] == [doc]
    finally:
        _cleanup(user_id)


def test_expired_doc_is_removed_without_keep_flag(tmp_path):
    import app as app_mod
    user_id, profile, doc = _profile_with_doc(days_old=400, keep=False)
    real = tmp_path / 'report.pdf'
    real.write_bytes(b'%PDF-1.4')
    doc['stored_path'] = str(real)
    profile.data['uploaded_documents'] = [doc]
    profile.data['upload_settings'] = {'retention_days': 30}
    try:
        removed = app_mod._cleanup_expired_uploaded_documents(profile)
        assert removed == 1
        assert not real.exists()
        assert profile.data['uploaded_documents'] == []
    finally:
        _cleanup(user_id)


def test_recent_changes_and_expiring_docs():
    from ai_compare import health_insights
    today = datetime.now().date()
    data = {
        'upload_settings': {'retention_days': 30},
        'uploaded_documents': [
            {'original_name': 'old.pdf',
             'stored_name': 's1',
             'uploaded_at': (today - timedelta(days=20)).isoformat()},
            {'original_name': 'keep.pdf',
             'stored_name': 's2', 'keep_forever': True,
             'uploaded_at': (today - timedelta(days=100)).isoformat()},
        ],
        'medications': [
            {'name': 'Metformin',
             'added_at': (today - timedelta(days=3)).isoformat()},
        ],
        'conditions': [],
        'symptoms': [],
    }
    changes = health_insights.recent_changes(data, days=30, today=today)
    assert any(c['event'] == 'added' and c['name'] == 'Metformin' for c in changes)
    expiring = health_insights.expiring_documents(data, within_days=30, today=today)
    names = [d['original_name'] for d in expiring]
    assert 'old.pdf' in names and 'keep.pdf' not in names


# --- apply_extracted_data: everything shown in review must be saved -----------

def test_apply_extracted_saves_every_schema_key_and_extras():
    """The review screen renders every key the extractor returns. Whatever
    the user accepts must land in the profile — known keys in their proper
    store, extra item fields merged into free-text fields, and unknown
    top-level keys kept as a clinical note."""
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        extracted = {
            "foods": ["oats"],
            "food_notes": ["avoid salt"],
            "restrictions": ["grapefruit"],
            "medications": [{"name": "Aspirin", "dose": "100mg",
                             "purpose": "heart", "frequency": "daily"}],
            "supplements": [{"name": "Vitamin D", "dose": "1000IU",
                             "purpose": "bones"}],
            "symptoms": [{"description": "headache", "severity": "mild",
                          "triggers": ["stress"], "duration": "2 days"}],
            "conditions": [{"name": "Hypertension", "details": "stage 1",
                            "status": "active", "diagnosed_date": "2026-01-01"}],
            "test_results": [{"test_name": "eGFR", "value": "45 mL/min",
                              "reference_range": "60 - 200",
                              "date": "2026-09-09",
                              "flag": "L"}],
            "action_plans": [{"title": "Reduce salt", "steps": ["cook at home"]}],
            "next_steps": [{"title": "Repeat bloods", "due_date": "2026-12-01"}],
            "questions_for_doctor": [{"question": "Check dose?"}],
            "lifestyle_notes": ["walks daily"],
            "warnings": ["interaction risk"],
            "insights": [{"insight": "BP trending up", "category": "prognosis"}],
            "allergies": ["penicillin"],
            "personal": {"age": 64, "blood_type": "O+"},
            "procedures": [{"name": "Appendectomy", "date": "1990",
                            "notes": "uncomplicated"}],
            "family_history": ["father - prostate cancer"],
            "clinical_notes": [{"date": "2026-09-09", "note": "GP review"}],
            # Unknown top-level key — shown in review, must not vanish
            "lab_facility": "PathLab Central",
        }
        actions = profile.apply_extracted_data(extracted)
        assert actions, "nothing was applied"
        d = profile.data

        assert "oats" in d["diet"]["daily_foods"]
        assert "avoid salt" in d["diet"]["notes"]
        assert "grapefruit" in d["diet"]["restrictions"]
        assert any(r == "ALLERGY: penicillin" for r in d["diet"]["restrictions"])

        med = next(m for m in d["medications"] if m.get("name") == "Aspirin")
        assert "frequency" in str(med)

        assert any(s.get("name") == "Vitamin D" for s in d["supplements"])
        sym = next(s for s in d["symptoms"] if "headache" in s.get("description", ""))
        assert "duration" in str(sym)

        assert any(c.get("name") == "Hypertension" for c in d["conditions"])
        tr = next(t for t in d["test_results"] if t.get("test_name") == "eGFR")
        assert tr["date"] == "2026-09-09"
        assert "45" in tr["value"]
        # extra field 'flag' preserved in notes
        assert "flag" in (tr.get("notes") or "")

        assert any(p.get("title") == "Reduce salt" for p in d["action_plans"])
        assert any(f.get("title") == "Repeat bloods" for f in d["follow_ups"])
        assert any(q.get("question") == "Check dose?" for q in d["questions_for_doctor"])
        assert any("walks daily" in i.get("insight", "") for i in d["conversation_insights"])
        assert any("interaction risk" in i.get("insight", "") for i in d["conversation_insights"])
        assert any("BP trending up" in i.get("insight", "") for i in d["conversation_insights"])
        assert any("prostate cancer" in i.get("insight", "") for i in d["conversation_insights"])

        assert d["personal"]["age"] == 64
        assert d["personal"]["blood_type"] == "O+"
        assert any("[Procedure] Appendectomy" == c.get("name") for c in d["conditions"])
        assert any("GP review" in n for n in d["provider_notes"])
        # unknown key kept
        assert any("lab facility" in n.lower() and "PathLab Central" in n
                   for n in d["provider_notes"])
    finally:
        _cleanup(user_id)


# --- document viewing ---------------------------------------------------------

def test_view_document_serves_own_file_only(tmp_path):
    """The document endpoint must serve the user's stored file and refuse
    anything that is not registered in that user's profile."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        real = tmp_path / '20260901_ab12_report.pdf'
        real.write_bytes(b'%PDF-1.4 hello')
        profile.data['uploaded_documents'] = [{
            'original_name': 'report.pdf',
            'stored_name': real.name,
            'stored_path': str(real),
            'mime_type': 'application/pdf',
            'uploaded_at': datetime.now().isoformat(),
        }]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.get(f'/api/health-profile/document?stored_name={real.name}')
        assert resp.status_code == 200
        assert resp.data == b'%PDF-1.4 hello'

        # A file that exists on disk but is not in the profile must not
        # be served — the profile entry is the access check.
        resp = client.get('/api/health-profile/document?stored_name=not_in_profile.pdf')
        assert resp.status_code == 404
    finally:
        _cleanup(user_id)


def test_document_result_serves_stored_analysis(tmp_path):
    """Reviewing a stored document must return the saved analysis JSON —
    a file read, not another model call."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        result_file = tmp_path / 'hash1_result.json'
        result_file.write_text(json.dumps({'extracted': {'medications': [{'name': 'Aspirin'}]}}),
                               encoding='utf-8')
        text_file = tmp_path / 'hash1.txt'
        text_file.write_text('Aspirin 100mg daily', encoding='utf-8')
        profile.data['uploaded_documents'] = [{
            'original_name': 'report.pdf',
            'stored_name': 's_report.pdf',
            'uploaded_at': datetime.now().isoformat(),
            'result_path': str(result_file),
            'extracted_text_path': str(text_file),
        }]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.get('/api/health-profile/document-result?stored_name=s_report.pdf')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['pending_review']['medications'][0]['name'] == 'Aspirin'
        assert data['extracted_text'] == 'Aspirin 100mg daily'

        # Unknown document -> 404; document with no stored analysis -> 404
        assert client.get('/api/health-profile/document-result?stored_name=nope.pdf').status_code == 404
    finally:
        _cleanup(user_id)


def test_list_documents_newest_first():
    """GET /documents returns newest upload first, while the stored list
    order is untouched (the index-based delete fallback depends on it)."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['uploaded_documents'] = [
            {'original_name': 'older.pdf', 'stored_name': 's_old',
             'uploaded_at': '2025-01-01T10:00:00'},
            {'original_name': 'newest.pdf', 'stored_name': 's_new',
             'uploaded_at': '2026-09-09T10:00:00'},
            {'original_name': 'middle.pdf', 'stored_name': 's_mid',
             'uploaded_at': '2025-06-01T10:00:00'},
        ]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.get('/api/health-profile/documents')
        assert resp.status_code == 200
        names = [d['original_name'] for d in resp.get_json()['documents']]
        assert names == ['newest.pdf', 'middle.pdf', 'older.pdf']
        # Stored order unchanged — delete fallback addresses rows by index.
        stored = [d['stored_name']
                  for d in HealthProfile(user_id).data['uploaded_documents']]
        assert stored == ['s_old', 's_new', 's_mid']
    finally:
        _cleanup(user_id)


def test_duplicate_same_date_keeps_stored_value():
    """Same test + same date with a different value: the stored row was
    already reviewed, so the incoming value is discarded and only missing
    metadata is backfilled — re-scanning cannot clobber a verified number."""
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.add_test_result('Ferritin', '55 ug/L', '30 - 300', '2024-08-01')
        profile.add_test_result('Ferritin', '61 ug/L', '', '2024-08-01', 'second reading')
        rows = profile.data['test_results']
        assert len(rows) == 1
        assert '55' in rows[0]['value'] and '61' not in rows[0]['value']
        # ref range already present, notes were missing -> backfilled
        assert rows[0]['notes'] == 'second reading'

        # Same test on a different date is a genuinely new result
        profile.add_test_result('Ferritin', '61 ug/L', '30 - 300', '2024-09-01')
        assert len(profile.data['test_results']) == 2
    finally:
        _cleanup(user_id)


def test_same_date_different_units_are_not_duplicates():
    """'HbA1c (NGSP)' in % and 'HbA1c (IFCC)' in mmol/mol share the same
    canonical key (the qualifier is stripped), but they are different
    measurements — same date must not collapse them."""
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.add_test_result('HbA1c (NGSP)', '6.0 %', '4.0 - 6.0 %', '2026-09-09')
        profile.add_test_result('HbA1c (IFCC)', '42 mmol/mol', '20 - 42 mmol/mol', '2026-09-09')
        rows = profile.data['test_results']
        assert len(rows) == 2
        units = {r.get('unit') or r['value'] for r in rows}
        assert any('42' in str(u) for u in units)
    finally:
        _cleanup(user_id)


def test_name_merge_requires_same_unit_and_reference():
    """Folding a name variant onto the canonical name is a merge — it needs
    the same reference range and unit. 'Bicarb' measured in a different unit
    than the stored 'Bicarbonate' series must keep its own name."""
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.add_test_result('Bicarbonate', '24 mmol/L', '22 - 29 mmol/L', '2024-01-01')
        profile.add_test_result('Bicarb', '2.4 g/dL', '2.0 - 3.0 g/dL', '2024-02-01')
        names = [r['test_name'] for r in profile.data['test_results']]
        assert 'Bicarb' in names  # not folded onto the incompatible series

        # Same name+date+value is still one reading even if the ref was
        # transcribed differently.
        profile.add_test_result('Bicarbonate', '24 mmol/L', '22-29', '2024-01-01')
        assert len(profile.data['test_results']) == 2
    finally:
        _cleanup(user_id)


def test_update_item_persists_default_range_and_unit():
    """PUT /item accepts an explicit unit alongside reference_range — this is
    how the data manager stores a test's default range/unit on the newest
    row, and both must survive a reload."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['test_results'] = [
            {'test_name': 'Sodium', 'value': '140 mmol/L',
             'reference_range': '135 - 145', 'date': '2026-01-01'},
        ]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.put('/api/health-profile/item', json={
            'category': 'test_results',
            'index': 0,
            'updates': {'reference_range': '136 - 146', 'unit': 'mmol/L'}
        })
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

        row = HealthProfile(user_id).data['test_results'][0]
        assert row['reference_range'] == '136 - 146'
        assert row['unit'] == 'mmol/L'
        # Value and date untouched — defaults never rewrite history.
        assert row['value'] == '140 mmol/L'
        assert row['date'] == '2026-01-01'
    finally:
        _cleanup(user_id)


def test_update_item_blank_ref_marks_user_lock():
    """Blanking reference_range or unit through PUT /item is a deliberate
    user choice — the row gets ref_locked/unit_locked so the UI keeps it
    blank rather than substituting the group default. Import-produced
    blanks carry no lock and still inherit the default."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['test_results'] = [
            {'test_name': 'Sodium', 'value': '140 mmol/L',
             'reference_range': '135 - 145', 'unit': 'mmol/L',
             'date': '2026-01-01'},
        ]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.put('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0,
            'updates': {'reference_range': '', 'unit': ''}
        })
        assert resp.status_code == 200
        row = HealthProfile(user_id).data['test_results'][0]
        assert row['reference_range'] == ''
        assert row['unit'] == ''
        assert row['ref_locked'] is True
        assert row['unit_locked'] is True

        # A real value clears the lock again.
        resp = client.put('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0,
            'updates': {'reference_range': '135 - 145'}
        })
        assert resp.status_code == 200
        row = HealthProfile(user_id).data['test_results'][0]
        assert row['reference_range'] == '135 - 145'
        assert row['ref_locked'] is False
        # unit untouched this round — lock stays
        assert row['unit_locked'] is True
    finally:
        _cleanup(user_id)


def test_rename_test_name_sticks_across_reload():
    """Renaming a test (eAGh -> eAG) must survive the load-time canonicalizer,
    which otherwise prefers the longer stored name and learns an alias that
    flips the user's choice back. The pin also converges the rest of the
    series onto the chosen name."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['test_results'] = [
            {'test_name': 'eAGh', 'value': '5.4', 'reference_range': '4 - 6',
             'date': '2026-09-20'},
            {'test_name': 'eAGh', 'value': '5.1', 'reference_range': '4 - 6',
             'date': '2026-08-01'},
        ]
        profile.save()

        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.put('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0,
            'updates': {'test_name': 'eAG'}
        })
        assert resp.status_code == 200

        # A fresh load runs canonicalize_test_names() — the rename must hold,
        # and the pinned alias pulls the rest of the series along.
        rows = HealthProfile(user_id).data['test_results']
        assert [r['test_name'] for r in rows] == ['eAG', 'eAG']

        # A blank test name is rejected, not silently stored.
        resp = client.put('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0,
            'updates': {'test_name': '   '}
        })
        assert resp.status_code == 400
    finally:
        _cleanup(user_id)


def test_post_item_carries_unit_and_provenance():
    """POST /item for a test result must not silently drop fields beyond the
    five add_test_result arguments — a hand-entered unit, the user_entered
    source and verified_by_user all belong on the stored row."""
    import app as app_mod
    user_id = _user()
    try:
        HealthProfile(user_id).save()
        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.post('/api/health-profile/item', json={
            'category': 'test_results',
            'item': {'test_name': 'Sodium', 'value': '140',
                     'unit': 'mmol/L', 'reference_range': '135 - 145',
                     'date': '2026-09-09'}
        })
        assert resp.status_code == 200

        row = HealthProfile(user_id).data['test_results'][0]
        assert row['unit'] == 'mmol/L'
        assert row['source'] == 'user_entered'
        assert row['verified_by_user'] is True
    finally:
        _cleanup(user_id)


def test_wrapped_transposed_table_keeps_reference_and_unit():
    """OCR of a phone-width lab table wraps wide rows onto a second line, e.g.
    the Reference and Units cells land on a continuation line that does not
    start with '|'.  The canonicalizer must rejoin them and still recognise
    the transposed layout (dates as rows, test name as a column header)."""
    text = (
        '| Date | Time | Lab Id | S GLU (Fast) | Reference | Units |\n'
        '|---|---|---|---|---|---|\n'
        '|03-Apr-25 |0956 F |972432598 |5.3 |\n'
        '(3.6-6.0) |mmol/L |\n'
        '|03-Oct-25 |0809 |978881054 |5.4 | | |\n'
        '|20-Jan-26 |0815 F |981726833 |5.3 |\n'
        '(3.6-6.0) |mmol/L |\n'
    )
    out = _canonicalize_lab_tables(text)
    lines = [ln for ln in out.splitlines() if ln.strip().startswith('|')]
    # Transposed to: Test | <dates...> | Reference | Units
    assert 'S GLU (Fast)' in lines[0] or any('S GLU (Fast)' in ln for ln in lines)
    data = [ln for ln in lines if 'GLU' in ln][0]
    cells = [c.strip() for c in data.strip().strip('|').split('|')]
    assert cells[0] == 'S GLU (Fast)'
    assert cells[1:4] == ['5.3', '5.4', '5.3']
    assert cells[-2] == '(3.6-6.0)'
    assert cells[-1] == 'mmol/L'


def test_fill_test_defaults_backfills_blank_ref_and_unit():
    """Sibling rows of the same test inherit the populated Reference/Units;
    qualifier-distinct tests (NGSP vs IFCC) never borrow from each other."""
    results = [
        {'test_name': 'S GLU (Fast)', 'value': '5.3 mmol/L',
         'reference_range': '(3.6-6.0)', 'date': '2025-04-03'},
        {'test_name': 'S GLU (Fast)', 'value': '5.4',
         'reference_range': '', 'date': '2025-10-03'},
        {'test_name': 'HbA1c (NGSP)', 'value': '6.0 %',
         'reference_range': '(4-6)', 'date': '2025-04-03'},
        {'test_name': 'HbA1c (IFCC)', 'value': '42',
         'reference_range': '', 'date': '2025-04-03'},
    ]
    _fill_test_defaults(results)
    assert results[1]['reference_range'] == '(3.6-6.0)'
    assert 'mmol/L' in results[1]['value']
    # IFCC must not inherit the NGSP range or % unit
    assert results[3]['reference_range'] == ''
    assert '%' not in results[3]['value']


def test_uploaded_at_parse_normalizes_to_naive_utc():
    """uploaded_at may be naive UTC (old rows) or offset-aware (new rows).
    _parse_iso_datetime must normalise aware values to naive UTC so internal
    comparisons against datetime.now() (server TZ is UTC) never mix aware
    and naive — and so 09:34 +08:00 and 01:34Z are the same instant."""
    from app import _parse_iso_datetime
    naive = _parse_iso_datetime('2026-09-23T01:34:00')
    aware = _parse_iso_datetime('2026-09-23T01:34:00+00:00')
    offset = _parse_iso_datetime('2026-09-23T09:34:00+08:00')
    assert naive.tzinfo is None
    assert aware.tzinfo is None
    assert naive == aware == offset


def test_test_audit_records_add_edit_delete_and_window():
    """Every test-result mutation lands in test_audit with a timestamp; the
    endpoint filters by the configured window (default 30 days)."""
    import app as app_mod
    user_id = _user()
    try:
        HealthProfile(user_id).save()
        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        assert client.post('/api/health-profile/item', json={
            'category': 'test_results',
            'item': {'test_name': 'Sodium', 'value': '140',
                     'reference_range': '135 - 145', 'date': '2026-09-09'}
        }).status_code == 200
        assert client.put('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0,
            'updates': {'value': '142'}
        }).status_code == 200
        assert client.delete('/api/health-profile/item', json={
            'category': 'test_results', 'index': 0
        }).status_code == 200

        audit = HealthProfile(user_id).data.get('test_audit') or []
        assert [e['action'] for e in audit] == ['added', 'updated', 'deleted']
        assert all(e.get('at') for e in audit)
        change = audit[1]['detail']['changes'][0]
        assert (change['field'], change['from'], change['to']) == ('value', '140', '142')

        resp = client.get('/api/health-profile/test-audit')
        data = resp.get_json()
        assert data['days'] == 30
        assert len(data['entries']) == 3
        assert data['entries'][0]['action'] == 'deleted'  # newest first

        # An entry older than the window is filtered out.
        prof = HealthProfile(user_id)
        prof.data['test_audit'][0]['at'] = (
            datetime.now() - timedelta(days=100)).isoformat()
        prof.save()
        assert len(client.get('/api/health-profile/test-audit').get_json()['entries']) == 2
        assert len(client.get('/api/health-profile/test-audit?days=400')
                   .get_json()['entries']) == 3

        # The window is configurable through settings.
        assert client.put('/api/health-profile', json={
            'audit_settings': {'days': 7}}).status_code == 200
        assert HealthProfile(user_id).data['audit_settings']['days'] == 7
        assert client.get('/api/health-profile/test-audit').get_json()['days'] == 7
    finally:
        _cleanup(user_id)


def test_bulk_delete_documents():
    """DELETE /documents accepts a stored_names list and removes them all."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['uploaded_documents'] = [
            {'stored_name': 'a.pdf', 'original_name': 'a.pdf',
             'stored_path': '/nonexistent/a.pdf'},
            {'stored_name': 'b.pdf', 'original_name': 'b.pdf',
             'stored_path': '/nonexistent/b.pdf'},
            {'stored_name': 'c.pdf', 'original_name': 'c.pdf',
             'stored_path': '/nonexistent/c.pdf'},
        ]
        profile.save()
        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.delete('/api/health-profile/documents', json={
            'stored_names': ['a.pdf', 'b.pdf']})
        data = resp.get_json()
        assert resp.status_code == 200 and data['deleted'] == 2
        remaining = [d['stored_name']
                     for d in HealthProfile(user_id).data['uploaded_documents']]
        assert remaining == ['c.pdf']
    finally:
        _cleanup(user_id)


def test_apply_review_then_undo_removes_only_imported_rows():
    """Apply tags new rows with a batch id; undo removes exactly those and
    leaves pre-existing rows — even ones the merge edited — alone."""
    import app as app_mod
    user_id = _user()
    try:
        profile = HealthProfile(user_id)
        profile.data['test_results'] = [
            {'test_name': 'Sodium', 'value': '140',
             'reference_range': '135 - 145', 'date': '2026-01-01'},
        ]
        profile.save()
        app_mod.app.config['TESTING'] = True
        client = app_mod.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['username'] = 'safety-test'

        resp = client.post('/api/health-profile/apply-review', json={
            'extracted': {'test_results': [
                {'test_name': 'Potassium', 'value': '4.5', 'date': '2026-09-09'},
                {'test_name': 'Chloride', 'value': '102', 'date': '2026-09-09'},
            ]}
        })
        data = resp.get_json()
        assert resp.status_code == 200 and data['added_count'] == 2
        assert data['last_import']['batch']

        rows = HealthProfile(user_id).data['test_results']
        assert len(rows) == 3
        # Pre-existing row must NOT carry the batch tag.
        assert [r['test_name'] for r in rows if '_import_batch' not in r] == ['Sodium']

        resp = client.post('/api/health-profile/undo-import')
        data = resp.get_json()
        assert resp.status_code == 200 and data['removed'] == 2
        rows = HealthProfile(user_id).data['test_results']
        assert [r['test_name'] for r in rows] == ['Sodium']
        assert 'last_import' not in HealthProfile(user_id).data

        # Second undo is a clean no-op.
        assert client.post('/api/health-profile/undo-import').status_code == 400
    finally:
        _cleanup(user_id)


def test_dimensionless_test_drops_misattributed_concentration_unit():
    """OCR sometimes puts a neighbouring row's unit on Hct — a ratio test
    that can never carry g/L. The guard strips it; real units stay."""
    from ai_compare.medical_advisor_health_context import _drop_implausible_test_unit
    t = {'test_name': 'Haematocrit', 'value': '0.46 g/L'}
    _drop_implausible_test_unit(t)
    assert t['value'] == '0.46'
    # Percent is a legitimate Hct unit — kept
    t2 = {'test_name': 'Hct', 'value': '46 %'}
    _drop_implausible_test_unit(t2)
    assert t2['value'] == '46 %'
    # A non-dimensionless test keeps its concentration unit
    t3 = {'test_name': 'Haemoglobin', 'value': '145 g/L'}
    _drop_implausible_test_unit(t3)
    assert t3['value'] == '145 g/L'


def test_emergency_field_candidates_from_document_text():
    """Phone-only emergency fields are suggested from stored document text —
    names, addresses, Medicare numbers, insurers and member numbers."""
    import app as app_mod
    sample = (
        'TSE, WAI\n'
        '4 HIGHVALE CRES, BERWICK. 3806\n'
        'Phone: 0415151791\n'
        'Birthdate: 12/06/1962  Sex: M  Medicare Number: 2297496521\n'
        'Health Insurance: MEDIBANK  Member No: AB123456\n'
        'Medicare valid to: 05/2030\n'
    )
    out = app_mod._emergency_field_candidates([('report.pdf', sample)])
    assert 'Wai Tse' in out['full_name']
    assert out['date_of_birth'] == ['12/06/1962']
    assert any('HIGHVALE' in a for a in out['address'])
    assert '0415151791' in out['phone']
    assert out['medicare'] == ['2297496521']
    assert out['medicare_expiry'] == ['05/2030']
    assert 'Medibank' in out['insurer']
    assert 'AB123456' in out['insurance_member']


def test_emergency_field_candidates_empty_and_safe():
    import app as app_mod
    out = app_mod._emergency_field_candidates([('doc.txt', 'no identifiers here')])
    assert all(v == [] for v in out.values())
    out2 = app_mod._emergency_field_candidates([])
    assert all(v == [] for v in out2.values())


def test_push_subscriptions_roundtrip(tmp_path, monkeypatch):
    from ai_compare import health_push
    monkeypatch.setattr(health_push, 'SUBS_PATH', tmp_path / 'subs.json')
    monkeypatch.setattr(health_push, 'DATA_DIR', tmp_path)
    sub = {'endpoint': 'https://push.example.com/abc',
           'keys': {'p256dh': 'k1', 'auth': 'a1'}}
    assert health_push.add_subscription(21, sub)
    assert health_push.subscriptions_for('21')[0]['endpoint'].endswith('/abc')
    # Re-posting the same endpoint updates it, does not duplicate.
    assert health_push.add_subscription(21, sub)
    assert len(health_push.subscriptions_for('21')) == 1
    # Malformed subscriptions are rejected.
    assert not health_push.add_subscription(21, {'endpoint': 'http://x'})
    assert not health_push.add_subscription(21, {'endpoint': 'https://x/1'})
    health_push.remove_subscription(21, 'https://push.example.com/abc')
    assert health_push.subscriptions_for('21') == []


def test_push_dispatch_only_when_reminders_due(tmp_path, monkeypatch):
    import json as _json
    from datetime import date as _date
    from ai_compare import health_push
    monkeypatch.setattr(health_push, 'SUBS_PATH', tmp_path / 'subs.json')
    monkeypatch.setattr(health_push, 'DATA_DIR', tmp_path)
    health_push.add_subscription(21, {'endpoint': 'https://push.example.com/x',
                                      'keys': {'p256dh': 'k', 'auth': 'a'}})
    profile = {
        'advice_settings': {'notifications_enabled': False},
        'follow_ups': [{'title': 'Blood test', 'due_date': '2000-01-01'}],
    }
    (tmp_path / '21.json').write_text(_json.dumps(profile))
    calls = []
    send = lambda s, t, b, url='/dr-health': calls.append((s, t, b))
    result = health_push.dispatch_due_reminders(today=_date(2026, 9, 24), send=send)
    assert result['sent'] == 0 and calls == []
    profile['advice_settings']['notifications_enabled'] = True
    (tmp_path / '21.json').write_text(_json.dumps(profile))
    result = health_push.dispatch_due_reminders(today=_date(2026, 9, 24), send=send)
    assert result['sent'] == 1
    assert 'Blood test' in calls[0][2]


def test_push_dispatch_prunes_dead_subscription(tmp_path, monkeypatch):
    import json as _json
    from datetime import date as _date
    from ai_compare import health_push
    monkeypatch.setattr(health_push, 'SUBS_PATH', tmp_path / 'subs.json')
    monkeypatch.setattr(health_push, 'DATA_DIR', tmp_path)
    health_push.add_subscription(21, {'endpoint': 'https://push.example.com/dead',
                                      'keys': {'p256dh': 'k', 'auth': 'a'}})
    profile = {
        'advice_settings': {'notifications_enabled': True},
        'follow_ups': [{'title': 'Review meds', 'due_date': '2000-01-01'}],
    }
    (tmp_path / '21.json').write_text(_json.dumps(profile))

    class _Resp:
        status_code = 410

    class _Gone(Exception):
        response = _Resp()

    def dead_send(s, t, b, url='/dr-health'):
        raise _Gone('gone')

    result = health_push.dispatch_due_reminders(today=_date(2026, 9, 24), send=dead_send)
    assert result['pruned'] == 1
    assert health_push.subscriptions_for('21') == []


def test_analyze_parses_spirometry_style_table(monkeypatch):
    """Pre/Post-bronchodilator reports have Actual/Pred/%Pred columns, not
    dates — the parser must classify column roles instead of storing the
    column headers as dates."""
    import ai_compare.medical_advisor_health_context as m

    raw = '''PULMONARY FUNCTION TEST
| | Pre-Bronch | | | Post-Bronch | | |
| | Actual | Pred | %Pred | Actual | %Pred | %Chng |
| --- | --- | --- | --- | --- | --- | --- |
| FEV1 (L) | 0.96 | 1.62 | 59 | 1.30 | 80 | 36.2 |
| FVC (L) | 1.47 | 2.03 | 73 | 1.37 | 68 | -6.8 |
---- DIFFUSION ----
| | Actual | Pred | %Pred |
| --- | --- | --- | --- |
| DLCOunc (ml/min/mmHg) | 13.37 | 16.93 | 79 |
'''
    user_id = _user()
    monkeypatch.setattr(m, '_health_ai_chat', lambda *a, **k: '{}')
    try:
        out = m.HealthContextManager.analyze_and_store(user_id, raw, save=False)
        assert out.get('success'), out
        rows = out['extracted']['test_results']
        names = {r['test_name'] for r in rows}
        assert 'FEV1 (L) (Pre-Bronch)' in names and 'FEV1 (L) (Post-Bronch)' in names
        pre = next(r for r in rows if r['test_name'] == 'FEV1 (L) (Pre-Bronch)')
        assert pre['value'] == '0.96 L'
        assert '1.62' in pre['reference_range']
        assert '59%' in pre['notes']
        post = next(r for r in rows if r['test_name'] == 'FEV1 (L) (Post-Bronch)')
        assert post['value'] == '1.30 L' and '+36.2%' in post['notes']
        # Column labels are not dates, and predicted/% figures are never
        # standalone values.
        assert all(not r.get('date') for r in rows)
        assert all(r['value'] not in ('1.62', '59', '80', '36.2') for r in rows)
        dlco = next(r for r in rows if r['test_name'] == 'DLCOunc (ml/min/mmHg)')
        assert dlco['value'].lower() == '13.37 ml/min/mmhg'
    finally:
        _cleanup(user_id)
