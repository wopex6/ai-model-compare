"""Unit tests for item lifecycle, change history and the confirmation queue.

Pure Python: no network, no model calls, no disk.
"""
import unittest
from datetime import date, datetime, timedelta

from ai_compare import health_freshness as hf
from ai_compare import health_insights as hi


TODAY = date(2026, 6, 1)


def _days_ago(n):
    return (TODAY - timedelta(days=n)).isoformat()


def _med(name, confirmed_days_ago=None, **extra):
    item = {'name': name, 'status': 'active', 'dose': '5mg',
            'frequency': 'daily', 'added_at': _days_ago(400)}
    if confirmed_days_ago is not None:
        item['last_confirmed_at'] = _days_ago(confirmed_days_ago)
    item.update(extra)
    return item


class TestLifecycle(unittest.TestCase):
    def test_unset_status_counts_as_active(self):
        self.assertTrue(hf.is_active({'name': 'X'}))
        self.assertTrue(hf.is_active({'name': 'X', 'status': 'active'}))
        self.assertFalse(hf.is_active({'name': 'X', 'status': 'stopped'}))
        self.assertFalse(hf.is_active({'name': 'X', 'status': 'resolved'}))

    def test_backfill_is_idempotent_and_preserves_status(self):
        data = {'medications': [{'name': 'A', 'added_at': '2024-03-05T10:00:00'}],
                'conditions': [{'name': 'Gout', 'status': 'resolved'}]}
        self.assertEqual(hf.backfill_lifecycle(data), 2)
        self.assertEqual(data['medications'][0]['status'], 'active')
        self.assertEqual(data['medications'][0]['started_on'], '2024-03-05')
        # An already-resolved condition must not be revived by the backfill.
        self.assertEqual(data['conditions'][0]['status'], 'resolved')
        self.assertEqual(hf.backfill_lifecycle(data), 0)

    def test_backfill_does_not_fake_a_confirmation(self):
        """Backdating last_confirmed_at would hide every stale item."""
        data = {'medications': [{'name': 'A', 'added_at': '2020-01-01T00:00:00'}]}
        hf.backfill_lifecycle(data)
        self.assertIsNone(data['medications'][0].get('last_confirmed_at'))

    def test_end_item_keeps_the_record(self):
        item = _med('Metformin')
        hf.end_item(item, category='medications', on=TODAY)
        self.assertEqual(item['status'], 'stopped')
        self.assertEqual(item['ended_on'], '2026-06-01')
        self.assertEqual(item['name'], 'Metformin')  # not deleted

    def test_conditions_resolve_rather_than_stop(self):
        item = {'name': 'Gout', 'status': 'active'}
        hf.end_item(item, category='conditions', on=TODAY)
        self.assertEqual(item['status'], 'resolved')


class TestChangeHistory(unittest.TestCase):
    def test_change_is_logged_with_old_value(self):
        item = _med('Metformin')
        self.assertTrue(hf.record_change(item, 'dose', '10mg', hi.SOURCE_USER))
        self.assertEqual(item['dose'], '10mg')
        self.assertEqual(item['history'][0]['from'], '5mg')
        self.assertEqual(item['history'][0]['to'], '10mg')

    def test_identical_value_is_not_a_change(self):
        item = _med('Metformin')
        self.assertFalse(hf.record_change(item, 'dose', '5mg'))
        self.assertEqual(item.get('history', []), [])

    def test_filling_a_blank_is_not_logged_as_a_change(self):
        item = {'name': 'A', 'dose': ''}
        self.assertTrue(hf.record_change(item, 'dose', '5mg'))
        self.assertEqual(item.get('history', []), [])

    def test_history_is_bounded(self):
        item = _med('A')
        for i in range(hf.MAX_HISTORY + 10):
            hf.record_change(item, 'dose', str(i) + 'mg')
        self.assertEqual(len(item['history']), hf.MAX_HISTORY)


