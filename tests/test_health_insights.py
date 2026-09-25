"""Unit tests for the deterministic health insight, reminder and provenance layers.

These must never touch the network: Tier 1 is pure Python, and the Tier 2 tests
inject a fake chat function.
"""
import json
import unittest
from datetime import date, timedelta

from ai_compare import health_insights as hi


class TestProvenance(unittest.TestCase):
    def test_legacy_sources_are_mapped(self):
        self.assertEqual(hi.normalize_source('ai'), hi.SOURCE_AI)
        self.assertEqual(hi.normalize_source('upload'), hi.SOURCE_DOCUMENT)
        self.assertEqual(hi.normalize_source('user'), hi.SOURCE_USER)
        self.assertEqual(hi.normalize_source('doctor'), hi.SOURCE_CLINICIAN)

    def test_unknown_source_falls_back_to_default(self):
        self.assertEqual(hi.normalize_source('wat', hi.SOURCE_AI), hi.SOURCE_AI)

    def test_defaults_are_stamped_and_idempotent(self):
        data = {'conditions': [{'name': 'Gout'}]}
        hi.apply_provenance_defaults(data, hi.SOURCE_AI)
        item = data['conditions'][0]
        self.assertEqual(item['source'], hi.SOURCE_AI)
        self.assertFalse(item['verified_by_user'])

        # A second pass must not relabel history.
        self.assertEqual(hi.apply_provenance_defaults(data, hi.SOURCE_USER), 0)
        self.assertEqual(data['conditions'][0]['source'], hi.SOURCE_AI)

    def test_user_entered_is_self_verifying(self):
        data = {'conditions': [{'name': 'Gout'}]}
        hi.apply_provenance_defaults(data, hi.SOURCE_USER)
        self.assertTrue(data['conditions'][0]['verified_by_user'])

    def test_counts_track_unverified_ai(self):
        data = {'conditions': [
            {'name': 'A', 'source': hi.SOURCE_AI, 'verified_by_user': False},
            {'name': 'B', 'source': hi.SOURCE_AI, 'verified_by_user': True},
            {'name': 'C', 'source': hi.SOURCE_USER, 'verified_by_user': True},
        ]}
        counts = hi.provenance_counts(data)
        self.assertEqual(counts['unverified_ai'], 1)
        self.assertEqual(counts[hi.SOURCE_AI], 2)


class TestParsing(unittest.TestCase):
    def test_date_formats(self):
        self.assertEqual(hi.parse_date('2026-05-12'), date(2026, 5, 12))
        self.assertEqual(hi.parse_date('12/05/2026'), date(2026, 5, 12))
        self.assertEqual(hi.parse_date('12 May 2026'), date(2026, 5, 12))
        self.assertEqual(hi.parse_date('May 12, 2026'), date(2026, 5, 12))
        self.assertEqual(hi.parse_date('2026-05-12T08:00:00'), date(2026, 5, 12))
        self.assertIsNone(hi.parse_date('sometime'))
        self.assertIsNone(hi.parse_date(''))

    def test_numeric_extraction(self):
        self.assertEqual(hi.extract_numeric('6.4 H mmol/L'), 6.4)
        self.assertEqual(hi.extract_numeric('368 pmol/L'), 368.0)
        self.assertEqual(hi.extract_numeric(4.3), 4.3)
        self.assertIsNone(hi.extract_numeric('not detected'))

    def test_reference_ranges(self):
        self.assertEqual(hi.parse_reference_range('3.5 - 5.5'), (3.5, 5.5))
        self.assertEqual(hi.parse_reference_range('3.5\u20135.5 mmol/L'), (3.5, 5.5))
        self.assertEqual(hi.parse_reference_range('< 5.2'), (None, 5.2))
        self.assertEqual(hi.parse_reference_range('> 1.0'), (1.0, None))
        self.assertEqual(hi.parse_reference_range(''), (None, None))

    def test_range_position(self):
        self.assertEqual(hi.range_position('6.4', '3.5 - 5.5'), 'high')
        self.assertEqual(hi.range_position('2.0', '3.5 - 5.5'), 'low')
        self.assertEqual(hi.range_position('4.0', '3.5 - 5.5'), 'normal')
        self.assertIsNone(hi.range_position('4.0', ''))

    def test_explicit_lab_flag_wins_without_a_range(self):
        self.assertEqual(hi.range_position('6.4 H mmol/L', ''), 'high')
        self.assertEqual(hi.range_position('1.1 L mmol/L', ''), 'low')


