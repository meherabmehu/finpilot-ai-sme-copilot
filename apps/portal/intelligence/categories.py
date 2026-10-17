"""Explicit category vocabulary, not guesses from descriptions or vendor identities.

Employer contributions, pensions and taxes are not inferred to be payroll. Owners
must classify unclear obligations explicitly or mark them critical. Token boundaries
avoid treating an unrelated category such as 'Salaryman supplies' as protected pay.
"""
import re

PAYROLL = re.compile(r'\b(?:payroll|pay\s+roll|pay\s+run|salary|salaries|wage|wages)\b')
DEBT_SERVICE = re.compile(r'\b(?:loan\s+repayment|debt\s+service|(?:loan|finance)\s+install?ment|debt\s+repayment)\b')


def category_text(value):
    return re.sub(r'[^\w]+', ' ', value.casefold()).strip()


def is_payroll_category(value):
    return bool(PAYROLL.search(category_text(value)))


def is_debt_service_category(value):
    return bool(DEBT_SERVICE.search(category_text(value)))
