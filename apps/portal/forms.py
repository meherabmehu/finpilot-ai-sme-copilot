import uuid
from decimal import Decimal
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone
from .models import Business, Transaction, RecurringObligation

COUNTRIES = [
    ("BD", "Bangladesh"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("IN", "India"),
    ("SG", "Singapore"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("AE", "United Arab Emirates"),
    ("DE", "Germany"),
    ("BR", "Brazil"),
    ("OTHER", "Other (enter ISO code below)"),
]
CURRENCIES = [
    ("BDT", "BDT · Bangladeshi taka"),
    ("USD", "USD · US dollar"),
    ("GBP", "GBP · British pound"),
    ("EUR", "EUR · Euro"),
    ("INR", "INR · Indian rupee"),
    ("SGD", "SGD · Singapore dollar"),
    ("CAD", "CAD · Canadian dollar"),
    ("AUD", "AUD · Australian dollar"),
    ("AED", "AED · UAE dirham"),
    ("BRL", "BRL · Brazilian real"),
]


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True, "placeholder": "you@example.com"}),
    )
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "The email address or password is incorrect. Use an account registered on this site.",
    }

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()


class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(max_length=150)
    terms = forms.BooleanField(label="I agree to the Terms and Privacy Policy")

    class Meta:
        model = User
        fields = ["full_name", "email", "password1", "password2", "terms"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"]
        user.is_active = False
        if commit:
            user.save()
        return user


class BusinessForm(forms.ModelForm):
    low_cash_threshold = forms.DecimalField(min_value=0, max_digits=18, decimal_places=2, initial=0)
    country = forms.ChoiceField(choices=COUNTRIES[:-1])
    currency = forms.ChoiceField(choices=CURRENCIES)
    category = forms.ChoiceField(
        choices=[(x, x) for x in ["Retail", "E-commerce", "Restaurant", "Manufacturing", "Services", "Wholesale", "Other"]]
    )

    class Meta:
        model = Business
        fields = [
            "name",
            "category",
            "country",
            "currency",
            "size",
            "description",
            "address",
            "registration_number",
            "opening_balance",
            "opening_date",
            "low_cash_threshold",
            "cash_records_complete",
        ]
        widgets = {"opening_date": forms.DateInput(attrs={"type": "date"}), "description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["opening_date"].initial = timezone.localdate()

    def clean_opening_date(self):
        value = self.cleaned_data["opening_date"]
        if value > timezone.localdate():
            raise forms.ValidationError("Opening date cannot be in the future.")
        if self.instance.pk and self.instance.transactions.exists() and value != self.instance.opening_date:
            raise forms.ValidationError("Opening date is locked once transactions exist.")
        return value

    def clean_currency(self):
        value = self.cleaned_data["currency"]
        if self.instance.pk and self.instance.transactions.exists() and value != self.instance.currency:
            raise forms.ValidationError("Currency is locked once transactions exist.")
        return value


class TransactionForm(forms.ModelForm):
    submission_key = forms.UUIDField(required=False, widget=forms.HiddenInput, initial=uuid.uuid4)

    class Meta:
        model = Transaction
        fields = ["date", "description", "amount", "kind", "category", "account", "status", "due_date", "reference", "notes", "is_critical", "recurring_obligation"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, business, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        self.fields["account"].queryset = business.accounts.all()
        self.fields["recurring_obligation"].queryset = business.recurring_obligations.all()
        self.fields["account"].label_from_instance = lambda obj: obj.name
        self.fields["date"].initial = timezone.localdate()
        self.fields["account"].initial = business.accounts.first()

    def clean(self):
        data = super().clean()
        if data.get("date") and data["date"] < self.business.opening_date:
            self.add_error("date", "Transaction date must be on or after the opening balance date.")
        if data.get("status") == "pending" and data.get("kind") not in ("receivable", "payable", "income", "expense"):
            self.add_error("status", "This transaction type must be paid.")
        if data.get("status") == "pending" and not data.get("due_date"):
            self.add_error("due_date", "Set an expected payment date.")
        return data


class ScenarioForm(forms.Form):
    name = forms.CharField(max_length=80)
    revenue_change = forms.DecimalField(min_value=-100, max_value=1000, initial=0)
    expense_change = forms.DecimalField(min_value=-100, max_value=1000, initial=0)
    employees = forms.IntegerField(min_value=0, max_value=10000, initial=0)
    salary = forms.DecimalField(min_value=0, max_value=Decimal("1000000000"), initial=0)
    inventory = forms.DecimalField(min_value=0, initial=0)
    marketing = forms.DecimalField(min_value=0, initial=0)
    collection_delay = forms.DecimalField(min_value=0, initial=0, label="Collections delayed beyond period (amount)")
    supplier_delay = forms.DecimalField(min_value=0, initial=0, label="Supplier payments delayed beyond period (amount)")
    financing = forms.DecimalField(min_value=0, initial=0)
    repayment = forms.DecimalField(min_value=0, initial=0)


class LoanForm(forms.Form):
    amount = forms.DecimalField(min_value=Decimal("0.01"), max_value=Decimal("1000000000000"), initial=100000)
    annual_rate = forms.DecimalField(min_value=0, max_value=1000, initial=12)
    months = forms.IntegerField(min_value=1, max_value=600, initial=12)
    fees = forms.DecimalField(min_value=0, initial=0)
    monthly_capacity = forms.DecimalField(min_value=0, initial=10000)


class RecurringForm(forms.ModelForm):
    category = forms.CharField(max_length=80, required=False, initial='General')

    def clean_category(self):
        return self.cleaned_data.get('category') or 'General'

    class Meta:
        model = RecurringObligation
        fields = ["description", "amount", "direction", "next_due", "frequency", "category", "is_critical"]
        widgets = {"next_due": forms.DateInput(attrs={"type": "date"})}


class FinancialPolicyForm(forms.ModelForm):
    minimum_reserve = forms.DecimalField(min_value=0, max_digits=18, decimal_places=2,
                                         label='Minimum operating reserve')
    restricted_categories = forms.CharField(required=False, max_length=2400,
                                            help_text='Comma-separated category names; protected from plan changes.')

    class Meta:
        from .models import FinancialPolicy
        model = FinancialPolicy
        fields = ['horizon_days', 'protect_payroll', 'protect_critical_suppliers', 'max_delay_days',
                  'max_borrowing', 'max_annual_rate', 'risk_tolerance', 'concentration_percent',
                  'expense_increase_percent', 'restricted_categories', 'goal', 'issue_cooldown_hours']
        labels = {'max_borrowing': 'Maximum illustrative borrowing (0 means no borrowing)',
                  'goal': 'Financial objectives', 'horizon_days': 'Planning horizon (days)',
                  'protect_payroll': 'Protect payroll dates and amounts',
                  'protect_critical_suppliers': 'Protect critical supplier commitments',
                  'max_delay_days': 'Maximum supplier delay to discuss (days)',
                  'max_annual_rate': 'Maximum illustrative annual interest rate (%)'}
        help_texts = {'protect_payroll': 'Plans cannot delay, split or reduce protected payroll.',
                      'protect_critical_suppliers': 'Mark critical payments in transactions or recurring commitments.',
                      'max_delay_days': 'A planning limit only. A supplier must agree before you change a payment.',
                      'max_borrowing': 'Illustrations only; no loan approval or lender availability is inferred.'}

    def __init__(self, *args, business, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['minimum_reserve'].initial = business.low_cash_threshold
        self.fields['minimum_reserve'].help_text = 'The amount of money you want to keep available. A forecast cannot guarantee this buffer.'
        self.initial['restricted_categories'] = ', '.join(self.instance.restricted_categories or [])

    def clean_restricted_categories(self):
        return [value.strip() for value in self.cleaned_data['restricted_categories'].split(',') if value.strip()]

    def clean(self):
        from pydantic import ValidationError as SchemaError
        from .intelligence.schemas import PolicySpec
        data = super().clean()
        if not self.errors:
            try:
                PolicySpec.model_validate({key: data[key] for key in PolicySpec.model_fields})
            except SchemaError:
                raise forms.ValidationError('Check preference bounds: horizon 7–90 days; delay 0–90; concentration 1–100%; growth 1–1000%; cooldown 1–168 hours; up to 30 categories of 80 characters.')
        return data


class InvestigationForm(forms.Form):
    question = forms.CharField(max_length=4000, widget=forms.Textarea(attrs={'rows': 2}),
                               initial='Can I cover my scheduled payments and protect payroll?')
    request_key = forms.UUIDField(widget=forms.HiddenInput)
    issue_id = forms.IntegerField(required=False, min_value=1, widget=forms.HiddenInput)


class DecisionForm(forms.Form):
    target = forms.ChoiceField(choices=[(s, s.title()) for s in ['accepted', 'rejected', 'modified', 'monitoring', 'closed']])
    selected_plan = forms.CharField(required=False, max_length=80)
    feedback = forms.CharField(required=False, max_length=4000, widget=forms.Textarea(attrs={'rows': 2}))
    modified_plan = forms.JSONField(required=False)

    def clean_modified_plan(self):
        from .intelligence.schemas import PlanSpec
        from pydantic import ValidationError as SchemaError
        value = self.cleaned_data.get('modified_plan')
        if value:
            try:
                return PlanSpec.model_validate(value).model_dump(mode='json')
            except SchemaError:
                raise forms.ValidationError('Use a named plan with at most eight valid bounded actions.')
        return None