class TestReminders(unittest.TestCase):
    today = date(2026, 6, 1)

    def test_overdue_and_upcoming_follow_ups(self):
        data = {'follow_ups': [
            {'title': 'See cardiologist', 'due_date': '2026-05-01'},
            {'title': 'Book blood test', 'due_date': '2026-06-01'},
            {'title': 'Annual review', 'due_date': '2026-06-20'},
        ]}
        reminders = hi.build_reminders(data, self.today)
        by_title = {r['title']: r for r in reminders}
        self.assertEqual(by_title['See cardiologist']['status'], 'overdue')
        self.assertEqual(by_title['Book blood test']['status'], 'due_today')
        self.assertEqual(by_title['Annual review']['status'], 'upcoming')
        self.assertEqual(by_title['Annual review']['days_until'], 19)

    def test_overdue_sorts_first(self):
        data = {'follow_ups': [
            {'title': 'Later', 'due_date': '2026-06-20'},
            {'title': 'Missed', 'due_date': '2026-04-01'},
        ]}
        self.assertEqual(hi.build_reminders(data, self.today)[0]['title'], 'Missed')

    def test_completed_follow_ups_are_skipped(self):
        data = {'follow_ups': [
            {'title': 'Done thing', 'due_date': '2026-05-01', 'status': 'completed'},
        ]}
        self.assertEqual(hi.build_reminders(data, self.today), [])

    def test_beyond_horizon_is_skipped(self):
        data = {'follow_ups': [{'title': 'Far off', 'due_date': '2027-06-01'}]}
        self.assertEqual(hi.build_reminders(data, self.today), [])

    def test_retest_phrase_becomes_a_dated_reminder(self):
        data = {'test_results': [{
            'test_name': 'HbA1c', 'value': '7.1', 'date': '2026-05-01',
            'notes': 'Please recheck in 2 months',
        }]}
        reminders = hi.build_reminders(data, self.today)
        retest = [r for r in reminders if r['kind'] == 'retest']
        self.assertEqual(len(retest), 1)
        self.assertEqual(retest[0]['due_date'], '2026-06-30')
        self.assertEqual(retest[0]['title'], 'Recheck HbA1c')

    def test_medication_with_frequency_is_recurring(self):
        data = {'medications': [{'name': 'Rosuvastatin', 'dose': '10mg', 'frequency': 'daily'}]}
        reminders = hi.build_reminders(data, self.today)
        self.assertEqual(len(reminders), 1)
        self.assertEqual(reminders[0]['status'], 'recurring')
        self.assertEqual(reminders[0]['title'], 'Take Rosuvastatin')

    def test_medication_without_frequency_is_not_a_reminder(self):
        data = {'medications': [{'name': 'Rosuvastatin', 'dose': '10mg'}]}
        self.assertEqual(hi.build_reminders(data, self.today), [])

    def test_diary_nudge_after_a_quiet_stretch(self):
        quiet = {'diary': [{'title': 'x', 'date': '2026-05-20'}]}
        self.assertTrue(any(r['kind'] == 'diary' for r in hi.build_reminders(quiet, self.today)))
        recent = {'diary': [{'title': 'x', 'date': '2026-05-31'}]}
        self.assertFalse(any(r['kind'] == 'diary' for r in hi.build_reminders(recent, self.today)))

    def test_ics_export_only_includes_dated_reminders(self):
        data = {
            'follow_ups': [{'title': 'See cardiologist', 'due_date': '2026-06-10'}],
            'medications': [{'name': 'Rosuvastatin', 'frequency': 'daily'}],
        }
        ics = hi.reminders_to_ics(hi.build_reminders(data, self.today))
        self.assertIn('BEGIN:VCALENDAR', ics)
        self.assertIn('DTSTART;VALUE=DATE:20260610', ics)
        self.assertEqual(ics.count('BEGIN:VEVENT'), 1)
        self.assertIn('SUMMARY:See cardiologist', ics)


