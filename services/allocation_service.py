from services.account_service import get_spending_balance
from services.settings_service import get_pay_frequency, get_average_paycheck
from services.bill_service import get_bills_committed, get_monthly_bills_total
from services.goal_service import get_goals_committed
from services.wishlist_service import get_wishlist_committed
from config.constants import PAY_PERIODS_PER_YEAR


def get_current_balance():
    return get_spending_balance()


def calculate_true_available_cash():
    balance = get_current_balance()
    pay_freq = get_pay_frequency()
    bills = get_bills_committed()
    goals = get_goals_committed(pay_freq)
    wishlist = get_wishlist_committed(pay_freq)
    return {
        "balance": balance,
        "bills_committed": bills,
        "goals_committed": goals,
        "wishlist_committed": wishlist,
        "true_available": balance - bills - goals - wishlist,
    }


def calculate_paycheck_allocation():
    pay_freq = get_pay_frequency()
    paycheck = get_average_paycheck()
    periods = PAY_PERIODS_PER_YEAR.get(pay_freq, 26)
    bills_per_check = get_monthly_bills_total() * 12.0 / periods
    goals_per_check = get_goals_committed(pay_freq)
    wishlist_per_check = get_wishlist_committed(pay_freq)
    return {
        "paycheck": paycheck,
        "bills": round(bills_per_check, 2),
        "goals": round(goals_per_check, 2),
        "wishlist": round(wishlist_per_check, 2),
        "available": round(paycheck - bills_per_check - goals_per_check - wishlist_per_check, 2),
    }
