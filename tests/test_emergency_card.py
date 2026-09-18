"""Emergency card derivation: age from DOB, blood thinners from current meds."""
from ai_compare.medical_advisor_health_context import (
    age_from_date_of_birth,
    anticoagulant_labels,
)


def test_age_from_date_of_birth_rejects_junk():
    assert age_from_date_of_birth('') == ''
    assert age_from_date_of_birth(None) == ''
    assert age_from_date_of_birth('not-a-date') == ''
    assert age_from_date_of_birth('9999-01-01') == ''


def test_age_from_date_of_birth_is_whole_years():
    # A date of birth of 1 March 2000 is 24 on 29 Feb 2025 and 25 on 1 Mar 2025.
    assert age_from_date_of_birth('2000-03-01') != ''
    assert age_from_date_of_birth('2000-03-01').isdigit()


def test_age_from_free_typed_dates():
    assert age_from_date_of_birth('15/3/1954') == age_from_date_of_birth('1954-03-15')
    assert age_from_date_of_birth('15 Mar 1954') == age_from_date_of_birth('1954-03-15')


def test_anticoagulant_labels_current_only():
    labels = anticoagulant_labels([
        {'name': 'Warfarin', 'dose': '5mg', 'status': 'stopped'},
        {'name': 'Eliquis', 'dose': '2.5mg', 'status': 'active'},
        {'name': 'metformin', 'dose': '500mg', 'status': 'active'},
    ])
    assert labels == ['Eliquis 2.5mg']


def test_aspirin_is_flagged_as_antiplatelet():
    labels = anticoagulant_labels([
        {'name': 'Cartia', 'dose': '100mg'},
    ])
    assert labels == ['Cartia 100mg']
