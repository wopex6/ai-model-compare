"""Atomic profile save and refuse-to-wipe on corrupt JSON."""
import json
import os
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_compare.medical_advisor_health_context import (
    HEALTH_DATA_DIR,
    HealthContextManager,
    HealthProfile,
    ProfileCorruptError,
)


def _user():
    return 'save_test_' + uuid.uuid4().hex[:10]


def test_save_is_atomic_when_dump_fails():
    user_id = _user()
    profile = HealthProfile(user_id)
    profile.data['name'] = 'Kept'
    profile.save()
    original = profile.file_path.read_text(encoding='utf-8')
    profile.data['name'] = 'Lost'
    try:
        with patch('json.dump', side_effect=OSError('disk full')):
            try:
                profile.save()
                raised = False
            except OSError:
                raised = True
        assert raised
        assert profile.file_path.read_text(encoding='utf-8') == original
        tmp = profile.file_path.with_name(profile.file_path.name + '.tmp')
        assert not tmp.exists()
    finally:
        profile.file_path.unlink(missing_ok=True)
        HealthContextManager._profiles.pop(user_id, None)


def test_corrupt_profile_is_not_replaced_with_blank():
    user_id = _user()
    HEALTH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = HEALTH_DATA_DIR / f'{user_id}.json'
    path.write_text('{not-json', encoding='utf-8')
    try:
        try:
            HealthProfile(user_id)
            raised = False
        except ProfileCorruptError:
            raised = True
        assert raised
        assert path.read_text(encoding='utf-8') == '{not-json'
    finally:
        path.unlink(missing_ok=True)
        HealthContextManager._profiles.pop(user_id, None)


def test_missing_profile_still_creates_default():
    user_id = _user()
    path = HEALTH_DATA_DIR / f'{user_id}.json'
    try:
        profile = HealthProfile(user_id)
        assert profile.data['user_id'] == user_id
        assert path.exists() is False or json.loads(path.read_text(encoding='utf-8'))
    finally:
        path.unlink(missing_ok=True)
        HealthContextManager._profiles.pop(user_id, None)
