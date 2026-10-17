import io
from datetime import timedelta
from decimal import Decimal
import openpyxl
from pypdf import PdfReader
from django.urls import reverse
from django.utils import timezone
from apps.portal.intelligence.investigation import run_investigation
from apps.portal.intelligence.decision_memory import decide


def test_professional_pdf_and_typed_spreadsheets(client, owner, business, entry):
    entry(kind='payable', status='pending', amount=1500, due_date=timezone.localdate()+timedelta(days=3))
    item = run_investigation(owner, business.pk, '=Untrusted question <script>never run</script>')
    decision = decide(owner, business.pk, item.decision.pk, 'accepted', item.result['recommended'])
    client.force_login(owner)
    url = reverse('reports', args=[business.pk])
    pdf = client.get(url, {'type':'investigations', 'format':'pdf'})
    assert pdf.status_code == 200
    reader = PdfReader(io.BytesIO(pdf.content))
    text = '\n'.join(page.extract_text() for page in reader.pages)
    for title in ['Executive summary', 'Decision and investigation summary', 'Original financial state',
                  'Alternative comparison', 'Selected decision', 'Expected simulated outcome', 'Observed outcome',
                  'Evidence and assumptions', 'Limitations', 'Technical evidence appendix']:
        assert title in text
    assert "'timeline':" not in text and "'events':" not in text and "'balance_at_review':" not in text
    assert 'USD 1,000.00' in text
    assert 'Page 1' in text
    workbook = client.get(url, {'type':'investigations', 'format':'xlsx'})
    sheet = openpyxl.load_workbook(io.BytesIO(workbook.content)).active
    cells = [c for row in sheet for c in row]
    assert any(c.value == 1000 and c.data_type == 'n' for c in cells)
    assert any(str(c.value).startswith("'=Untrusted") for c in cells)
    assert all(c.data_type != 'f' for c in cells)
    csv = client.get(url, {'type':'investigations', 'format':'csv'}).content.decode()
    assert "'=Untrusted" in csv and decision.selected_plan in csv
    assert Decimal(item.snapshot['known_cash']) == 1000
