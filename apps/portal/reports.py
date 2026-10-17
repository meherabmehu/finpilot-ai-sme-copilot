import csv
import io
from django.http import HttpResponse
from django.utils import timezone
from .engine import summary, forecast
from .imports import safe_cell
from .access import audit, authorized_business


def export_report(user, business, format, start, end, report_type="summary"):
    business = authorized_business(user, business.pk)
    values = summary(business, start, end)
    rows = [
        ["FinPilot financial report", business.name],
        ["Period", f"{start} to {end}"],
        ["Currency", business.currency],
        ["Generated UTC", timezone.now().isoformat()],
        ["Source", "Synthetic demonstration records" if business.is_demo else "User-entered records; completeness unverified"],
        ["Basis", "Recorded operating summary; not audited net profit. Cash balance is as of period end."],
    ]
    if report_type in ('decisions', 'investigations', 'issues'):
        rows.append(['Basis', 'Historical investigation snapshots and SIMULATED alternatives; observed outcomes are separately labeled. No causal improvement or external execution is inferred.'])
        if report_type == 'issues':
            rows.append(['Issue', 'Severity', 'Status', 'Calculated rule', 'Amount', 'As of'])
            for issue in business.financial_issues.order_by('-checked_at'):
                rows.append([issue.title, issue.severity, issue.status, issue.evidence.get('rule'), issue.evidence.get('amount'), issue.evidence.get('as_of')])
        else:
            for item in business.investigations.filter(created_at__date__gte=start, created_at__date__lte=end).select_related('decision').order_by('-created_at'):
                decision = item.decision
                rows.extend([
                    ['Investigation', str(item.pk), item.question, item.created_at.isoformat()],
                    ['Snapshot', item.snapshot['as_of'], item.snapshot['fingerprint'], item.snapshot['currency']],
                    ['Calculated recorded cash', item.snapshot['known_cash']],
                    ['Decision', decision.state, decision.selected_plan, 'Review', decision.review_date.isoformat()],
                    ['Expected (SIMULATED)', str(decision.expected)],
                    ['Observed outcome (if available)', str(decision.outcome)],
                    ['Selected plan (SIMULATED)', str(decision.selected_snapshot)],
                    ['Owner feedback', decision.feedback],
                    ['Ranking', item.result['comparison']['objective']],
                ])
                for plan in item.result['comparison']['plans']:
                    timeline = plan['timeline']
                    rows.extend([
                        ['SIMULATED plan', plan['name'], 'Within constraints', plan['feasible']],
                        ['Minimum cash', timeline.get('minimum_balance', 'Unknown'), 'Lowest date', timeline.get('lowest_date', 'Unknown')],
                        ['Reserve gap', timeline.get('funding_gap', 'Unknown'), 'Borrowing', plan['borrowing'], 'Full cost', plan['financing_cost']],
                        ['Beyond-horizon liabilities', plan['deferred_liabilities']],
                    ])
                    for note in plan['dependencies'] + plan['tradeoffs'] + plan['violations']:
                        rows.append(['Plan assumption / constraint', note])
                if report_type == 'investigations':
                    for node in item.result['evidence_graph']['nodes']:
                        rows.append(['Evidence', node['id'], node.get('label'), node.get('amount'), node.get('date'), node.get('basis'), node.get('source'), node.get('formula')])
                for note in item.snapshot['limitations']:
                    rows.append(['Limitation', note])
    elif report_type == "transactions":
        rows.append(["Date", "Description", "Type", "Amount", "Currency", "Status", "Category", "Reference"])
        rows.extend(
            [
                [r.date, r.description, r.kind, r.amount, r.currency, r.status, r.category, r.reference]
                for r in business.transactions.filter(archived=False, date__gte=start, date__lte=end)
            ]
        )
    elif report_type == "forecast":
        result = forecast(business)
        rows.append(["Method", result.get("limitations", result.get("reason"))])
        rows.append(["Date", "Projected balance", "Expected inflow", "Expected outflow"])
        rows.extend([[p["date"], p["balance"], p["inflow"], p["outflow"]] for p in result.get("points", [])])
    elif report_type == "scenarios":
        rows.append(["Scenario", "Revenue", "Expenses", "Cash delta", "Assumptions"])
        rows.extend(
            [
                [s.name, s.result["revenue"], s.result["expenses"], s.result["cash_delta"], str(s.assumptions)]
                for s in business.scenarios.all()
            ]
        )
    elif report_type == "financing":
        rows.append(["Saved UTC", "Principal", "Annual rate", "Months", "Monthly payment", "Total cost", "Fees"])
        rows.extend(
            [
                [
                    s.created_at.isoformat(),
                    s.assumptions["amount"],
                    s.assumptions["annual_rate"],
                    s.assumptions["months"],
                    s.result["payment"],
                    s.result["total_cost"],
                    s.result["fees"],
                ]
                for s in business.loan_comparisons.all()
            ]
        )
        rows.append(
            ["Limitations", "User-entered illustrations; not loan offers or approvals. Reducing-balance monthly repayments; upfront fees."]
        )
    elif report_type == "quality":
        rows.extend(
            [
                ["Record count", values["count"]],
                ["Cash records user-confirmed complete", business.cash_records_complete],
                ["Opening balance known", business.opening_balance is not None],
                ["Accounting completeness", "Not independently verified; inventory, taxes and accrual completeness are unknown."],
            ]
        )
    else:
        rows.extend([[k.replace("_", " ").title(), v if v is not None else "Unknown"] for k, v in values.items()])
    if format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerows([[safe_cell(x) for x in row] for row in rows])
        response = HttpResponse("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8")
    elif format == "xlsx":
        from openpyxl import Workbook

        book = Workbook()
        sheet = book.active
        sheet.title = "Financial report"
        for row in rows:
            sheet.append([safe_cell(x) for x in row])
        sheet.column_dimensions["A"].width = 30
        sheet.column_dimensions["B"].width = 60
        output = io.BytesIO()
        book.save(output)
        response = HttpResponse(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif format == "pdf":
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from xml.sax.saxutils import escape

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, title="FinPilot financial report")
        styles = getSampleStyleSheet()
        story = []
        for row in rows:
            story.extend([Paragraph(escape(" | ".join(str(x) for x in row)), styles["BodyText"]), Spacer(1, 9)])
        doc.build(story)
        response = HttpResponse(output.getvalue(), content_type="application/pdf")
    else:
        raise ValueError("Unsupported export format")
    response["Content-Disposition"] = f'attachment; filename="finpilot-{report_type}.{format}"'
    audit(user, business, "report.exported", report_type + "." + format)
    return response
