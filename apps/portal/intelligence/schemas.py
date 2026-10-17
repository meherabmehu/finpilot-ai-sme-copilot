from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class CashEvent(StrictModel):
    id: str
    source: Literal['transaction', 'recurring']
    source_id: int
    date: str
    amount: Decimal = Field(gt=0, le=Decimal('9999999999999999.99'))
    direction: Literal['inflow', 'outflow']
    category: str
    description: str
    payroll: bool = False
    critical: bool = False
    basis: str = 'assumed'


class PlanAction(StrictModel):
    kind: Literal['shift', 'split', 'reduce', 'finance', 'collect']
    event_id: str = ''
    days: int = Field(default=0, ge=-90, le=90)
    amount: Decimal = Field(default=Decimal('0'), ge=0, le=Decimal('1000000000'), decimal_places=2)
    date: str = ''
    annual_rate: Decimal = Field(default=Decimal('0'), ge=0, le=1000)
    months: int = Field(default=12, ge=1, le=120)
    fee: Decimal = Field(default=Decimal('0'), ge=0, le=Decimal('1000000000'), decimal_places=2)


class PlanSpec(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    actions: list[PlanAction] = Field(default_factory=list, max_length=8)


class PolicySpec(StrictModel):
    horizon_days: int = Field(default=30, ge=7, le=90)
    protect_payroll: bool = True
    protect_critical_suppliers: bool = True
    max_delay_days: int = Field(default=7, ge=0, le=90)
    max_borrowing: Decimal = Field(default=Decimal('0'), ge=0, le=Decimal('1000000000'))
    max_annual_rate: Decimal = Field(default=Decimal('20'), ge=0, le=1000)
    expense_increase_percent: int = Field(default=25, ge=1, le=1000)
    concentration_percent: int = Field(default=60, ge=1, le=100)
    risk_tolerance: Literal['cautious', 'balanced'] = 'cautious'
    restricted_categories: list[str] = Field(default_factory=list, max_length=30)
    goal: str = Field(default='', max_length=240)
    issue_cooldown_hours: int = Field(default=24, ge=1, le=168)

    @field_validator('restricted_categories')
    @classmethod
    def valid_categories(cls, values):
        if any(not value.strip() or len(value) > 80 for value in values):
            raise ValueError('Use category names of 1–80 characters.')
        return list(dict.fromkeys(value.strip() for value in values))
