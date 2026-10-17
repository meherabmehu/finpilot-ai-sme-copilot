import io
from datetime import timedelta
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from apps.portal.imports import preview_import, confirm_import
from apps.portal.models import Alert


def csv_file(rows):
    return SimpleUploadedFile(
        "records.csv", ("date,description,amount,kind,currency,status,category\n" + rows).encode(), content_type="text/csv"
    )


def test_import_preview_confirmation_and_idempotency(business, owner):
    day = timezone.localdate().isoformat()
    item = preview_import(business, csv_file(f"{day},Customer payment,125.20,income,USD,paid,Sales"))
    assert not item.errors
    assert not business.transactions.exists()
    assert confirm_import(business, owner, item.pk) == 1
    assert confirm_import(business, owner, item.pk) == 0
    assert business.transactions.count() == 1


def test_import_rejects_mixed_currency_and_missing_status(business, owner):
    day = timezone.localdate().isoformat()
    item = preview_import(business, csv_file(f"{day},Invalid,125,income,EUR,,Sales"))
    assert item.errors
    with pytest.raises(ValidationError):
        confirm_import(business, owner, item.pk)
    assert not business.transactions.exists()


def test_xlsx_formula_rejected(business):
    from openpyxl import Workbook

    book = Workbook()
    book.active.append(["date", "description", "amount"])
    book.active.append(["2026-01-01", '=HYPERLINK("bad")', 5])
    output = io.BytesIO()
    book.save(output)
    with pytest.raises(ValidationError):
        preview_import(business, SimpleUploadedFile("bad.xlsx", output.getvalue()))


def test_bad_and_oversized_uploads(business):
    for file in [
        SimpleUploadedFile("bad.exe", b"MZ"),
        SimpleUploadedFile("bad.csv", b"\x00bad"),
        SimpleUploadedFile("huge.csv", b"x" * (5 * 1024 * 1024 + 1)),
    ]:
        with pytest.raises(ValidationError):
            preview_import(business, file)


@pytest.mark.parametrize("format,mime", [("csv", "text/csv"), ("xlsx", "application/vnd.openxmlformats"), ("pdf", "application/pdf")])
def test_exports(client, owner, business, entry, format, mime):
    entry(description="=malicious()")
    client.force_login(owner)
    response = client.get(reverse("reports", args=[business.pk]) + f"?format={format}&type=transactions")
    assert response.status_code == 200
    assert response["Content-Type"].startswith(mime)
    assert response["Content-Disposition"].endswith(f'.{format}"')
    if format == "csv":
        assert b"'=malicious()" in response.content


@pytest.mark.parametrize("url", ["/", "/login/", "/signup/", "/password-reset/", "/info/privacy/", "/info/terms/"])
def test_public_pages(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize(
    "route,suffix",
    [
        ("dashboard", ""),
        ("my_business", ""),
        ("my_business", "?tab=transactions"),
        ("my_business", "?tab=upload"),
        ("my_business", "?tab=sales"),
        ("my_business", "?tab=expenses"),
        ("planning", ""),
        ("planning", "?tab=scenarios"),
        ("planning", "?tab=loans"),
        ("advisor", ""),
        ("reports", ""),
    ],
)
def test_portal_pages_render(client, owner, business, entry, route, suffix):
    entry()
    client.force_login(owner)
    assert client.get(reverse(route, args=[business.pk]) + suffix).status_code == 200


def test_registration_verification_and_login(client, db):
    from django.contrib.auth.models import User
    from django.test import override_settings
    from django.core import signing

    with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
        response = client.post(
            "/signup/",
            {
                "full_name": "Taylor",
                "email": "taylor@example.com",
                "password1": "Safe-registration-8721!",
                "password2": "Safe-registration-8721!",
                "terms": "on",
            },
        )
        assert response.status_code == 200
        user = User.objects.get(username="taylor@example.com")
        assert not user.is_active
        assert len(mail.outbox) == 1
        token = signing.dumps({"id": user.pk}, salt="verify-email")
        assert client.post(reverse("verify", args=[token])).status_code == 302
        user.refresh_from_db()
        assert user.is_active
        assert client.post("/logout/").status_code == 302
        assert client.post("/login/", {"username": user.email, "password": "Safe-registration-8721!"}).status_code == 302


def test_monitoring_does_not_duplicate_alerts(business, entry):
    from django.core.management import call_command

    entry(kind="receivable", status="pending", due_date=timezone.localdate() - timedelta(days=1))
    call_command("monitor_finances")
    count = Alert.objects.count()
    call_command("monitor_finances")
    assert Alert.objects.count() == count
    assert Alert.objects.get(code="overdue_receivables").active
