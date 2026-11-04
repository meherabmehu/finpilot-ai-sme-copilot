"""Consumer inputs using the existing scoped ledger and Decimal fields."""
from decimal import Decimal
from django import forms
from django.utils import timezone
from .forms import COUNTRIES,CURRENCIES,TransactionForm,RecurringForm
from .models import PersonalProfile

MAX=Decimal('1000000000')
CATEGORIES=['Salary','Freelance income','Other income','Rent','Utilities','Groceries','Education','Transportation','Debt payment','Medical','Other expenses']


class PersonalOnboardingForm(forms.Form):
    name=forms.CharField(max_length=120,initial='My personal finances',label='Workspace name')
    income_type=forms.ChoiceField(choices=PersonalProfile._meta.get_field('income_type').choices)
    country=forms.ChoiceField(choices=COUNTRIES[:-1],initial='BD')
    currency=forms.ChoiceField(choices=CURRENCIES,initial='BDT')
    available_cash=forms.DecimalField(max_digits=18,decimal_places=2,min_value=-MAX,max_value=MAX,label='Cash available right now')
    reserve=forms.DecimalField(min_value=0,max_value=MAX,decimal_places=2,initial=0,label='Emergency reserve to protect')
    savings_target=forms.DecimalField(required=False,min_value=0,max_value=MAX,decimal_places=2,label='Optional savings goal (not money already saved)')
    expected_income=forms.DecimalField(required=False,min_value=Decimal('.01'),max_value=MAX,decimal_places=2,label='Optional next expected income')
    income_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}),label='Expected receipt date (not guaranteed)')
    monthly_essentials=forms.DecimalField(required=False,min_value=Decimal('.01'),max_value=MAX,decimal_places=2,label='Optional essential monthly bills total')
    bills_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}),label='Next monthly bill date')
    complete=forms.BooleanField(label='I have included my available cash and upcoming commitments',help_text='You can add individual bills next. Missing bills make spending estimates unreliable.')

    def clean(self):
        data=super().clean()
        for amount,day in [('expected_income','income_date'),('monthly_essentials','bills_date')]:
            if bool(data.get(amount))!=bool(data.get(day)):
                self.add_error(day,'Enter both an amount and its date, or leave both empty.')
            if data.get(day) and data[day]<timezone.localdate():
                self.add_error(day,'Use today or a future date; add overdue records separately after setup.')
        if data.get('monthly_essentials') and data.get('bills_date')==timezone.localdate():
            self.add_error('bills_date','Use the next future monthly bill date. Add a bill due today as an individual unpaid bill after setup; it must not disappear from your plan.')
        return data


class PersonalRecurringForm(RecurringForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['is_critical'].label='Essential bill'
        self.fields['next_due'].label='Next future occurrence'
    def clean_next_due(self):
        value=self.cleaned_data['next_due']
        if value<=timezone.localdate():
            raise forms.ValidationError('Recurring projections start in the future. Add a due-today or overdue bill as an individual unpaid bill in My Money.')
        return value


class PersonalTransactionForm(TransactionForm):
    category=forms.ChoiceField(choices=[(v,v) for v in CATEGORIES]+[('General','Uncategorized')])

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name in ('customer_alias','follow_up_status','dispute_status','promised_date','reported_partial_amount','confirmation_reference'):
            self.fields.pop(name,None)
        self.fields['recurring_obligation'].label='Optional link to an existing recurring bill or income'
        self.fields['recurring_obligation'].help_text='To avoid counting the same occurrence twice, choose its recurring entry and set Due date to that occurrence date, even for an early paid record.'
        self.fields['kind'].choices=[('income','Income received or expected'),('expense','Expense paid or planned'),('receivable','Expected income'),('payable','Upcoming bill'),('loan_repayment','Debt payment already paid'),('refund','Refund paid')]
        self.fields['status'].choices=[('paid','Already received / paid'),('pending','Expected / unpaid')]
        self.fields['is_critical'].label='Essential payment'
        self.fields['is_critical'].help_text='Record whether missing this payment could affect housing, health, study or essential daily needs. This does not authorize postponement.'
        self.fields['reference'].label='Optional payment reference'
        self.fields['due_date'].label='Bill due date or expected income date'


class PersonalScenarioForm(forms.Form):
    scenario=forms.ChoiceField(choices=[('delay','Delayed income'),('expense','Unexpected expense'),('savings','Savings target'),('reduced','Reduced future income')])
    delay_days=forms.ChoiceField(required=False,choices=[('7','7 days'),('14','14 days'),('30','30 days')],initial='7')
    amount=forms.DecimalField(required=False,min_value=Decimal('.01'),max_value=MAX,decimal_places=2,label='Extra expense or savings amount')
    event_date=forms.DateField(required=False,widget=forms.DateInput(attrs={'type':'date'}),label='Date of the expense or savings transfer')
    reduction=forms.ChoiceField(required=False,choices=[('10','10%'),('20','20%'),('30','30%')],initial='20')
    income_reference=forms.ChoiceField(required=False,label='Expected income to delay')
    save=forms.BooleanField(required=False,label='Save this hypothetical comparison')

    def __init__(self,*args,state,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['income_reference'].choices=[('','Choose a dated expected income')]+[(e['id'],f"{e['date']} · {e['amount']} {state['currency']} · {e['id']}") for e in state['events'] if e['id'] in state['collection_event_ids']]

    def clean(self):
        data=super().clean()
        if data.get('scenario')=='delay' and not data.get('income_reference'):
            self.add_error('income_reference','Choose the expected payment; no income is selected automatically.')
        if data.get('scenario') in ('expense','savings'):
            for field in ('amount','event_date'):
                if not data.get(field):
                    self.add_error(field,'This scenario requires an explicit amount and date.')
        return data
