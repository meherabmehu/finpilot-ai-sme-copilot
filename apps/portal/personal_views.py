"""Consumer workflows share authorization, ledger writers, exports and AI transport."""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import render,redirect
from django.utils import timezone

from .access import authorized_business,audit
from .models import Business,PersonalProfile,Membership,FinancialAccount,Transaction,RecurringObligation,Scenario
from .personal_forms import PersonalOnboardingForm,PersonalScenarioForm,PersonalRecurringForm
from .intelligence.personal_finance import personal_state,overview,simulate,demo_state,question_analysis


def require_personal(request,business_id,write=False):
    business=authorized_business(request.user,business_id,write=write)
    if business.mode!='personal':
        raise Http404('Choose a personal workspace.')
    return business


@login_required
def personal_new(request):
    form=PersonalOnboardingForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        data=form.cleaned_data
        today=timezone.localdate()
        with transaction.atomic():
            business=Business.objects.create(mode='personal',name=data['name'],category='Personal',country=data['country'],currency=data['currency'],
                opening_balance=data['available_cash'],opening_date=today,low_cash_threshold=data['reserve'],cash_records_complete=data['complete'])
            Membership.objects.create(business=business,user=request.user)
            account=FinancialAccount.objects.create(business=business,name='Personal cash')
            PersonalProfile.objects.create(workspace=business,income_type=data['income_type'],savings_target=data['savings_target'] or 0)
            if data['expected_income']:
                Transaction.objects.create(business=business,account=account,date=today,currency=business.currency,kind='receivable',status='pending',
                    amount=data['expected_income'],due_date=data['income_date'],category='Freelance income' if data['income_type']=='freelance' else 'Other income',description='Expected personal income')
            if data['monthly_essentials']:
                RecurringObligation.objects.create(business=business,description='Essential monthly bills (owner total)',category='Essential living costs',
                    direction='outflow',amount=data['monthly_essentials'],next_due=data['bills_date'],frequency='monthly',is_critical=True)
            audit(request.user,business,'business.created',business.pk,{'mode':'personal'})
        request.session['active_business']=str(business.pk)
        return redirect('dashboard',business_id=business.pk)
    return render(request,'personal_onboarding.html',{'form':form})


def personal_dashboard(request,business):
    from .views import context
    state=personal_state(business)
    return render(request,'personal_dashboard.html',{**context(request,business,'dashboard'),'state':state,'personal':overview(state)})


def personal_records(request,business):
    from .views import context
    if request.method=='POST':
        authorized_business(request.user,business.pk,write=True)
        from django import forms
        class Preferences(forms.Form):
            reserve=forms.DecimalField(min_value=0,max_value=1000000000,decimal_places=2)
            savings_target=forms.DecimalField(min_value=0,max_value=1000000000,decimal_places=2)
            complete=forms.BooleanField(required=False)
        form=Preferences(request.POST)
        if form.is_valid():
            with transaction.atomic():
                locked=Business.objects.select_for_update().get(pk=business.pk)
                locked.low_cash_threshold=form.cleaned_data['reserve']
                locked.cash_records_complete=form.cleaned_data['complete']
                locked.save(update_fields=['low_cash_threshold','cash_records_complete'])
                PersonalProfile.objects.filter(workspace=locked).update(savings_target=form.cleaned_data['savings_target'])
                audit(request.user,locked,'business.updated',locked.pk,{'mode':'personal'})
            return redirect('my_business',business_id=business.pk)
        errors=form.errors
    else:
        errors=None
    state=personal_state(business)
    return render(request,'personal_records.html',{**context(request,business,'my_business'),'state':state,'personal':overview(state),
        'records':business.transactions.filter(archived=False)[:100],'recurring':business.recurring_obligations.filter(active=True),
        'recurring_form':PersonalRecurringForm(),'preference_errors':errors})


def personal_planning(request,business):
    from .views import context
    state=personal_state(business)
    form=PersonalScenarioForm(request.POST or None,state=state)
    result=None
    if request.method=='POST' and form.is_valid():
        values=form.cleaned_data
        try:
            result=simulate(state,values['scenario'],amount=values['amount'],event_date=values['event_date'],delay_days=values['delay_days'] or 7,
                reduction=values['reduction'] or 20,income_reference=values['income_reference'])
            if values['save']:
                authorized_business(request.user,business.pk,write=True)
                Scenario.objects.create(business=business,name='Personal: '+values['scenario'],assumptions={'kind':'personal_v1','description':result['assumptions']},result=result)
                audit(request.user,business,'scenario.personal_saved')
        except ValueError as exc:
            form.add_error(None,str(exc))
    return render(request,'personal_planning.html',{**context(request,business,'planning'),'state':state,'personal':overview(state),'form':form,'result':result,
        'saved_scenarios':business.scenarios.filter(result__kind='personal_v1')[:10]})


def personal_reports(request,business):
    from .views import context
    from .reports import export_report
    today=timezone.localdate()
    if request.GET.get('format') in ('pdf','csv','xlsx'):
        return export_report(request.user,business,request.GET['format'],today-timedelta(days=29),today,'personal')
    return render(request,'personal_reports.html',{**context(request,business,'reports'),'state':personal_state(business)})


def personal_demo(request):
    state=demo_state()
    if request.GET.get('format')=='pdf':
        from types import SimpleNamespace
        from django.http import HttpResponse
        from .report_sections import render_pdf,amount
        personal=overview(state)
        rows=[['Available paid cash',amount(personal['cash'])],['Upcoming bills',amount(personal['bills'])],
              ['Expected income (not cash)',amount(personal['expected_income'])],['Emergency reserve',amount(personal['reserve'])],
              ['After bills without future income',amount(personal['after_bills'])],['Conservative spending room',amount(personal['safe_to_spend'])]]
        content=render_pdf(SimpleNamespace(name='Fully synthetic freelancer demo',currency='BDT'),state['as_of'],state['end_date'],
            [['Demo','Synthetic'],['Source','Built-in synthetic assumptions'],['Mode','Personal'],['Basis',personal['basis']]],
            [{'title':'Synthetic personal financial snapshot','headers':['Measure','BDT amount'],'rows':rows}])
        response=HttpResponse(content,content_type='application/pdf')
        response['Content-Disposition']='attachment; filename="finpilot-synthetic-personal.pdf"'
        return response
    form=PersonalScenarioForm(request.POST if request.method=='POST' and 'scenario' in request.POST else None,state=state)
    form.fields.pop('save',None)
    result=None
    explanation=None
    if request.method=='POST' and 'scenario' in request.POST and form.is_valid():
        data=form.cleaned_data
        if data.get('save'):
            form.add_error('save','This public demo never saves shared data. Create your own workspace to save a scenario.')
        else:
            try:
                result=simulate(state,data['scenario'],amount=data['amount'],event_date=data['event_date'],delay_days=data['delay_days'] or 7,
                    reduction=data['reduction'] or 20,income_reference=data['income_reference'])
            except ValueError as exc:
                form.add_error(None,str(exc))
    if request.method=='POST' and request.POST.get('question'):
        from .intelligence.ai_grounding import scope
        question=request.POST['question'][:4000]
        explanation=question_analysis(state,question) if scope(question) in ('financial','follow_up') else {'sections':[{'title':'Financial questions only','lines':['This question is outside personal finance. Try cash, bills, savings or delayed income.']}]}
    return render(request,'personal_demo.html',{'state':state,'personal':overview(state),'form':form,'result':result,'explanation':explanation})
