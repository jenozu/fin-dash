from datetime import date, timedelta
from database.database import get_session
from database.models import Setting


def get_setting(name, default=""):
    session = get_session()
    try:
        s = session.query(Setting).filter_by(setting_name=name).first()
        return s.setting_value if s else default
    finally:
        session.close()


def set_setting(name, value):
    session = get_session()
    try:
        s = session.query(Setting).filter_by(setting_name=name).first()
        if s:
            s.setting_value = str(value)
        else:
            session.add(Setting(setting_name=name, setting_value=str(value)))
        session.commit()
    finally:
        session.close()


def get_pay_frequency():
    return get_setting("pay_frequency", "Bi-Weekly")


def get_average_paycheck():
    val = get_setting("average_paycheck", "0")
    return float(val) if val else 0.0


def get_next_paycheck_date():
    val = get_setting("next_paycheck_date", "")
    if val:
        return date.fromisoformat(val)
    return date.today() + timedelta(days=14)
