"""Reviewed public product discovery; no invented quotation or approval."""
from datetime import date
from decimal import Decimal
from urllib.parse import urlsplit
import re

from pydantic import model_validator
from .schemas import StrictModel


class PublicProduct(StrictModel):
    id: str
    country: str
    currency: str
    lender: str
    name: str
    source_url: str
    verified_at: date
    purpose: str
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    max_months: int | None = None
    eligibility: str
    terms: str
    annual_rate: Decimal | None = None
    fees: Decimal | None = None

    @model_validator(mode='after')
    def verified(self):
        url = urlsplit(self.source_url)
        if url.scheme != 'https' or url.hostname not in ('www.bracbank.com', 'www.sba.gov', 'www.british-business-bank.co.uk') or url.username or url.password or url.port not in (None, 443):
            raise ValueError('Only reviewed official source hosts are allowed.')
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError('Invalid product bounds.')
        if self.annual_rate is not None and not 0 <= self.annual_rate <= 1000:
            raise ValueError('Invalid published rate.')
        return self


CATALOG = [
    dict(id='bd-brac-anonno', country='BD', currency='BDT', lender='BRAC Bank', name='Anonno',
         source_url='https://www.bracbank.com/en/sme/loan/anonno', verified_at='2026-10-19',
         minimum='500000', maximum='5000000', max_months=48, purpose='Working capital or fixed assets',
         eligibility='Lender assessment required; full eligibility and pricing were not available on the reviewed page.',
         terms='Mortgage-free product; seasonal single-installment option mentioned. Request complete rate, fee and guarantee terms.'),
    dict(id='us-sba-7a', country='US', currency='USD', lender='SBA participating lenders', name='7(a) program',
         source_url='https://www.sba.gov/loans/7a-loans/', verified_at='2026-10-19', maximum='5000000',
         purpose='Working capital, equipment and other permitted business uses',
         eligibility='US for-profit small business; creditworthiness and repayment ability assessed by participating lender.',
         terms='Program guarantee is to the lender. Actual rate, fees, collateral and maturity require a lender quotation; no numeric offer is inferred.'),
    dict(id='gb-ggs', country='GB', currency='GBP', lender='British Business Bank accredited lenders', name='Growth Guarantee Scheme',
         source_url='https://www.british-business-bank.co.uk/finance-options/debt-finance/growth-guarantee-scheme',
         verified_at='2026-10-19', maximum='2000000', purpose='Permitted business investment or cash flow',
         eligibility='UK trading business and lender viability assessment. Regional and subsidy restrictions may reduce the limit.',
         terms='Rates and fees are lender-specific. Announced scheme enhancements may differ from operational lender terms; confirm directly. Borrower remains liable for the debt.'),
]


def discover(business, amount=None, months=None, as_of=None, purpose=''):
    as_of = as_of or date.today()
    rows = []
    for raw in CATALOG:
        product = PublicProduct.model_validate(raw)
        if (product.country, product.currency) != (business.country, business.currency):
            continue
        constraints = []
        if amount is not None and ((product.minimum is not None and amount < product.minimum) or (product.maximum is not None and amount > product.maximum)):
            constraints.append('Requested amount falls outside the published bounds.')
        if months is not None and product.max_months is not None and months > product.max_months:
            constraints.append('Requested term exceeds the published maximum.')
        age = (as_of-product.verified_at).days
        rows.append({'product': product.model_dump(mode='json'), 'constraints': constraints,
                     'purpose_assessment': 'Broad business purpose appears relevant; lender must confirm the specific use.' if re.search(r'working capital|cash flow|inventory|payroll|supplier|equipment|asset|investment', purpose, re.I) else
                                           'Specific purpose not established from public catalog; obtain lender confirmation.' if purpose else 'Enter the purpose or confirm it with the lender.',
                     'freshness': 'Reviewed public source; not a live lender feed' if 0 <= age <= 90 else 'Needs source re-verification',
                     'quotation_required': product.annual_rate is None or product.fees is None,
                     'suitability': 'Country/currency discovery only; eligibility and affordability unverified.'})
    return rows
