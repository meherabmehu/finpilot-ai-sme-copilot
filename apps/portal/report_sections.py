"""Shared, readable financial report sections for PDF and spreadsheet exports."""
from decimal import Decimal


def amount(value):
    return Decimal(str(value)) if value is not None else 'Unknown'


def agentic_sections(business, start, end, report_type):
    sections = []

    def add(title, headers, rows):
        sections.append({'title': title, 'headers': headers, 'rows': rows or [['No records available for this selection.']]})

    if report_type == 'issues':
        add('Executive summary', ['Basis', 'Meaning'], [['Latest persisted issue state', 'Calculated from recorded data; invoke monitoring for refresh. No guarantee of financial health.']])
        add('Financial issues', ['Issue / severity', 'Status / as of', 'Amount', 'Rule'], [
            [f'{issue.title} ({issue.severity})', f"{issue.status} / {issue.evidence.get('as_of', 'unknown')}",
             amount(issue.evidence.get('amount')), issue.evidence.get('rule', '')]
            for issue in business.financial_issues.order_by('-checked_at')])
        return sections
    items = list(business.investigations.filter(created_at__date__gte=start, created_at__date__lte=end).select_related('decision').order_by('-created_at'))
    add('Executive summary', ['Measure', 'Summary'], [
        ['Saved investigations in period', len(items)],
        ['Financial basis', 'Historical evidence, estimated dated cash and SIMULATED alternatives. Actual observed outcomes are labeled separately.'],
        ['Recommendation scope', 'Best among evaluated candidates, not globally optimal. Action feasibility does not prove reserve satisfaction.'],
    ])
    for index, item in enumerate(items, 1):
        state, result, decision = item.snapshot, item.result, item.decision
        add(f'{index}. Decision and investigation summary', ['Field', 'Value'], [
            ['Financial question', item.question], ['Saved UTC', item.created_at.isoformat()],
            ['Decision status', decision.get_state_display()], ['Review date', decision.review_date.isoformat()],
            ['Recommended for review', result.get('recommended') or 'Unknown'],
            ['Recommendation caveat', result['comparison'].get('recommendation_note', 'Best among evaluated candidates; inspect remaining gaps.')],
        ])
        for section in result.get('analysis', {}).get('sections', []):
            add(section['title'], ['Question-specific evidence'], [[line] for line in section['lines']])
        projection = state['projection']
        add('Original financial state', ['Measure', 'Value'], [
            ['Snapshot as of', state['as_of']], ['Recorded cash (paid ledger)', amount(state['known_cash'])],
            ['Minimum operating reserve', amount(state['policy']['reserve'])],
            ['Minimum estimated cash', amount(projection.get('minimum_balance'))],
            ['Lowest estimated cash date', projection.get('lowest_date', 'Unknown')],
            ['Original reserve gap', amount(projection.get('funding_gap'))],
            ['Completeness', 'User-confirmed; not independently audited' if state['complete'] else 'Incomplete / unknown'],
        ])
        add('Alternative comparison (SIMULATED)', ['Candidate', 'Minimum cash', 'Reserve gap', 'Borrowing', 'Full cost', 'Status'], [
            [plan['name'], amount(plan['timeline'].get('minimum_balance')), amount(plan['timeline'].get('funding_gap')),
             amount(plan['borrowing']), amount(plan['financing_cost']),
             (plan.get('goal_status') or ('Within action constraints' if plan['feasible'] else 'Restricted / unknown'))]
            for plan in result['comparison']['plans']])
        add('Selected decision', ['Field', 'Value'], [
            ['Selected plan', decision.selected_plan or 'None selected'], ['Owner feedback', decision.feedback or 'Not provided'],
            ['Execution', 'Intention only; transactions and external agreements are not executed by acceptance.'],
        ])
        if decision.selected_snapshot:
            add('Selected actions (SIMULATED)', ['Change', 'Event', 'Amount', 'Date / shift'], [
                [a['kind'], a.get('event_id', ''), amount(a.get('amount')), a.get('date') or f"{a.get('days', 0)} days"]
                for a in decision.selected_snapshot.get('actions', [])])
        expected = decision.expected
        add('Expected simulated outcome', ['Measure', 'Value'], [
            ['Balance at review (SIMULATED)', amount(expected.get('balance_at_review'))],
            ['Minimum cash (SIMULATED)', amount(expected.get('minimum_balance'))],
            ['Remaining reserve gap (SIMULATED)', amount(expected.get('funding_gap'))],
        ])
        observed = decision.outcome
        if observed.get('status') == 'observed':
            add('Observed outcome', ['Measure', 'Value'], [
                ['Actual balance at review', amount(observed.get('actual_balance'))],
                ['Expected simulated balance', amount(observed.get('expected_balance'))],
                ['Actual minus expected', amount(observed.get('difference'))],
                ['Actual daily-net minimum', amount(observed.get('actual_minimum'))],
                ['Causation', observed.get('basis', 'Improvement cannot be causally attributed to the plan.')],
            ])
        else:
            add('Observed outcome', ['Availability', 'Reason'], [[observed.get('status', 'Not evaluated'), observed.get('reason', 'Sufficient paid records and review-date evidence are required.')]])
        notes = []
        for plan in result['comparison']['plans']:
            for note in plan['dependencies'] + plan['tradeoffs'] + plan['violations']:
                notes.append([plan['name'], note])
        add('Evidence and assumptions', ['Candidate', 'Dependency / trade-off / restriction'], notes)
        add('Limitations', ['Important qualification'], [[line] for line in state['limitations']] + [[result['comparison']['objective']]])
        if report_type == 'investigations':
            add('Technical evidence appendix', ['Source / identifier', 'Date / basis', 'Amount', 'Formula / description'], [
                [f"{node.get('source', node['kind'])} / {node['id']}", f"{node.get('date', '')} / {node.get('basis', '')}",
                 amount(node.get('amount')), node.get('formula') or node.get('label', '')]
                for node in result['evidence_graph']['nodes']])
    return sections


