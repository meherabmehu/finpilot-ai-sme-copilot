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
    pricing_basis: str = 'Lender quotation required; no numeric rate or fee verified.'
    excluded_uses: list[str] = []

    @model_validator(mode='after')
    def verified(self):
        url = urlsplit(self.source_url)
        if url.scheme != 'https' or url.hostname not in ('www.bracbank.com', 'www.sba.gov', 'www.british-business-bank.co.uk') or url.username or url.password or url.port not in (None, 443) or url.query or url.fragment:
            raise ValueError('Only reviewed official source hosts are allowed.')
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError('Invalid product bounds.')
        if self.annual_rate is not None and not 0 <= self.annual_rate <= 1000:
            raise ValueError('Invalid published rate.')
        if any(v is not None and (not v.is_finite() or v < 0) for v in (self.minimum, self.maximum, self.fees)) or (self.max_months is not None and self.max_months <= 0):
            raise ValueError('Product amounts, fees and terms must be finite and nonnegative.')
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
    dict(id='us-sba-microloan', country='US', currency='USD', lender='SBA-approved intermediary lenders', name='Microloan program',
         source_url='https://www.sba.gov/loans/microloans/', verified_at='2026-10-19', maximum='50000', max_months=84,
         purpose='Working capital, inventory, supplies, furniture, fixtures, machinery or equipment',
         excluded_uses=['existing debt', 'refinancing', 'real estate'],
         eligibility='US small operating business; intermediary makes credit decisions and sets terms. Confirm current eligibility with the intermediary.',
         pricing_basis='Official page publishes a general 8%–13% range, varying by intermediary. This is not an individual annual-rate quotation; fees are unverified.',
         terms='Maximum seven-year repayment term. No existing-debt repayment or real-estate purchase. Obtain an actual rate, fees, collateral and guarantee quotation.'),
    dict(id='us-sba-504', country='US', currency='USD', lender='SBA Certified Development Companies and senior lenders', name='504 fixed-asset program',
         source_url='https://www.sba.gov/loans/504-loans/', verified_at='2026-10-19', maximum='5500000', max_months=300,
         purpose='Eligible major fixed assets, buildings, land or long-life machinery and equipment',
         excluded_uses=['working capital', 'inventory', 'payroll'],
         eligibility='US for-profit small operating business; CDC and lender assessment, permitted fixed-asset project and repayment ability required.',
         pricing_basis='Market-linked fixed-rate structure; no current numeric quotation verified. Header says up to $5m while detailed maximum says $5.5m; CDC must confirm project-specific limits and costs.',
         terms='Published maturities are 10, 20 or 25 years. Working capital and inventory are excluded. Published cost language is not a personal rate or fee quotation.'),
]


def discover(business, amount=None, months=None, as_of=None, purpose=''):
    as_of = as_of or date.today()
    rows = []
    for raw in CATALOG:
        product = PublicProduct.model_validate(raw)
        if (product.country, product.currency) != (business.country, business.currency):
            continue
        constraints = []
        for excluded in product.excluded_uses:
            if excluded in purpose.casefold():
                constraints.append('Published purpose restriction: '+excluded+' is excluded; do not treat this program as a matching offer.')
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
