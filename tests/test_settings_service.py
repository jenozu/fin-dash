from datetime import date, timedelta

from services import settings_service


def test_get_setting_default_when_missing():
    assert settings_service.get_setting("missing", "fallback") == "fallback"


def test_set_and_get_setting():
    settings_service.set_setting("pay_frequency", "Weekly")
    assert settings_service.get_setting("pay_frequency") == "Weekly"


def test_set_setting_overwrites_existing():
    settings_service.set_setting("pay_frequency", "Weekly")
    settings_service.set_setting("pay_frequency", "Monthly")
    assert settings_service.get_setting("pay_frequency") == "Monthly"


def test_get_pay_frequency_default():
    assert settings_service.get_pay_frequency() == "Bi-Weekly"


def test_get_average_paycheck_default_and_empty_string():
    assert settings_service.get_average_paycheck() == 0.0
    settings_service.set_setting("average_paycheck", "")
    assert settings_service.get_average_paycheck() == 0.0


def test_get_average_paycheck_parses_float():
    settings_service.set_setting("average_paycheck", "1234.56")
    assert settings_service.get_average_paycheck() == 1234.56


def test_get_next_paycheck_date_default():
    expected = date.today() + timedelta(days=14)
    assert settings_service.get_next_paycheck_date() == expected


def test_get_next_paycheck_date_parses_iso():
    target = date.today() + timedelta(days=5)
    settings_service.set_setting("next_paycheck_date", target.isoformat())
    assert settings_service.get_next_paycheck_date() == target
