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
    class Meta:
        model = Transaction
        fields = ["date", "description", "amount", "kind", "category", "account", "status", "due_date", "reference", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, business, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        self.fields["account"].queryset = business.accounts.all()
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
    class Meta:
        model = RecurringObligation
        fields = ["description", "amount", "direction", "next_due", "frequency"]
        widgets = {"next_due": forms.DateInput(attrs={"type": "date"})}
