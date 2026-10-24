from app.email_templates import certificate_email, confirmation_email, pass_email


def test_confirmation_html_contains_branding():
    subject, plain, html = confirmation_email("Alex")
    assert "Alex" in plain
    assert "Registration confirmed" in html
    assert "Step 1 of 3" in html
    assert "<!DOCTYPE html>" in html
    assert "#0f172a" in html  # sidebar theme
    assert "EP</div>" in html
    assert subject


def test_pass_and_certificate_html():
    _, _, pass_html = pass_email("Sam")
    assert "event-pass.pdf" in pass_html
    _, _, cert_html = certificate_email("Sam")
    assert "certificate.pdf" in cert_html