class TestMergeIncoming(unittest.TestCase):
    def test_trusted_source_updates_and_logs(self):
        item = _med('Metformin')
        result = hf.merge_incoming(item, {'dose': '10mg'}, hi.SOURCE_DOCUMENT, 'medications')
        self.assertTrue(result['updated'])
        self.assertEqual(item['dose'], '10mg')
        self.assertEqual(result['proposals'], [])

    def test_ai_inference_never_overwrites_a_stated_fact(self):
        item = _med('Metformin')
        result = hf.merge_incoming(item, {'dose': '10mg'}, hi.SOURCE_AI, 'medications')
        self.assertFalse(result['updated'])
        self.assertEqual(item['dose'], '5mg')
        self.assertEqual(result['proposals'][0]['to'], '10mg')

    def test_ai_may_still_fill_a_blank(self):
        item = {'name': 'A', 'dose': ''}
        result = hf.merge_incoming(item, {'dose': '5mg'}, hi.SOURCE_AI, 'medications')
        self.assertTrue(result['updated'])
        self.assertEqual(item['dose'], '5mg')

    def test_empty_incoming_values_are_ignored(self):
        item = _med('A')
        result = hf.merge_incoming(item, {'dose': '', 'purpose': None}, hi.SOURCE_USER)
        self.assertFalse(result['updated'])
        self.assertEqual(item['dose'], '5mg')


class TestReviewQueue(unittest.TestCase):
    def test_fresh_items_are_not_asked_about(self):
        data = {'medications': [_med('A', confirmed_days_ago=10)]}
        self.assertEqual(hf.build_review_queue(data, TODAY), [])

    def test_overdue_item_surfaces(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        queue = hf.build_review_queue(data, TODAY)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['label'], 'A')
        self.assertEqual(queue[0]['category'], 'medications')
        self.assertIn('Are you still taking A', queue[0]['question'])

    def test_ended_items_are_never_asked_about(self):
        data = {'medications': [_med('A', confirmed_days_ago=900, status='stopped')]}
        self.assertEqual(hf.build_review_queue(data, TODAY), [])

    def test_batch_is_capped(self):
        data = {'medications': [_med('M%d' % i, confirmed_days_ago=900)
                                for i in range(10)]}
        self.assertEqual(len(hf.build_review_queue(data, TODAY)), hf.MAX_BATCH)

    def test_medications_outrank_diet(self):
        """Age must not let a food preference out-rank a drug: the overdue
        ratio saturates so clinical weight decides among very stale items."""
        data = {
            'medications': [_med('Metformin', confirmed_days_ago=180)],
            'diet': {'restrictions': ['low salt']},
            'created_at': _days_ago(3650),
        }
        queue = hf.build_review_queue(data, TODAY, limit=5)
        self.assertEqual(queue[0]['category'], 'medications')

    def test_unverified_ai_items_rank_above_equivalent_confirmed_ones(self):
        plain = _med('Plain', confirmed_days_ago=200)
        guessed = _med('Guessed', confirmed_days_ago=200,
                       source=hi.SOURCE_AI, verified_by_user=False)
        data = {'medications': [plain, guessed]}
        queue = hf.build_review_queue(data, TODAY, limit=5)
        self.assertEqual(queue[0]['label'], 'Guessed')

    def test_snoozed_items_are_hidden_until_the_date_passes(self):
        item = _med('A', confirmed_days_ago=900)
        item['snoozed_until'] = (TODAY + timedelta(days=5)).isoformat()
        data = {'medications': [item]}
        self.assertEqual(hf.build_review_queue(data, TODAY), [])
        self.assertEqual(len(hf.build_review_queue(data, TODAY + timedelta(days=6))), 1)

    def test_diet_is_asked_about_per_section_not_per_entry(self):
        data = {'diet': {'daily_foods': ['rice', 'fish', 'tofu', 'eggs', 'kale']},
                'created_at': _days_ago(3650)}
        queue = hf.build_review_queue(data, TODAY, limit=10)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]['kind'], 'group')
        self.assertEqual(queue[0]['group_key'], 'diet.daily_foods')
        self.assertIn('+1 more', queue[0]['detail'])

    def test_empty_sections_are_not_asked_about(self):
        data = {'diet': {'daily_foods': []}, 'created_at': _days_ago(3650)}
        self.assertEqual(hf.build_review_queue(data, TODAY, limit=10), [])