class TestObservations(unittest.TestCase):
    today = date(2026, 6, 1)

    def test_out_of_range_latest_value(self):
        data = {'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'reference_range': '0 - 3.0', 'date': '2026-05-01'},
        ]}
        obs = hi.build_observations(data, self.today)
        titles = [o['title'] for o in obs]
        self.assertIn('LDL is high', titles)

    def test_extreme_value_is_urgent(self):
        data = {'test_results': [
            {'test_name': 'Potassium', 'value': '12', 'reference_range': '3.5 - 5.0', 'date': '2026-05-01'},
        ]}
        obs = hi.build_observations(data, self.today)
        flags = hi.red_flags(obs)
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]['severity'], hi.SEVERITY_URGENT)

    def test_trend_needs_three_points(self):
        two = {'test_results': [
            {'test_name': 'LDL', 'value': '3.1', 'date': '2026-01-01'},
            {'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01'},
        ]}
        self.assertFalse(any(o['id'].startswith('') and 'has risen' in o['title']
                             for o in hi.build_observations(two, self.today)))

        three = {'test_results': [
            {'test_name': 'LDL', 'value': '3.1', 'date': '2026-01-01'},
            {'test_name': 'LDL', 'value': '3.8', 'date': '2026-03-01'},
            {'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01'},
        ]}
        trends = [o for o in hi.build_observations(three, self.today) if 'has risen' in o['title']]
        self.assertEqual(len(trends), 1)
        self.assertEqual(len(trends[0]['evidence']), 3)

    def test_flat_trend_is_not_reported(self):
        data = {'test_results': [
            {'test_name': 'LDL', 'value': '3.1', 'date': '2026-01-01'},
            {'test_name': 'LDL', 'value': '3.12', 'date': '2026-03-01'},
            {'test_name': 'LDL', 'value': '3.15', 'date': '2026-05-01'},
        ]}
        self.assertFalse(any('has risen' in o['title'] or 'has fallen' in o['title']
                             for o in hi.build_observations(data, self.today)))

    def test_stale_results_flagged(self):
        data = {'test_results': [{'test_name': 'LDL', 'value': '3.1', 'date': '2024-01-01'}]}
        titles = [o['title'] for o in hi.build_observations(data, self.today)]
        self.assertIn('Your test results are over a year old', titles)

    def test_polypharmacy(self):
        data = {
            'medications': [{'name': f'Drug {i}'} for i in range(3)],
            'supplements': [{'name': f'Vit {i}'} for i in range(2)],
        }
        titles = [o['title'] for o in hi.build_observations(data, self.today)]
        self.assertIn('You are taking 5 medications and supplements', titles)

    def test_unverified_ai_items_surface(self):
        data = {'conditions': [
            {'name': f'C{i}', 'source': hi.SOURCE_AI, 'verified_by_user': False}
            for i in range(4)
        ]}
        self.assertTrue(any('came from AI and are unconfirmed' in o['title']
                            for o in hi.build_observations(data, self.today)))

    def test_low_mood_pattern(self):
        data = {'diary': [
            {'title': 'a', 'date': '2026-05-28', 'mood': 'sad'},
            {'title': 'b', 'date': '2026-05-29', 'mood': 'anxious'},
            {'title': 'c', 'date': '2026-05-30', 'mood': 'calm'},
        ]}
        self.assertTrue(any('low mood' in o['title']
                            for o in hi.build_observations(data, self.today)))

    def test_empty_profile_yields_nothing(self):
        self.assertEqual(hi.build_observations({}, self.today), [])


