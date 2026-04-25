import math
from .models import FinancingType


CLOSING_COST_RATE_FINANCED = 0.030   # ~3% buyer closing costs with a loan
CLOSING_COST_RATE_CASH = 0.015       # ~1.5% cash purchase (no lender fees)


def monthly_payment(principal: float, annual_rate: float, term_years: int) -> float:
    if annual_rate == 0 or principal == 0:
        return 0.0
    r = annual_rate / 12
    n = term_years * 12
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def loan_amount(purchase_price: float, down_payment: float) -> float:
    return max(0.0, purchase_price - down_payment)


def closing_costs(purchase_price: float, financing_type: FinancingType) -> float:
    rate = CLOSING_COST_RATE_CASH if financing_type == FinancingType.CASH else CLOSING_COST_RATE_FINANCED
    return purchase_price * rate


def total_cash_to_close(purchase_price: float, down_payment: float, financing_type: FinancingType) -> float:
    return down_payment + closing_costs(purchase_price, financing_type)


def amortization_by_year(principal: float, annual_rate: float, term_years: int, years: int) -> list[dict]:
    """Returns year-by-year amortization summary up to `years`."""
    if annual_rate == 0 or principal == 0:
        return [{"year": y, "interest_paid": 0, "principal_paid": 0, "remaining_balance": 0} for y in range(1, years + 1)]

    r = annual_rate / 12
    pmt = monthly_payment(principal, annual_rate, term_years)
    balance = principal
    schedule = []

    for year in range(1, min(years, term_years) + 1):
        year_interest = 0.0
        year_principal = 0.0
        for _ in range(12):
            interest = balance * r
            paid = pmt - interest
            year_interest += interest
            year_principal += paid
            balance = max(0.0, balance - paid)
        schedule.append({
            "year": year,
            "interest_paid": year_interest,
            "principal_paid": year_principal,
            "remaining_balance": balance,
        })

    return schedule
