"""HTML email layouts — colors and structure match static/style.css (dashboard)."""

from __future__ import annotations

import html

from app.event_config import event_date, event_name, event_venue

# Mirror :root in static/style.css (inline for email clients)
THEME = {
    "sidebar": "#0f172a",
    "sidebar_text": "#cbd5e1",
    "bg": "#f1f5f9",
    "surface": "#ffffff",
    "border": "#e2e8f0",
    "text": "#0f172a",
    "muted": "#64748b",
    "primary": "#4f46e5",
    "primary_dark": "#4338ca",
    "primary_soft": "#eef2ff",
    "green": "#059669",
    "green_soft": "#ecfdf5",
    "green_text": "#047857",
    "amber_soft": "#fff7ed",
    "amber_text": "#c2410c",
    "radius": "12px",
    "shadow": "0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 24px rgba(15, 23, 42, 0.06)",
    "font": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
}


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _layout(
    *,
    preheader: str,
    eyebrow: str,
    badge: str,
    title: str,
    greeting_name: str,
    body_html: str,
    accent: str = "primary",
    footer_note: str = "",
) -> tuple[str, str]:
    T = THEME
    event = _esc(event_name())
    date = _esc(event_date())
    venue = _esc(event_venue())

    if accent == "green":
        badge_bg, badge_color = T["green_soft"], T["green_text"]
        accent_bar = T["green"]
    elif accent == "amber":
        badge_bg, badge_color = T["amber_soft"], T["amber_text"]
        accent_bar = T["primary"]
    else:
        badge_bg, badge_color = T["primary_soft"], T["primary_dark"]
        accent_bar = T["primary"]

    plain = (
        f"Hello {greeting_name},\n\n"
        f"{preheader}\n\n"
        f"Event: {event_name()}\nDate: {event_date()}\nVenue: {event_venue()}\n\n"
        f"{footer_note}\n\n— EventPilot AI"
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="color-scheme" content="light" />
  <title>{_esc(title)}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
</head>
<body style="margin:0;padding:0;background:{T['bg']};font-family:{T['font']};color:{T['text']};">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;">{_esc(preheader)}</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{T['bg']};padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;">
          <!-- Sidebar-style brand bar (matches website header) -->
          <tr>
            <td style="background:{T['sidebar']};border-radius:{T['radius']} {T['radius']} 0 0;padding:16px 20px;">
              <table role="presentation" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="padding-right:10px;vertical-align:middle;">
                    <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;font-weight:700;font-size:13px;line-height:36px;text-align:center;">EP</div>
                  </td>
                  <td style="vertical-align:middle;">
                    <div style="color:#ffffff;font-weight:700;font-size:15px;line-height:1.2;">EventPilot AI</div>
                    <div style="color:{T['sidebar_text']};font-size:12px;margin-top:2px;">Registration dashboard</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Main panel card -->
          <tr>
            <td style="background:{T['surface']};border:1px solid {T['border']};border-top:none;border-radius:0 0 {T['radius']} {T['radius']};box-shadow:{T['shadow']};overflow:hidden;">
              <div style="height:4px;background:{accent_bar};"></div>
              <div style="padding:24px 24px 8px;">
                <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:{T['muted']};margin-bottom:6px;">{_esc(eyebrow)}</div>
                <div style="display:inline-block;padding:4px 10px;border-radius:999px;background:{badge_bg};color:{badge_color};font-size:11px;font-weight:700;margin-bottom:10px;">{_esc(badge)}</div>
                <div style="font-size:22px;line-height:1.25;font-weight:700;letter-spacing:-0.02em;color:{T['text']};">{_esc(title)}</div>
              </div>
              <div style="padding:8px 24px 24px;">
                <p style="margin:0 0 14px;font-size:15px;line-height:1.6;color:{T['text']};">
                  Hi <strong>{_esc(greeting_name)}</strong>,
                </p>
                {body_html}
                <!-- Event details — stat-card style -->
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:20px 0 0;border:1px solid {T['border']};border-radius:{T['radius']};background:{T['surface']};">
                  <tr>
                    <td style="padding:14px 16px;">
                      <div style="font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:{T['muted']};margin-bottom:6px;">Event details</div>
                      <div style="font-size:15px;font-weight:700;color:{T['text']};">{event}</div>
                      <div style="font-size:13px;color:{T['muted']};margin-top:6px;line-height:1.5;">
                        <div>Date · {date}</div>
                        <div>Venue · {venue}</div>
                      </div>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 8px 0;text-align:center;font-size:12px;line-height:1.6;color:{T['muted']};">
              EventPilot AI · same experience as your organizer dashboard<br />
              {_esc(footer_note) if footer_note else "Transactional email — please keep for your records."}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
    return plain, html_doc


def _p(text: str) -> str:
    T = THEME
    return f'<p style="margin:0 0 12px;font-size:14px;line-height:1.65;color:{T["muted"]};">{text}</p>'


def _callout(text: str, *, accent: str = "primary") -> str:
    T = THEME
    if accent == "green":
        bg, border, color = T["green_soft"], T["green"], T["green_text"]
    else:
        bg, border, color = T["primary_soft"], T["primary"], T["primary_dark"]
    return f"""<div style="margin-top:4px;padding:12px 14px;border-left:4px solid {border};background:{bg};border-radius:8px;font-size:13px;line-height:1.55;color:{color};">{text}</div>"""


def confirmation_email(name: str) -> tuple[str, str, str]:
    subject = f"You're confirmed — {event_name()}"
    preheader = "Your registration is confirmed. Your event pass arrives in a separate email."
    T = THEME
    body = (
        _p(
            f'Great news — your registration is <strong style="color:{T["text"]};">confirmed</strong>. '
            "We're excited to have you join us."
        )
        + _p(
            "Next: two more emails — your <strong>event pass (PDF + QR)</strong> and, after the event, "
            "your <strong>certificate</strong>."
        )
        + _callout("Status badge on your dashboard: <strong>Confirmed</strong> (green)", accent="green")
    )
    plain, html_out = _layout(
        preheader=preheader,
        eyebrow="Registration dashboard",
        badge="Step 1 of 3 · Confirmation",
        title="Registration confirmed",
        greeting_name=name,
        body_html=body,
        accent="green",
        footer_note="Matches the Confirm action in your EventPilot dashboard.",
    )
    return subject, plain, html_out


def pass_email(name: str) -> tuple[str, str, str]:
    subject = f"Your event pass — {event_name()}"
    preheader = "Your QR pass is attached. Show it at check-in."
    T = THEME
    body = (
        _p(
            f'Your pass is <strong style="color:{T["text"]};">attached</strong> as '
            f'<span style="background:{T["bg"]};padding:2px 8px;border-radius:6px;font-family:ui-monospace,monospace;font-size:12px;">event-pass.pdf</span>.'
        )
        + _p("Present the <strong>QR code</strong> at the door — same flow as the <strong>/check-in</strong> page on the website.")
        + _callout("Tip: Print the PDF or open it on your phone before arrival.")
    )
    plain, html_out = _layout(
        preheader=preheader,
        eyebrow="Pass & check-in",
        badge="Step 2 of 3 · Event pass",
        title="Your pass is ready",
        greeting_name=name,
        body_html=body,
        accent="primary",
    )
    return subject, plain, html_out


def certificate_email(name: str) -> tuple[str, str, str]:
    subject = f"Your certificate — {event_name()}"
    preheader = "Congratulations! Your certificate of participation is attached."
    T = THEME
    body = (
        _p(
            f'Congratulations on participating in <strong style="color:{T["text"]};">{_esc(event_name())}</strong>!'
        )
        + _p(
            f'Certificate attached as '
            f'<span style="background:{T["bg"]};padding:2px 8px;border-radius:6px;font-family:ui-monospace,monospace;font-size:12px;">certificate.pdf</span>.'
        )
        + _callout("Thank you for attending — share your certificate on LinkedIn!", accent="green")
    )
    plain, html_out = _layout(
        preheader=preheader,
        eyebrow="Certificate delivery",
        badge="Step 3 of 3 · Certificate",
        title="Certificate of participation",
        greeting_name=name,
        body_html=body,
        accent="green",
    )
    return subject, plain, html_out
