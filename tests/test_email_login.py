from django.urls import reverse


def test_login_labels_email_and_accepts_normalized_address(client, owner):
    page = client.get(reverse("login"))
    assert b"Email address" in page.content
    assert b'type="email"' in page.content
    response = client.post(reverse("login"), {"username": "OWNER@EXAMPLE.COM", "password": "Strong-test-password-982"})
    assert response.status_code == 302
    assert int(client.session["_auth_user_id"]) == owner.pk


def test_login_errors_do_not_reveal_account_presence(client, owner):
    for email in ("owner@example.com", "not-registered@example.com"):
        response = client.post(reverse("login"), {"username": email, "password": "wrong-password"})
        assert response.status_code == 200
        assert b"The email address or password is incorrect." in response.content
        assert "_auth_user_id" not in client.session