def render_pdf(business, start, end, metadata, sections):
    """Wrapped tables and paginated sections; no raw dictionary dumps."""
    import io
    from xml.sax.saxutils import escape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=36, bottomMargin=36,
                            title='FinPilot financial decision report', author='FinPilot AI')
    styles = getSampleStyleSheet()
    cell = ParagraphStyle('FinancialCell', parent=styles['BodyText'], fontSize=8, leading=11, spaceAfter=0, splitLongWords=True)

    def paragraph(value, header=False):
        text = f'{business.currency} {value:,.2f}' if isinstance(value, Decimal) else str(value if value is not None else 'Unknown')
        return Paragraph(escape(text), styles['Heading5'] if header else cell)

    story = [Paragraph('FinPilot | Financial decision report', styles['Title']),
             Paragraph(escape(business.name), styles['Heading2']),
             Paragraph(escape(f'Reporting period: {start} to {end} | Currency: {business.currency}'), styles['BodyText']), Spacer(1, 10)]
    for row in metadata[3:]:
        story.extend([paragraph(' | '.join(str(value) for value in row)), Spacer(1, 4)])
    for section in sections:
        headers, rows = section['headers'], section['rows']
        count = len(headers)
        data = [[paragraph(v, True) for v in headers]]
        for row in rows:
            padded = (list(row)+['']*count)[:count]
            data.append([paragraph(value) for value in padded])
        widths = [doc.width/count]*count
        if count == 6:
            widths = [doc.width*.25]+[doc.width*.15]*5
        table = LongTable(data, colWidths=widths, repeatRows=1, hAlign='LEFT', splitInRow=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E8EFFC')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6), ('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6), ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#AAB8D4')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#F6F8FB')]),
        ]))
        story.extend([KeepTogether([Spacer(1, 12), Paragraph(escape(section['title']), styles['Heading2'])]), table])

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(32, 18, 'Decision support | Estimates are not audited results or loan approval')
        canvas.drawRightString(A4[0]-32, 18, f'Page {doc.page}')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