class TestAdviceGating(unittest.TestCase):
    def _profile(self):
        return {
            'conditions': [{'name': 'High cholesterol', 'status': 'active',
                            'source': hi.SOURCE_USER, 'verified_by_user': True}],
            'test_results': [{'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01',
                              'source': hi.SOURCE_DOCUMENT, 'verified_by_user': True}],
        }

    def _fake_chat(self, payload, calls):
        def chat(messages, max_tokens=None, temperature=None, model=None):
            calls.append(messages)
            return json.dumps(payload)
        return chat

    def test_signature_ignores_cosmetic_changes(self):
        data = self._profile()
        before = hi.advice_signature(data)
        data['name'] = 'Renamed'
        data['diary'] = [{'title': 'new entry'}]
        self.assertEqual(before, hi.advice_signature(data))

    def test_signature_changes_with_a_new_test(self):
        data = self._profile()
        before = hi.advice_signature(data)
        data['test_results'].append({'test_name': 'HbA1c', 'value': '7.1', 'date': '2026-05-02'})
        self.assertNotEqual(before, hi.advice_signature(data))

    def test_second_call_is_served_from_cache(self):
        data = self._profile()
        calls = []
        chat = self._fake_chat({'suggestions': [
            {'title': 'Discuss LDL', 'detail': 'Your LDL is above range.', 'cites': ['LDL']}
        ]}, calls)
        first = hi.generate_advice(data, today=date(2026, 6, 1), chat=chat)
        self.assertEqual(len(first['suggestions']), 1)
        second = hi.generate_advice(data, today=date(2026, 6, 1), chat=chat)
        self.assertTrue(second['cached'])
        self.assertEqual(len(calls), 1)

    def test_opt_out_blocks_generation(self):
        data = self._profile()
        data['advice_settings'] = {'ai_enabled': False}
        calls = []
        result = hi.generate_advice(data, chat=self._fake_chat({}, calls))
        self.assertEqual(calls, [])
        self.assertIn('turned off', result['reason'])

    def test_daily_cap_blocks_generation(self):
        data = self._profile()
        today = date(2026, 6, 1)
        data['ai_advice_usage'] = {'date': today.isoformat(), 'count': hi.daily_cap()}
        calls = []
        result = hi.generate_advice(data, force=True, today=today,
                                    chat=self._fake_chat({}, calls))
        self.assertEqual(calls, [])
        self.assertIn('limit', result['reason'].lower())

    def test_hallucinated_citation_is_dropped(self):
        data = self._profile()
        calls = []
        chat = self._fake_chat({'suggestions': [
            {'title': 'Real', 'detail': 'About your LDL.', 'cites': ['LDL']},
            {'title': 'Invented', 'detail': 'Your ferritin is low.', 'cites': ['Ferritin']},
        ]}, calls)
        result = hi.generate_advice(data, today=date(2026, 6, 1), chat=chat)
        titles = [s['title'] for s in result['suggestions']]
        self.assertIn('Real', titles)
        self.assertNotIn('Invented', titles)

    def test_unverified_facts_are_not_citable(self):
        data = self._profile()
        data['test_results'].append({
            'test_name': 'Ferritin', 'value': '20', 'date': '2026-05-01',
            'source': hi.SOURCE_AI, 'verified_by_user': False,
        })
        calls = []
        chat = self._fake_chat({'suggestions': [
            {'title': 'Guessy', 'detail': 'Your ferritin is low.', 'cites': ['Ferritin']},
        ]}, calls)
        result = hi.generate_advice(data, today=date(2026, 6, 1), chat=chat)
        self.assertEqual(result['suggestions'], [])

    def test_unverified_items_are_separated_in_the_prompt(self):
        data = self._profile()
        data['conditions'].append({'name': 'Suspected apnoea', 'status': 'investigating',
                                   'source': hi.SOURCE_AI, 'verified_by_user': False})
        verified, unverified, citable = hi._facts_for_prompt(data)
        self.assertIn('High cholesterol', verified)
        self.assertIn('Suspected apnoea', unverified)
        self.assertNotIn('Suspected apnoea', verified)
        self.assertNotIn(hi.normalize_test_key('Suspected apnoea'), citable)

    def test_stopped_items_are_labelled_not_current(self):
        data = self._profile()
        data['medications'] = [
            {'name': 'metformin', 'dose': '500mg', 'status': 'active',
             'source': hi.SOURCE_USER, 'verified_by_user': True},
            {'name': 'old drug', 'dose': '10mg', 'status': 'stopped',
             'source': hi.SOURCE_USER, 'verified_by_user': True},
        ]
        data['supplements'] = [
            {'name': 'vitamin D', 'status': 'stopped',
             'source': hi.SOURCE_USER, 'verified_by_user': True},
        ]
        data['conditions'].append({'name': 'gout', 'status': 'resolved',
                                   'source': hi.SOURCE_USER, 'verified_by_user': True})
        verified, unverified, citable = hi._facts_for_prompt(data)
        self.assertIn('Medication: metformin 500mg', verified)
        self.assertIn('Medication (STOPPED — do not treat as current): old drug 10mg', verified)
        self.assertIn('Supplement (STOPPED — do not treat as current): vitamin D', verified)
        self.assertIn('Condition (RESOLVED — do not treat as current): gout', verified)
        self.assertNotIn('Medication: old drug', verified)
        self.assertIn(hi.normalize_test_key('old drug'), citable)

    def test_model_failure_degrades_gracefully(self):
        def boom(messages, max_tokens=None, temperature=None, model=None):
            raise RuntimeError('no api key')
        result = hi.generate_advice(self._profile(), chat=boom)
        self.assertEqual(result['suggestions'], [])
        self.assertIn('Could not generate', result['reason'])

    def test_empty_profile_does_not_call_the_model(self):
        calls = []
        result = hi.generate_advice({}, chat=self._fake_chat({}, calls))
        self.assertEqual(calls, [])
        self.assertIn('Add some health information', result['reason'])


