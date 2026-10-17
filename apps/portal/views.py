import uuid
from datetime import date, timedelta
from decimal import Decimal
from functools import wraps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction as db_transaction, IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .access import authorized_business, audit
from .models import (
    Membership,
    FinancialAccount,
    Transaction,
    Scenario,
    LoanProduct,
    LoanComparison,
    Conversation,
    Message,
    DataImport,
    RecurringObligation,
)
from .forms import SignupForm, BusinessForm, TransactionForm, ScenarioForm, LoanForm, RecurringForm, EmailAuthenticationForm
from .engine import summary, monthly_chart, forecast, simulate, loan_schedule, backtest
from .imports import preview_import, confirm_import, FIELDS
from .reports import export_report
from .advisor import answer
from .forms import FinancialPolicyForm, InvestigationForm, DecisionForm
from .models import FinancialPolicy, FinancialIssue, Investigation, FinancialDecision, Business
from .intelligence.financial_state import build_state
from .intelligence.issue_detection import detect_issues
from .intelligence.investigation import run_investigation
from .intelligence.decision_memory import decide, monitor_decision
from .intelligence.financing import financing_assessment


def limited(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method == "POST":
            # Do not trust forwarded IP headers. Production should also rate-limit at ingress.
            key = "sensitive:" + request.META.get("REMOTE_ADDR", "") + ":" + str(request.user.pk) + ":" + view.__name__
            cache.add(key, 0, 300)
            if cache.incr(key) > 20:
                return HttpResponse("Too many requests. Try again in five minutes.", status=429)
        return view(request, *args, **kwargs)

    return wrapped


def landing(request):
    return render(request, "landing.html")


def legal(request, page):
    content = {
        "privacy": (
            "Privacy policy",
            "FinPilot stores account details and the business records you enter. Authorized workspace members can access those records. If you use a configured AI provider, authorized aggregate financial information is sent to that provider. Contact the deployment operator for export, correction, deletion, and retention requests. Do not upload data you are not authorized to process.",
        ),
        "terms": (
            "Terms of use",
            "FinPilot is a financial decision-support tool. You are responsible for the accuracy and completeness of submitted records. Forecasts and simulations depend on assumptions; they are not guarantees, audited financial statements, loan approvals, or professional advice. Do not use the service to process unauthorized data.",
        ),
        "about": (
            "Built for better business decisions",
            "FinPilot AI brings your business records, cash planning, financing calculations, and a configured financial assistant into one private workspace. Built for the 2026 FinTechathon, Topic E: SME Finance Copilot.",
        ),
        "contact": (
            "Contact",
            "For project support, open an issue in the GitHub repository linked below. For privacy requests, contact the operator of your FinPilot deployment.",
        ),
    }
    if page not in content:
        return HttpResponse(status=404)
    title, body = content[page]
    return render(request, "legal.html", {"title": title, "body": body})


@limited
def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with db_transaction.atomic():
                user = form.save()
        except IntegrityError:
            form.add_error("email", "An account with this email already exists.")
        else:
            token = signing.dumps({"id": user.pk}, salt="verify-email")
            url = settings.SITE_URL + reverse("verify", args=[token])
            send_mail("Verify your FinPilot account", "Activate your account: " + url, settings.DEFAULT_FROM_EMAIL, [user.email])
            return render(
                request,
                "notice.html",
                {
                    "title": "Check your email",
                    "body": "Open your verification link to activate your account. In development, email appears in the server console.",
                },
            )
    return render(
        request,
        "auth.html",
        {
            "form": form,
            "title": "Create your account",
            "subtitle": "Your next chapter starts with a clearer picture.",
            "button": "Create account",
            "signup": True,
        },
    )


def verify(request, token):
    try:
        data = signing.loads(token, salt="verify-email", max_age=86400)
        user = User.objects.get(pk=data["id"])
    except (signing.BadSignature, User.DoesNotExist, KeyError):
        return HttpResponseBadRequest("Invalid or expired verification link.")
    if request.method == "POST":
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        return redirect("business_new")
    return render(request, "verify.html")


@limited
def signin(request):
    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("workspace")
    return render(
        request,
        "auth.html",
        {"form": form, "title": "Welcome back", "subtitle": "A little clarity. A lot of possibility.", "button": "Sign in"},
    )


@login_required
def workspace(request):
    membership = Membership.objects.filter(user=request.user).select_related("business").first()
    if not membership:
        return redirect("business_new")
    active = request.session.get("active_business")
    if active:
        selected = Membership.objects.filter(user=request.user, business_id=active).first()
        if selected:
            membership = selected
    return redirect("dashboard", business_id=membership.business_id)


@login_required
def business_new(request):
    form = BusinessForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with db_transaction.atomic():
            business = form.save()
            Membership.objects.create(business=business, user=request.user)
            FinancialAccount.objects.create(business=business, name="Operating account")
            audit(request.user, business, "business.created", business.pk)
        request.session["active_business"] = str(business.pk)
        return redirect("dashboard", business_id=business.pk)
    return render(request, "onboarding.html", {"form": form})


@login_required
@require_POST
def switch(request, business_id):
    business = authorized_business(request.user, business_id)
    request.session["active_business"] = str(business.pk)
    request.session.cycle_key()
    return redirect("dashboard", business_id=business.pk)


def context(request, business, page):
    return {
        "business": business,
        "page": page,
        "memberships": Membership.objects.filter(user=request.user).select_related("business"),
        "owner": Membership.objects.filter(business=business, user=request.user, role="owner").exists(),
        "alerts": business.alerts.filter(active=True)[:3],
        "today": timezone.localdate(),
    }


def reporting_period(request):
    try:
        days = int(request.GET.get("days", 30))
        if days not in (7, 30, 90, 180, 365):
            days = 30
        end = date.fromisoformat(request.GET["end"]) if request.GET.get("end") else timezone.localdate()
        start = date.fromisoformat(request.GET["start"]) if request.GET.get("start") else end - timedelta(days=days - 1)
        if start > end:
            raise ValueError
        return start, end, days
    except (ValueError, OverflowError):
        return timezone.localdate() - timedelta(days=29), timezone.localdate(), 30


@login_required
def dashboard(request, business_id):
    business = authorized_business(request.user, business_id)
    start, end, days = reporting_period(request)
    data = context(request, business, "dashboard")
    data.update(
        {
            "financial_state": build_state(business),
            "stats": summary(business, start, end),
            "chart": monthly_chart(business),
            "recent": business.transactions.filter(archived=False)[:5],
            "days": days,
            "start": start,
            "end": end,
        }
    )
    data['watchtower'] = detect_issues(data['financial_state'])[:5]
    data['monitoring'] = business.monitoring_runs.order_by('-started_at').first()
    data['active_decisions'] = business.decisions.filter(state__in=['accepted', 'monitoring']).count()
    return render(request, "dashboard.html", data)


@login_required
def my_business(request, business_id):
    business = authorized_business(request.user, business_id)
    tab = request.GET.get("tab", "overview")
    if tab not in ("overview", "transactions", "sales", "expenses", "upload"):
        tab = "overview"
    form = BusinessForm(instance=business)
    if request.method == "POST":
        authorized_business(request.user, business_id, write=True)
        form = BusinessForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            audit(request.user, business, "business.updated", business.pk)
            messages.success(request, "Business details updated.")
            return redirect(reverse("my_business", args=[business.pk]))
    rows = business.transactions.filter(archived=False)
    if tab == "sales":
        rows = rows.filter(kind__in=["income", "receivable", "refund"])
    if tab == "expenses":
        rows = rows.filter(kind__in=["expense", "payable"])
    query = request.GET.get("q", "")[:200]
    if query:
        rows = rows.filter(description__icontains=query)
    if request.GET.get("kind") in dict(Transaction.TYPES):
        rows = rows.filter(kind=request.GET["kind"])
    data = context(request, business, "my_business")
    policy = FinancialPolicy.objects.filter(business=business).first() or FinancialPolicy(business=business)
    data['policy_form'] = FinancialPolicyForm(instance=policy, business=business)
    from django.core.paginator import Paginator

    data.update(
        {
            "tab": tab,
            "form": form,
            "rows": Paginator(rows, 30).get_page(request.GET.get("p")),
            "query": query,
            "chart": monthly_chart(business),
            "imports": DataImport.objects.filter(business=business).order_by("-created_at")[:10],
            "fields": FIELDS,
            "stats": summary(business),
            "recurring_form": RecurringForm(),
            "obligations": business.recurring_obligations.filter(active=True),
        }
    )
    return render(request, "business.html", data)


@login_required
@require_POST
def recurring_add(request, business_id):
    business = authorized_business(request.user, business_id, write=True)
    form = RecurringForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.business = business
        item.save()
        audit(request.user, business, "recurring.created", item.pk)
        messages.success(request, "Recurring commitment saved. Forecasts include future due dates; actual records are unchanged.")
    else:
        messages.error(request, form.errors.as_text())
    return redirect("my_business", business_id=business.pk)


@login_required
@require_POST
def recurring_disable(request, business_id, pk):
    business = authorized_business(request.user, business_id, write=True)
    item = get_object_or_404(RecurringObligation, business=business, pk=pk)
    item.active = False
    item.save(update_fields=["active"])
    audit(request.user, business, "recurring.disabled", item.pk)
    return redirect("my_business", business_id=business.pk)


@login_required
def transaction_edit(request, business_id, pk=None):
    business = authorized_business(request.user, business_id, write=True)
    item = get_object_or_404(Transaction, pk=pk, business=business, archived=False) if pk else None
    before = {field: str(getattr(item, field)) for field in TransactionForm.Meta.fields} if item else {}
    form = TransactionForm(request.POST or None, instance=item, business=business)
    if request.method == "POST" and form.is_valid():
        with db_transaction.atomic():
            item = form.save(commit=False)
            item.business = business
            item.currency = business.currency
            item.save()
            audit(
                request.user,
                business,
                "transaction.updated" if pk else "transaction.created",
                item.pk,
                {"before": before, "after": {field: str(getattr(item, field)) for field in TransactionForm.Meta.fields}},
            )
        messages.success(request, "Transaction saved.")
        return redirect(reverse("my_business", args=[business.pk]) + "?tab=transactions")
    data = context(request, business, "my_business")
    data.update({"form": form, "title": "Edit transaction" if pk else "Add a transaction"})
    return render(request, "form.html", data)


@login_required
@require_POST
def transaction_archive(request, business_id, pk):
    business = authorized_business(request.user, business_id, write=True)
    item = get_object_or_404(Transaction, pk=pk, business=business)
    item.archived = True
    item.save(update_fields=["archived"])
    audit(request.user, business, "transaction.archived", item.pk)
    messages.success(request, "Entry voided. The original entry and audit event are retained.")
    return redirect(reverse("my_business", args=[business.pk]) + "?tab=transactions")


@login_required
@require_POST
def upload(request, business_id):
    business = authorized_business(request.user, business_id, write=True)
    if "file" not in request.FILES:
        return HttpResponseBadRequest("Choose a file.")
    try:
        mapping = {field: request.POST.get("map_" + field, "").strip() for field in FIELDS}
        item = preview_import(business, request.FILES["file"], mapping)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect(reverse("my_business", args=[business.pk]) + "?tab=upload")
    data = context(request, business, "my_business")
    data["item"] = item
    return render(request, "import_preview.html", data)


@login_required
@require_POST
def import_confirm(request, business_id, pk):
    business = authorized_business(request.user, business_id, write=True)
    get_object_or_404(DataImport, pk=pk, business=business)
    try:
        count = confirm_import(business, request.user, pk)
        messages.success(request, f"{count} transactions imported.")
    except (ValidationError, IntegrityError) as exc:
        messages.error(request, str(exc))
    return redirect(reverse("my_business", args=[business.pk]) + "?tab=upload")


@login_required
def planning(request, business_id):
    business = authorized_business(request.user, business_id)
    tab = request.GET.get("tab", "forecast")
    data = context(request, business, "planning")
    data['financial_state'] = build_state(business)
    data['issues'] = detect_issues(data['financial_state'])
    data['investigation_form'] = InvestigationForm(initial={'request_key': uuid.uuid4()})
    data['decisions'] = business.decisions.select_related('investigation').order_by('-created_at')[:50]
    scenario_form = ScenarioForm(request.POST if request.method == "POST" and tab == "scenarios" else None)
    loan_form = LoanForm(request.POST if request.method == "POST" and tab == "loans" else None)
    if request.method == "POST" and tab == "scenarios":
        authorized_business(request.user, business_id, write=True)
        if scenario_form.is_valid():
            assumptions = {k: str(v) for k, v in scenario_form.cleaned_data.items() if k != "name"}
            scenario = Scenario.objects.create(
                business=business, name=scenario_form.cleaned_data["name"], assumptions=assumptions, result=simulate(business, assumptions)
            )
            audit(request.user, business, "scenario.saved", scenario.pk)
            messages.success(request, "Scenario saved. Actual transactions are unchanged.")
            return redirect(reverse("planning", args=[business.pk]) + "?tab=scenarios")
    if request.method == "POST" and tab == "loans" and loan_form.is_valid():
        values = loan_form.cleaned_data
        result = loan_schedule(values["amount"], values["annual_rate"], values["months"], values["fees"])
        result["capacity_warning"] = Decimal(result["payment"]) > values["monthly_capacity"]
        data["loan"] = result
        if values['months'] <= 120 and values['amount'] <= 1000000000 and values['fees'] <= 1000000000:
            data['financing_assessment'] = financing_assessment(data['financial_state'], values['amount'], values['annual_rate'], values['months'], values['fees'])
        if request.POST.get("save_comparison"):
            authorized_business(request.user, business_id, write=True)
            comparison = LoanComparison.objects.create(business=business, assumptions={k: str(v) for k, v in values.items()}, result=result)
            audit(request.user, business, "financing.saved", comparison.pk)
            messages.success(request, "Financing illustration saved for export. No application or real payment occurred.")
        products = LoanProduct.objects.filter(
            country=business.country,
            currency=business.currency,
            active=True,
            minimum__lte=values["amount"],
            maximum__gte=values["amount"],
            min_months__lte=values["months"],
            max_months__gte=values["months"],
        )
        data["products"] = [
            {"product": p, "result": loan_schedule(values["amount"], p.annual_rate, values["months"], p.fee)} for p in products if p.valid_until is None or p.valid_until >= timezone.localdate()
        ]
    try:
        horizon = int(request.GET.get("horizon", 30))
        projection = forecast(business, horizon)
    except ValueError:
        horizon, projection = 30, forecast(business, 30)
    data.update(
        {
            "tab": tab,
            "forecast": projection,
            "horizon": horizon,
            "backtest": backtest(business),
            "scenario_form": scenario_form,
            "loan_form": loan_form,
            "scenarios": business.scenarios.order_by("-created_at")[:3],
        }
    )
    return render(request, "planning.html", data)


@login_required
@limited
def advisor(request, business_id):
    business = authorized_business(request.user, business_id)
    conversation = Conversation.objects.filter(business=business, user=request.user).first()
    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if not question or len(question) > 4000:
            messages.error(request, "Enter a question of up to 4,000 characters.")
        else:
            if conversation is None:
                conversation = Conversation.objects.create(business=business, user=request.user)
            Message.objects.create(conversation=conversation, role="user", content=question)
            try:
                result = answer(request.user, business, question)
            except (Exception,) as exc:
                # Never expose upstream response bodies, keys, or raw financial prompts.
                import logging

                logging.getLogger(__name__).warning("Advisor failed: %s", type(exc).__name__)
                result = "The AI provider is unavailable or returned an invalid tool request. Please retry. Your records were not changed."
            Message.objects.create(conversation=conversation, role="assistant", content=result)
            audit(request.user, business, "advisor.asked", conversation.pk)
        return redirect("advisor", business_id=business.pk)
    data = context(request, business, "advisor")
    data.update(
        {
            "chat_messages": conversation.messages.order_by("created_at") if conversation else [],
            "investigation_form": InvestigationForm(initial={'request_key': uuid.uuid4()}),
            "latest_investigation": business.investigations.filter(user=request.user).order_by('-created_at').first(),
            "configured": bool(settings.LLM_API_KEY and settings.LLM_MODEL),
            "stats": summary(business),
        }
    )
    return render(request, "advisor.html", data)


@login_required
def reports(request, business_id):
    business = authorized_business(request.user, business_id)
    start, end, days = reporting_period(request)
    kind = request.GET.get("type", "summary")
    if kind not in ("summary", "transactions", "forecast", "scenarios", "financing", "quality", "decisions", "investigations", "issues"):
        kind = "summary"
    if request.GET.get("format") in ("csv", "xlsx", "pdf"):
        return export_report(request.user, business, request.GET["format"], start, end, kind)
    data = context(request, business, "reports")
    data["decisions"] = business.decisions.select_related("investigation").order_by("-created_at")[:20]
    data.update({"stats": summary(business, start, end), "chart": monthly_chart(business), "start": start, "end": end, "report_type": kind})
    return render(request, "reports.html", data)


@api_view(["GET"])
def api_summary(request, business_id):
    business = authorized_business(request.user, business_id)
    return Response(summary(business))


def health(request):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


@login_required
@require_POST
def financial_policy(request, business_id):
    business = authorized_business(request.user, business_id, write=True)
    with db_transaction.atomic():
        business = Business.objects.select_for_update().get(pk=business.pk)
        policy = FinancialPolicy.objects.filter(business=business).first() or FinancialPolicy(business=business)
        form = FinancialPolicyForm(request.POST, instance=policy, business=business)
        if form.is_valid():
            form.save()
            business.low_cash_threshold = form.cleaned_data['minimum_reserve']
            business.save(update_fields=['low_cash_threshold'])
            audit(request.user, business, 'policy.updated', policy.pk)
            messages.success(request, 'Preferences saved. New investigations use these settings; historical evidence is unchanged.')
            return redirect('my_business', business_id=business.pk)
    data = context(request, business, 'my_business')
    data.update({'form': form, 'title': 'Review financial preferences'})
    return render(request, 'form.html', data, status=400)


@login_required
@require_POST
@limited
def investigation_start(request, business_id):
    business = authorized_business(request.user, business_id, write=True)
    form = InvestigationForm(request.POST)
    if form.is_valid():
        try:
            item = run_investigation(request.user, business.pk, **form.cleaned_data)
            return redirect('investigation_detail', business_id=business.pk, pk=item.pk)
        except (ValidationError, ValueError):
            form.add_error(None, 'Investigation could not be completed. Review your records and retry.')
    data = context(request, business, 'planning')
    data.update({'form': form, 'title': 'Review investigation request'})
    return render(request, 'form.html', data, status=400)


@login_required
def investigation_detail(request, business_id, pk):
    business = authorized_business(request.user, business_id)
    item = get_object_or_404(Investigation.objects.select_related('decision'), business=business, pk=pk)
    data = context(request, business, 'planning')
    data.update({'investigation': item, 'decision': item.decision,
                 'stale': build_state(business)['fingerprint'] != item.snapshot['fingerprint']})
    return render(request, 'investigation.html', data)


@login_required
def issue_detail(request, business_id, pk):
    business = authorized_business(request.user, business_id)
    issue = get_object_or_404(FinancialIssue, business=business, pk=pk)
    data = context(request, business, 'planning')
    data.update({'issue': issue, 'investigation_form': InvestigationForm(initial={
        'request_key': uuid.uuid4(), 'issue_id': issue.pk, 'question': issue.title})})
    return render(request, 'issue.html', data)


@login_required
@require_POST
def decision_update(request, business_id, pk):
    business = authorized_business(request.user, business_id, write=True)
    item = get_object_or_404(FinancialDecision, business=business, pk=pk)
    form = DecisionForm(request.POST)
    if form.is_valid():
        try:
            decide(request.user, business.pk, item.pk, **form.cleaned_data)
            messages.success(request, 'Decision recorded. No payments, collections or external actions were executed.')
        except (ValidationError, ValueError) as exc:
            messages.error(request, '; '.join(exc.messages) if isinstance(exc, ValidationError) else 'Invalid plan. Review the dates and amounts.')
    else:
        messages.error(request, 'Decision not recorded. Check the action, plan and feedback fields.')
    return redirect('investigation_detail', business_id=business.pk, pk=item.investigation_id)


@login_required
@require_POST
def decision_review(request, business_id, pk):
    business = authorized_business(request.user, business_id, write=True)
    item = get_object_or_404(FinancialDecision, business=business, pk=pk)
    monitor_decision(item)
    messages.success(request, 'Review checked against recorded data. Insufficient evidence is shown explicitly.')
    return redirect('investigation_detail', business_id=business.pk, pk=item.investigation_id)
