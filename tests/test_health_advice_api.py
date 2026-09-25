"""End-to-end checks for the health advice/reminder endpoints.

Uses Flask's test client with a session cookie for auth and an injected fake chat
function, so no network or real model call happens. The point is to prove the
routes wire up to the insight engine and write provenance back to disk correctly.
"""
import json
import os
import sys
import unittest
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from ai_compare import health_insights as hi
from ai_compare import medical_advisor_health_context as mahc
from ai_compare.medical_advisor_health_context import HealthContextManager, HEALTH_DATA_DIR

TEST_USER = '999999_advice_test'


class HealthAdviceApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.config['TESTING'] = True
        cls.client = app_module.app.test_client()

    def setUp(self):
        self.path = HEALTH_DATA_DIR / f'{TEST_USER}.json'
        HealthContextManager._profiles.pop(TEST_USER, None)
        if self.path.exists():
            self.path.unlink()

        # authenticate_token() falls back to the session cookie, which is the
        # supported path for download links. Use it instead of minting a JWT.
        with self.client.session_transaction() as sess:
            sess['user_id'] = TEST_USER
            sess['username'] = 'advice-test'

    def tearDown(self):
        HealthContextManager._profiles.pop(TEST_USER, None)
        if self.path.exists():
            self.path.unlink()

    def seed(self, data):
        HEALTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
        profile = HealthContextManager.get_profile(TEST_USER)
        profile.data.update(data)
        profile.save()
        return profile

    # ---------- overview ----------

    def test_overview_is_free_and_complete(self):
        self.seed({'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'reference_range': '0 - 3.0',
             'date': date.today().isoformat()},
        ]})
        resp = self.client.get('/api/health-profile/overview')
        self.assertEqual(resp.status_code, 200)
        ov = resp.get_json()['overview']
        for key in ('observations', 'reminders', 'reminder_counts', 'advice',
                    'settings', 'provenance', 'disclaimer'):
            self.assertIn(key, ov)
        # Opening the screen must not have generated AI advice.
        self.assertEqual(ov['advice']['suggestions'], [])
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertIsNone(stored.get('ai_advice'))

    def test_observations_report_out_of_range(self):
        self.seed({'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'reference_range': '0 - 3.0',
             'date': date.today().isoformat()},
        ]})
        body = self.client.get('/api/health-profile/observations').get_json()
        self.assertTrue(any('LDL is high' == o['title'] for o in body['observations']))
        self.assertIn('not medical advice', body['disclaimer'])

    # ---------- reminders ----------

    def test_reminder_complete_and_snooze(self):
        due = (date.today() - timedelta(days=3)).isoformat()
        self.seed({'follow_ups': [{'title': 'See cardiologist', 'due_date': due}]})

        body = self.client.get('/api/health-profile/reminders').get_json()
        self.assertEqual(body['counts']['overdue'], 1)

        snoozed = self.client.post('/api/health-profile/reminder', json={
            'action': 'snooze', 'source_category': 'follow_ups', 'source_index': 0, 'days': 5
        }).get_json()
        self.assertEqual(snoozed['item']['due_date'],
                         (date.today() + timedelta(days=5)).isoformat())

        done = self.client.post('/api/health-profile/reminder', json={
            'action': 'complete', 'source_category': 'follow_ups', 'source_index': 0
        }).get_json()
        self.assertEqual(done['item']['status'], 'completed')
        self.assertEqual(done['reminders'], [])

    def test_reminder_rejects_bad_input(self):
        self.seed({'follow_ups': [{'title': 'x', 'due_date': date.today().isoformat()}]})
        self.assertEqual(self.client.post('/api/health-profile/reminder', json={
            'action': 'explode', 'source_category': 'follow_ups', 'source_index': 0
        }).status_code, 400)
        self.assertEqual(self.client.post('/api/health-profile/reminder', json={
            'action': 'complete', 'source_category': 'passwords', 'source_index': 0
        }).status_code, 400)
        self.assertEqual(self.client.post('/api/health-profile/reminder', json={
            'action': 'complete', 'source_category': 'follow_ups', 'source_index': 99
        }).status_code, 400)

    def test_ics_export_headers(self):
        self.seed({'follow_ups': [
            {'title': 'See cardiologist', 'due_date': (date.today() + timedelta(days=4)).isoformat()},
        ]})
        resp = self.client.get('/api/health-profile/reminders.ics')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/calendar', resp.headers['Content-Type'])
        self.assertIn('attachment', resp.headers['Content-Disposition'])
        self.assertIn('BEGIN:VCALENDAR', resp.get_data(as_text=True))

    # ---------- advice ----------

    def test_advice_is_cached_and_capped(self):
        self.seed({'conditions': [{'name': 'High cholesterol', 'status': 'active'}]})
        calls = []

        def fake_chat(messages, max_tokens=None, temperature=None, model=None):
            calls.append(messages)
            return json.dumps({'suggestions': [
                {'title': 'Discuss cholesterol', 'detail': 'Ask about your statin options.',
                 'cites': ['High cholesterol']}
            ]})

        original = mahc._health_ai_chat
        mahc._health_ai_chat = fake_chat
        try:
            first = self.client.get('/api/health-profile/advice?refresh=1').get_json()
            self.assertEqual(len(first['advice']['suggestions']), 1)
            self.assertEqual(len(calls), 1)

            # A plain GET must serve the cache, not spend another call.
            second = self.client.get('/api/health-profile/advice').get_json()
            self.assertTrue(second['advice']['cached'])
            self.assertEqual(len(calls), 1)
        finally:
            mahc._health_ai_chat = original

        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(stored['ai_advice_usage']['count'], 1)

    def test_advice_respects_opt_out(self):
        self.seed({
            'conditions': [{'name': 'High cholesterol', 'status': 'active'}],
            'advice_settings': {'ai_enabled': False},
        })
        calls = []

        def fake_chat(messages, **kwargs):
            calls.append(messages)
            return '{}'

        original = mahc._health_ai_chat
        mahc._health_ai_chat = fake_chat
        try:
            body = self.client.get('/api/health-profile/advice?refresh=1').get_json()
        finally:
            mahc._health_ai_chat = original
        self.assertEqual(calls, [])
        self.assertIn('turned off', body['advice']['reason'])

    # ---------- provenance ----------

    def test_verify_promotes_an_ai_item(self):
        profile = HealthContextManager.get_profile(TEST_USER)
        profile.ingest_source = hi.SOURCE_AI
        profile.data['conditions'] = [{'name': 'Suspected apnoea'}]
        profile.save()

        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(stored['conditions'][0]['source'], hi.SOURCE_AI)
        self.assertFalse(stored['conditions'][0]['verified_by_user'])

        body = self.client.post('/api/health-profile/item/verify', json={
            'category': 'conditions', 'index': 0, 'verified': True
        }).get_json()
        self.assertTrue(body['item']['verified_by_user'])
        self.assertEqual(body['provenance']['unverified_ai'], 0)

    def test_verify_rejects_bad_category(self):
        self.seed({'conditions': [{'name': 'Gout'}]})
        self.assertEqual(self.client.post('/api/health-profile/item/verify', json={
            'category': 'nonsense', 'index': 0
        }).status_code, 400)

    def test_prompt_context_warns_about_unconfirmed_items(self):
        profile = HealthContextManager.get_profile(TEST_USER)
        profile.ingest_source = hi.SOURCE_AI
        profile.data['conditions'] = [{'name': 'Suspected apnoea', 'status': 'active'}]
        profile.save()
        context = HealthContextManager.get_context_for_prompt(TEST_USER)
        self.assertIn('DATA PROVENANCE', context)
        self.assertIn('never present them as established fact', context)

    # ---------- settings & digest ----------

    def test_settings_round_trip_and_validation(self):
        self.seed({})
        body = self.client.put('/api/health-profile/advice-settings', json={
            'ai_enabled': False, 'reminders_enabled': False,
            'digest_frequency': 'monthly', 'locale': 'zh-HK'
        }).get_json()
        self.assertEqual(body['settings']['digest_frequency'], 'monthly')
        self.assertEqual(body['settings']['locale'], 'zh-HK')
        self.assertFalse(body['settings']['ai_enabled'])

        self.assertEqual(self.client.put('/api/health-profile/advice-settings',
                                         json={'digest_frequency': 'hourly'}).status_code, 400)
        self.assertEqual(self.client.put('/api/health-profile/advice-settings',
                                         json={'locale': 'klingon'}).status_code, 400)

    def test_digest_mark_seen_persists(self):
        self.seed({'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'added_at': datetime.now().isoformat()},
        ]})
        body = self.client.get('/api/health-profile/digest?mark_seen=1').get_json()
        self.assertEqual(body['digest']['added'].get('test_results'), 1)
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertTrue(stored['digest']['generated_at'])

    # ---------- confirmation queue ----------

    def _stale_med(self, name='Metformin'):
        old = (date.today() - timedelta(days=400)).isoformat()
        return {'name': name, 'dose': '500mg', 'frequency': 'daily',
                'status': 'active', 'started_on': old, 'last_confirmed_at': old}

    def test_queue_is_empty_for_a_fresh_profile(self):
        self.seed({'medications': [
            dict(self._stale_med(), last_confirmed_at=date.today().isoformat())]})
        body = self.client.get('/api/health-profile/review-queue').get_json()
        self.assertEqual(body['queue'], [])
        self.assertFalse(body['nudge_due'])

    def test_stale_item_is_offered_for_confirmation(self):
        self.seed({'medications': [self._stale_med()]})
        body = self.client.get('/api/health-profile/review-queue').get_json()
        self.assertEqual(len(body['queue']), 1)
        self.assertTrue(body['nudge_due'])
        self.assertEqual(body['queue'][0]['category'], 'medications')
        self.assertEqual(body['queue'][0]['values']['dose'], '500mg')

    def test_confirming_persists_and_clears_the_queue(self):
        self.seed({'medications': [self._stale_med()]})
        body = self.client.post('/api/health-profile/review-queue',
                                json={'action': 'confirm', 'category': 'medications',
                                      'index': 0}).get_json()
        self.assertEqual(body['queue'], [])
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertTrue(stored['medications'][0]['last_confirmed_at'])

    def test_reporting_a_change_records_history(self):
        self.seed({'medications': [self._stale_med()]})
        self.client.post('/api/health-profile/review-queue',
                         json={'action': 'changed', 'category': 'medications',
                               'index': 0, 'changes': {'dose': '1000mg'}})
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(stored['medications'][0]['dose'], '1000mg')
        self.assertEqual(stored['medications'][0]['history'][-1]['from'], '500mg')

    def test_stopping_retires_without_deleting(self):
        self.seed({'medications': [self._stale_med()]})
        self.client.post('/api/health-profile/review-queue',
                         json={'action': 'stopped', 'category': 'medications', 'index': 0})
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(len(stored['medications']), 1)
        self.assertEqual(stored['medications'][0]['status'], 'stopped')

    def test_bad_input_is_rejected(self):
        self.seed({'medications': [self._stale_med()]})
        for payload in ({'action': 'nonsense'},
                        {'action': 'confirm', 'category': 'nope', 'index': 0},
                        {'action': 'confirm', 'category': 'medications', 'index': 99},
                        {'action': 'changed', 'category': 'medications', 'index': 0,
                         'changes': 'not-an-object'}):
            resp = self.client.post('/api/health-profile/review-queue', json=payload)
            self.assertEqual(resp.status_code, 400, payload)

    def test_editing_an_item_counts_as_confirming_it(self):
        self.seed({'medications': [self._stale_med()]})
        self.client.put('/api/health-profile/item',
                        json={'category': 'medications', 'index': 0,
                              'updates': {'dose': '750mg'}})
        body = self.client.get('/api/health-profile/review-queue').get_json()
        self.assertEqual(body['queue'], [])

    # ---------- emergency card (single copy, derived) ----------

    def test_vitals_migrate_into_personal_and_lists(self):
        self.seed({'vitals': {
            'name': 'Test Person', 'age': '45', 'blood': 'O+',
            'conditions': 'diabetes, asthma', 'medications': 'metformin 500mg',
            'allergies': 'penicillin', 'history': 'Appendix out 2010',
            'doctors': 'Dr Smith, GP, 555-1234',
            'ecName': 'Jane', 'ecRel': 'Wife', 'ecPhone': '555-9999'}})
        body = self.client.get('/api/health-profile').get_json()
        p = body['profile']
        self.assertNotIn('vitals', p)
        self.assertEqual(p['name'], 'Test Person')
        self.assertEqual(p['personal']['blood_type'], 'O+')
        self.assertEqual(p['personal']['allergies'], 'penicillin')
        self.assertEqual(p['personal']['ec_phone'], '555-9999')
        self.assertEqual([c['name'] for c in p['conditions']], ['diabetes', 'asthma'])
        self.assertEqual([m['name'] for m in p['medications']], ['metformin 500mg'])

    def test_migration_never_overwrites_stated_values(self):
        self.seed({'name': 'Real Name',
                   'personal': {'age': '50', 'blood_type': 'A-'},
                   'vitals': {'name': 'Old Name', 'age': '40', 'blood': 'B+',
                              'ecPhone': '111'}})
        body = self.client.get('/api/health-profile').get_json()
        p = body['profile']
        self.assertEqual(p['name'], 'Real Name')
        self.assertEqual(p['personal']['age'], '50')
        self.assertEqual(p['personal']['blood_type'], 'A-')
        self.assertEqual(p['personal']['ec_phone'], '111')

    def test_emergency_card_derives_current_items_only(self):
        self.seed({'name': 'Test Person',
                   'personal': {'blood_type': 'O+', 'ec_phone': '555-9999'},
                   'conditions': [{'name': 'diabetes', 'status': 'active'},
                                  {'name': 'gout', 'status': 'resolved'}],
                   'medications': [{'name': 'metformin', 'dose': '500mg',
                                    'status': 'active'},
                                   {'name': 'old drug', 'status': 'stopped'}],
                   'diet': {'restrictions': ['ALLERGY: peanuts']}})
        body = self.client.get('/api/health-profile/emergency-card').get_json()
        card = body['card']
        self.assertEqual(card['name'], 'Test Person')
        self.assertEqual(card['blood'], 'O+')
        self.assertEqual(card['conditions'], ['diabetes'])
        self.assertEqual(card['medications'], [{
            'name': 'metformin', 'dose': '500mg', 'frequency': '',
            'label': 'metformin 500mg',
        }])
        self.assertEqual(card['allergies'], ['peanuts'])
        self.assertEqual(card['ec_phone'], '555-9999')

    def test_emergency_card_includes_paramedic_fields_and_derived_thinners(self):
        self.seed({
            'name': 'Test Person',
            'personal': {
                'date_of_birth': '1974-03-01',
                'weight': '72 kg',
                'advance_care': 'Not for CPR. Copy in the bedside drawer.',
                'implants': ['pacemaker 2019'],
                'anaphylaxis': 'Peanuts. EpiPen in the kitchen drawer.',
                'gp_name': 'Dr Smith',
                'gp_phone': '0295551234',
                'ec_phone': '0411111111',
                'language': 'Cantonese; limited English',
            },
            'medications': [
                {'name': 'apixaban', 'dose': '5mg', 'frequency': 'twice daily',
                 'status': 'active'},
                {'name': 'old warfarin', 'status': 'stopped'},
            ],
        })
        card = self.client.get('/api/health-profile/emergency-card').get_json()['card']
        self.assertEqual(card['date_of_birth'], '1974-03-01')
        self.assertEqual(card['age'], str(
            __import__('datetime').date.today().year - 1974 -
            ((__import__('datetime').date.today().month,
              __import__('datetime').date.today().day) < (3, 1))))
        self.assertEqual(card['weight'], '72 kg')
        self.assertEqual(card['advance_care'][:11], 'Not for CPR')
        self.assertEqual(card['implants'], ['pacemaker 2019'])
        self.assertEqual(card['anticoagulants'], ['apixaban 5mg'])
        self.assertEqual(card['medications'], [{
            'name': 'apixaban', 'dose': '5mg', 'frequency': 'twice daily',
            'label': 'apixaban 5mg twice daily',
        }])
        self.assertNotIn('old warfarin', ' '.join(m['label'] for m in card['medications']))
        self.assertEqual(card['gp_phone'], '0295551234')
        self.assertEqual(card['language'], 'Cantonese; limited English')
        vitals = self.client.get('/api/health-profile/vitals').get_json()['vitals']
        self.assertEqual(vitals['medications'], 'apixaban 5mg twice daily')

    def test_personal_accepts_emergency_fields(self):
        self.seed({})
        body = self.client.put('/api/health-profile', json={'personal': {
            'ec_name': 'Jane', 'ec_phone': '555-9999',
            'date_of_birth': '1974-03-01', 'weight': '72 kg',
            'advance_care': 'Not for CPR', 'implants': ['pacemaker'],
            'gp_phone': '0295551234',
            'medical_history': 'Appendix 2010', 'made_up_key': 'nope'}}).get_json()
        pers = body['profile']['personal']
        self.assertEqual(pers['ec_name'], 'Jane')
        self.assertEqual(pers['medical_history'], 'Appendix 2010')
        self.assertEqual(pers['date_of_birth'], '1974-03-01')
        self.assertEqual(pers['weight'], '72 kg')
        self.assertEqual(pers['advance_care'], 'Not for CPR')
        self.assertEqual(pers['implants'], ['pacemaker'])
        self.assertEqual(pers['gp_phone'], '0295551234')
        self.assertNotIn('made_up_key', pers)

    def test_personal_normalizes_free_typed_date_of_birth(self):
        self.seed({})
        body = self.client.put('/api/health-profile', json={'personal': {
            'date_of_birth': '15/3/1954'}}).get_json()
        self.assertEqual(body['profile']['personal']['date_of_birth'], '1954-03-15')
        card = self.client.get('/api/health-profile/emergency-card').get_json()['card']
        self.assertEqual(card['date_of_birth'], '1954-03-15')
        self.assertTrue(card['age'].isdigit())

    def test_prompt_context_has_medical_info_but_no_identifiers(self):
        self.seed({'name': 'Secret Name',
                   'personal': {'blood_type': 'O+', 'allergies': ['penicillin'],
                                'medical_history': 'Appendix 2010',
                                'doctors': 'Dr Smith', 'ec_phone': '555-9999'},
                   'conditions': [{'name': 'gout', 'status': 'resolved'}],
                   'lifestyle': {'exercise': ['walking daily'],
                                 'habits': ['smoking']}})
        ctx = HealthContextManager.get_context_for_prompt(TEST_USER)
        self.assertIn('penicillin', ctx)
        self.assertIn('Appendix 2010', ctx)
        self.assertIn('gout', ctx)
        self.assertIn('Past Conditions', ctx)
        self.assertIn('walking daily', ctx)
        self.assertNotIn('Secret Name', ctx)
        self.assertNotIn('555-9999', ctx)
        self.assertNotIn('Dr Smith', ctx)

    def test_prompt_includes_alerts_but_not_gp_phone(self):
        self.seed({'personal': {
            'weight': '72 kg', 'advance_care': 'Not for CPR',
            'implants': ['ICD'], 'gp_name': 'Dr Smith', 'gp_phone': '0295551234'}})
        ctx = HealthContextManager.get_context_for_prompt(TEST_USER)
        self.assertIn('72 kg', ctx)
        self.assertIn('Not for CPR', ctx)
        self.assertIn('ICD', ctx)
        self.assertNotIn('0295551234', ctx)
        self.assertNotIn('Dr Smith', ctx)

    def test_emergency_card_returns_pair_code_and_pair_endpoint_reads_it(self):
        self.seed({'name': 'Pair Person',
                   'personal': {'blood_type': 'O+'}})
        body = self.client.get('/api/health-profile/emergency-card').get_json()
        self.assertTrue(body['success'])
        self.assertEqual(body['card']['name'], 'Pair Person')
        code = body['pair_code']
        self.assertGreaterEqual(len(code), 20)
        self.assertNotIn('pair_code', body['card'])
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertEqual(stored.get('emergency_pair_token'), code)

        guest = app_module.app.test_client()
        miss = guest.post('/api/health-profile/emergency-card/pair',
                          json={'token': 'not-a-real-setup-code-value'})
        self.assertEqual(miss.status_code, 404)
        hit = guest.post('/api/health-profile/emergency-card/pair',
                         json={'token': code})
        self.assertEqual(hit.status_code, 200)
        self.assertEqual(hit.get_json()['card']['name'], 'Pair Person')

    def test_prompt_packs_question_relevant_sections_and_language(self):
        foods = ['oatmeal'] * 80
        self.seed({
            'personal': {'allergies': ['penicillin'], 'language': 'Cantonese',
                         'blood_type': 'O+'},
            'test_results': [{'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01'}],
            'diet': {'daily_foods': foods},
            'diary': [{'title': 'Walked', 'content': 'park'}],
        })
        profile = HealthContextManager.get_profile(TEST_USER)
        packed = profile.format_for_prompt(max_chars=220, question='What does my LDL mean?')
        self.assertIn('penicillin', packed)
        self.assertIn('LDL', packed)
        self.assertNotIn('oatmeal', packed)
        ctx = HealthContextManager.get_context_for_prompt(TEST_USER, question='LDL')
        self.assertIn('Traditional Chinese', ctx)
        self.assertIn('same language', ctx)

        from ai_compare.medical_advisor_health_context import pack_prompt_sections
        always = 'ALLERGIES (must not be contradicted by advice): penicillin'
        labs = 'Recent Tests: LDL: 4.3'
        foods_line = 'Daily Foods: ' + ', '.join(['oats'] * 60)
        out = pack_prompt_sections([always, foods_line, labs],
                                   max_chars=len(always) + len(labs) + 8,
                                   question='LDL cholesterol')
        self.assertIn('penicillin', out)
        self.assertIn('LDL', out)
        self.assertNotIn('oats', out)

    def test_visit_brief_omits_stopped_meds_and_answered_questions(self):
        self.seed({
            'name': 'Pat',
            'personal': {'allergies': ['penicillin'], 'language': 'English'},
            'medications': [
                {'name': 'Warfarin', 'dose': '5mg', 'status': 'active'},
                {'name': 'Old statin', 'status': 'stopped'},
            ],
            'test_results': [
                {'test_name': 'LDL', 'value': '4.8', 'reference_range': '0-3.0',
                 'date': '2026-05-01'},
            ],
            'questions_for_doctor': [
                {'question': 'Can I change my statin?', 'answered': False},
                {'question': 'Old question', 'answered': True},
            ],
        })
        body = self.client.get('/api/health-profile/visit-brief').get_json()
        self.assertTrue(body['success'])
        brief = body['brief']
        self.assertEqual(brief['name'], 'Pat')
        blob = json.dumps(brief)
        self.assertIn('Warfarin', blob)
        self.assertNotIn('Old statin', blob)
        self.assertEqual(brief['abnormal_tests'][0]['flag'], 'high')
        questions = [q['question'] for q in brief['questions_for_doctor']]
        self.assertIn('Can I change my statin?', questions)
        self.assertNotIn('Old question', questions)

    def test_explain_test_route_uses_original_index(self):
        self.seed({
            'test_results': [
                {'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01',
                 'source': hi.SOURCE_DOCUMENT, 'verified_by_user': True},
            ],
            'conditions': [{'name': 'High cholesterol', 'status': 'active',
                            'source': hi.SOURCE_USER, 'verified_by_user': True}],
        })
        calls = []

        def fake_chat(messages, max_tokens=None, temperature=None, model=None):
            calls.append(messages)
            return json.dumps({'suggestions': [
                {'title': 'LDL note', 'detail': 'Your LDL is 4.3.', 'cites': ['LDL']},
            ]})

        original = mahc._health_ai_chat
        mahc._health_ai_chat = fake_chat
        try:
            miss = self.client.post('/api/health-profile/explain-test', json={})
            self.assertEqual(miss.status_code, 400)
            body = self.client.post('/api/health-profile/explain-test',
                                    json={'index': 0}).get_json()
        finally:
            mahc._health_ai_chat = original
        self.assertTrue(body['success'])
        self.assertEqual(body['explanation']['test_name'], 'LDL')
        self.assertEqual(body['explanation']['suggestions'][0]['title'], 'LDL note')
        stored = json.loads(self.path.read_text(encoding='utf-8'))
        self.assertIsNone(stored.get('ai_advice'))
        self.assertEqual(stored['ai_advice_usage']['count'], 1)


if __name__ == '__main__':
    unittest.main()