class TestAdaptiveIntervals(unittest.TestCase):
    def test_confirming_unchanged_lengthens_the_interval(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        base = hf.horizon_days(data, 'medications')
        hf.apply_review_action(data, 'confirm', 'medications', 0, today=TODAY)
        self.assertGreater(hf.horizon_days(data, 'medications'), base)

    def test_reporting_a_change_shortens_the_interval(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        base = hf.horizon_days(data, 'medications')
        hf.apply_review_action(data, 'changed', 'medications', 0,
                               changes={'dose': '10mg'}, today=TODAY)
        self.assertLess(hf.horizon_days(data, 'medications'), base)
        self.assertEqual(data['medications'][0]['dose'], '10mg')
        self.assertEqual(data['medications'][0]['history'][0]['from'], '5mg')

    def test_interval_drift_is_bounded(self):
        data = {'medications': [_med('A', confirmed_days_ago=900)]}
        for _ in range(50):
            hf.apply_review_action(data, 'confirm', 'medications', 0, today=TODAY)
        ceiling = hf.BASE_HORIZON_DAYS['medications'] * hf.MAX_FACTOR
        self.assertLessEqual(hf.horizon_days(data, 'medications'), ceiling)

    def test_confirming_clears_the_item_from_the_queue(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        hf.apply_review_action(data, 'confirm', 'medications', 0, today=TODAY)
        self.assertEqual(hf.build_review_queue(data, TODAY), [])
        self.assertTrue(data['medications'][0]['verified_by_user'])

    def test_stopping_retires_the_item_without_deleting_it(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        hf.apply_review_action(data, 'stopped', 'medications', 0, today=TODAY)
        self.assertEqual(data['medications'][0]['status'], 'stopped')
        self.assertEqual(data['medications'][0]['ended_on'], '2026-06-01')
        self.assertEqual(len(data['medications']), 1)

    def test_stale_index_is_rejected_rather_than_corrupting_data(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        result = hf.apply_review_action(data, 'confirm', 'medications', 7, today=TODAY)
        self.assertFalse(result['ok'])

    def test_group_confirmation_is_recorded(self):
        data = {'diet': {'restrictions': ['low salt']}, 'created_at': _days_ago(3650)}
        result = hf.apply_review_action(data, 'confirm', group_key='diet.restrictions',
                                        today=TODAY)
        self.assertTrue(result['ok'])
        self.assertEqual(hf.build_review_queue(data, TODAY, limit=10), [])


class TestNudgeRateLimiting(unittest.TestCase):
    def test_no_nudge_when_nothing_is_overdue(self):
        data = {'medications': [_med('A', confirmed_days_ago=1)]}
        self.assertFalse(hf.nudge_due(data, TODAY))

    def test_nudge_when_something_is_overdue(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        self.assertTrue(hf.nudge_due(data, TODAY))

    def test_cooldown_suppresses_repeat_nudges(self):
        data = {'medications': [_med('A', confirmed_days_ago=200)]}
        hf.mark_nudged(data, datetime(2026, 6, 1))
        self.assertFalse(hf.nudge_due(data, TODAY))
        self.assertTrue(hf.nudge_due(data, TODAY + timedelta(days=hf.DEFAULT_COOLDOWN_DAYS)))

    def test_repeated_dismissal_backs_off_geometrically(self):
        data = {'medications': [_med('A', confirmed_days_ago=900)]}
        first = hf.review_prefs(data)['cooldown_days']
        for _ in range(3):
            hf.apply_review_action(data, 'dismiss', today=TODAY)
        self.assertGreater(hf.review_prefs(data)['cooldown_days'], first)
        self.assertLessEqual(hf.review_prefs(data)['cooldown_days'], hf.MAX_COOLDOWN_DAYS)

    def test_answering_resets_the_back_off(self):
        data = {'medications': [_med('A', confirmed_days_ago=900)]}
        for _ in range(3):
            hf.apply_review_action(data, 'dismiss', today=TODAY)
        hf.apply_review_action(data, 'confirm', 'medications', 0, today=TODAY)
        self.assertEqual(hf.review_prefs(data)['cooldown_days'], hf.DEFAULT_COOLDOWN_DAYS)
        self.assertEqual(hf.review_prefs(data)['consecutive_dismissals'], 0)

    def test_pause_suppresses_everything_until_it_expires(self):
        data = {'medications': [_med('A', confirmed_days_ago=900)]}
        hf.apply_review_action(data, 'pause', days=30, today=TODAY)
        self.assertFalse(hf.nudge_due(data, TODAY + timedelta(days=29)))
        self.assertTrue(hf.nudge_due(data, TODAY + timedelta(days=31)))

    def test_summary_reports_counts_without_the_batch_cap(self):
        data = {'medications': [_med('M%d' % i, confirmed_days_ago=900)
                                for i in range(10)]}
        summary = hf.freshness_summary(data, TODAY)
        self.assertEqual(summary['due'], 10)
        self.assertTrue(summary['nudge_due'])


class TestProfileIngest(unittest.TestCase):
    """End-to-end through HealthProfile, where the staleness bug actually bit.

    Re-adding a medication used to fill blank fields only, so a changed dose
    was silently discarded and the profile kept serving the old one.
    """

    def setUp(self):
        import shutil
        import tempfile
        import uuid
        from ai_compare import medical_advisor_health_context as ctx

        self.ctx = ctx
        self.tmp = tempfile.mkdtemp()
        self._orig_dir = ctx.HEALTH_DATA_DIR
        ctx.HEALTH_DATA_DIR = __import__('pathlib').Path(self.tmp)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(setattr, ctx, 'HEALTH_DATA_DIR', self._orig_dir)
        self.profile = ctx.HealthProfile('freshness_test_' + uuid.uuid4().hex[:8])

    def test_changed_dose_from_a_document_is_applied_and_logged(self):
        self.profile.add_medication('Metformin', dose='500mg', frequency='daily')
        self.profile.ingest_source = hi.SOURCE_DOCUMENT
        self.assertTrue(self.profile.add_medication('Metformin', dose='1000mg'))

        med = self.profile.data['medications'][0]
        self.assertEqual(med['dose'], '1000mg')
        self.assertEqual(med['history'][-1]['from'], '500mg')
        self.assertEqual(len(self.profile.data['medications']), 1)

    def test_ai_guess_does_not_overwrite_but_is_proposed(self):
        self.profile.add_medication('Metformin', dose='500mg')
        self.profile.ingest_source = hi.SOURCE_AI
        self.profile.add_medication('Metformin', dose='1000mg')

        self.assertEqual(self.profile.data['medications'][0]['dose'], '500mg')
        self.assertEqual(self.profile.data['pending_changes'][0]['to'], '1000mg')

    def test_new_items_start_active_and_dated(self):
        self.profile.add_supplement('Vitamin D', dose='1000IU')
        sup = self.profile.data['supplements'][0]
        self.assertEqual(sup['status'], hf.STATUS_ACTIVE)
        self.assertTrue(sup['started_on'])

    def test_restarting_a_stopped_medication_reactivates_it(self):
        self.profile.add_medication('Metformin', dose='500mg')
        hf.end_item(self.profile.data['medications'][0], category='medications')
        self.assertTrue(self.profile.add_medication('Metformin', dose='500mg'))

        med = self.profile.data['medications'][0]
        self.assertEqual(med['status'], hf.STATUS_ACTIVE)
        self.assertEqual(med['ended_on'], '')
        self.assertEqual(len(self.profile.data['medications']), 1)

    def test_a_resolved_symptom_reported_again_reopens(self):
        self.profile.add_symptom('headache')
        hf.end_item(self.profile.data['symptoms'][0], category='symptoms')
        self.assertTrue(self.profile.add_symptom('headache'))

        self.assertEqual(self.profile.data['symptoms'][0]['status'], hf.STATUS_ACTIVE)
        self.assertEqual(len(self.profile.data['symptoms']), 1)

    def test_stopped_drugs_are_labelled_not_listed_as_current(self):
        """Safety: retiring rather than deleting must not leave the AI
        believing the patient still takes something they stopped."""
        self.profile.add_medication('Metformin', dose='500mg')
        self.profile.add_medication('Statin', dose='20mg')
        hf.end_item(self.profile.data['medications'][1], category='medications')
        self.profile.save()

        context = self.profile.format_for_prompt(max_chars=100000)
        self.assertIn('currently taking', context)
        current = context.split('STOPPED')[0]
        self.assertIn('Metformin', current)
        self.assertNotIn('Statin', current)
        # Still present, so the AI knows it was tried and stopped.
        self.assertIn('Statin', context)

    def test_stopped_drugs_do_not_generate_take_reminders(self):
        self.profile.add_medication('Metformin', dose='500mg', frequency='daily')
        hf.end_item(self.profile.data['medications'][0], category='medications')
        titles = [r['title'] for r in hi.build_reminders(self.profile.data)]
        self.assertNotIn('Take Metformin', titles)

    def test_default_status_does_not_revive_a_resolved_condition(self):
        self.profile.add_condition('Gout', status='resolved')
        self.profile.data['conditions'][0]['status'] = 'resolved'
        # 'active' is only the caller's default, not an assertion.
        self.profile.add_condition('Gout')
        self.assertEqual(self.profile.data['conditions'][0]['status'], 'resolved')


if __name__ == '__main__':
    unittest.main()