class TestDigestAndOverview(unittest.TestCase):
    today = date(2026, 6, 1)

    def test_digest_counts_recent_additions(self):
        data = {'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'added_at': '2026-05-30'},
            {'test_name': 'HbA1c', 'value': '7.1', 'added_at': '2026-01-01'},
        ]}
        digest = hi.build_digest(data, self.today)
        self.assertEqual(digest['added'].get('test_results'), 1)
        self.assertEqual(digest['period'], 'weekly')

    def test_digest_due_when_never_generated(self):
        self.assertTrue(hi.digest_due({}, self.today))

    def test_digest_not_due_immediately_after(self):
        data = {'digest': {'generated_at': '2026-05-30'}}
        self.assertFalse(hi.digest_due(data, self.today))

    def test_digest_off_is_never_due(self):
        data = {'advice_settings': {'digest_frequency': 'off'}}
        self.assertFalse(hi.digest_due(data, self.today))

    def test_overview_never_generates_advice(self):
        data = {'test_results': [
            {'test_name': 'LDL', 'value': '4.3', 'reference_range': '0 - 3.0',
             'date': '2026-05-01', 'source': hi.SOURCE_USER, 'verified_by_user': True},
        ]}
        overview = hi.build_overview(data, self.today)
        self.assertEqual(overview['advice']['suggestions'], [])
        self.assertIn('reminder_counts', overview)
        self.assertTrue(overview['observations'])
        self.assertNotIn('ai_advice', data)

    def test_overview_respects_reminders_opt_out(self):
        data = {
            'advice_settings': {'reminders_enabled': False},
            'follow_ups': [{'title': 'See doctor', 'due_date': '2026-06-02'}],
        }
        self.assertEqual(hi.build_overview(data, self.today)['reminders'], [])


class TestPromptLanguageAndExplain(unittest.TestCase):
    def _profile(self):
        return {
            'conditions': [{'name': 'High cholesterol', 'status': 'active',
                            'source': hi.SOURCE_USER, 'verified_by_user': True}],
            'medications': [{'name': 'Atorvastatin', 'dose': '20mg', 'status': 'active',
                             'source': hi.SOURCE_USER, 'verified_by_user': True}],
            'test_results': [
                {'test_name': 'LDL', 'value': '4.3', 'date': '2026-05-01',
                 'source': hi.SOURCE_DOCUMENT, 'verified_by_user': True},
                {'test_name': 'Ferritin', 'value': '20', 'date': '2026-05-01',
                 'source': hi.SOURCE_AI, 'verified_by_user': False},
            ],
        }

    def _fake_chat(self, payload, calls):
        def chat(messages, max_tokens=None, temperature=None, model=None):
            calls.append(messages)
            return json.dumps(payload)
        return chat

    def test_language_follows_locale_and_spoken_field(self):
        self.assertIn('same language', hi.prompt_language_note({}))
        self.assertIn('English', hi.prompt_language_note({
            'advice_settings': {'locale': 'en'}}))
        self.assertIn('Traditional Chinese', hi.prompt_language_note({
            'advice_settings': {'locale': 'zh-HK'}}))
        self.assertIn('Traditional Chinese', hi.prompt_language_note({
            'personal': {'language': 'Cantonese'}}))

    def test_explain_cites_only_that_test_and_keeps_cached_advice(self):
        data = self._profile()
        data['ai_advice'] = {'suggestions': [{'title': 'keep me'}]}
        calls = []
        chat = self._fake_chat({'suggestions': [
            {'title': 'LDL note', 'detail': 'Your LDL is 4.3.', 'cites': ['LDL']},
            {'title': 'Guess', 'detail': 'Ferritin is low.', 'cites': ['Ferritin']},
        ]}, calls)
        result = hi.explain_test_result(data, 0, chat=chat, today=date(2026, 6, 1))
        titles = [s['title'] for s in result['suggestions']]
        self.assertIn('LDL note', titles)
        self.assertNotIn('Guess', titles)
        self.assertEqual(data['ai_advice']['suggestions'][0]['title'], 'keep me')
        self.assertIn('same language', calls[0][1]['content'])

    def test_explain_respects_opt_out_and_does_not_cite_unverified_row(self):
        data = self._profile()
        data['advice_settings'] = {'ai_enabled': False}
        calls = []
        result = hi.explain_test_result(data, 0, chat=self._fake_chat({}, calls),
                                        today=date(2026, 6, 1))
        self.assertEqual(calls, [])
        self.assertIn('turned off', result['reason'])

        data['advice_settings'] = {'ai_enabled': True}
        chat = self._fake_chat({'suggestions': [
            {'title': 'Ferritin note', 'detail': 'Low.', 'cites': ['Ferritin']},
        ]}, calls)
        result = hi.explain_test_result(data, 1, chat=chat, today=date(2026, 6, 1))
        self.assertEqual(result['suggestions'], [])

    def test_advice_prompt_uses_personal_language(self):
        data = self._profile()
        data['personal'] = {'language': 'Cantonese'}
        calls = []
        hi.generate_advice(data, today=date(2026, 6, 1),
                           chat=self._fake_chat({'suggestions': []}, calls))
        self.assertIn('Traditional Chinese', calls[0][1]['content'])


if __name__ == '__main__':
    unittest.main()
