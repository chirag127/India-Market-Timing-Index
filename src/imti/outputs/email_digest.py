"""Email digest sender via SendGrid.

Sends hourly email digests with the current IMTI score,
zone, action, and key indicators. Also sends signal-change
alerts when the score crosses zone boundaries.
"""

from __future__ import annotations

from typing import Any

from imti.config.settings import get_settings
from imti.core.enums import ScoreZone
from imti.core.logger import get_logger
from imti.core.types import IndexScore, Snapshot

logger = get_logger("outputs.email")


def send_hourly_digest(
    score: IndexScore,
    snapshot: Snapshot,
    audit_report: dict[str, Any],
) -> bool:
    """Send the hourly email digest.

    Returns True if email was sent successfully.
    """
    settings = get_settings()

    if not settings.email_is_configured:
        logger.warning("Email not configured — skipping digest")
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        # Build email content
        zone = score.score_zone
        subject = f"IMTI Update: {score.score:.1f} — {zone.value.replace('_', ' ').title()} {zone.emoji}"

        html_content = _build_email_html(score, snapshot, audit_report)

        message = Mail(
            from_email=Email(settings.email_from, "IMTI System"),
            to_emails=To(settings.email_to),
            subject=subject,
            html_content=Content("text/html", html_content),
        )

        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.client.mail.send.post(request_body=message.get())

        if response.status_code in (200, 201, 202):
            logger.info(f"Email digest sent: {subject}")
            return True
        else:
            logger.warning(f"Email send failed: status={response.status_code}")
            return False

    except ImportError:
        logger.warning("sendgrid package not installed — skipping email")
        return False
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def _build_email_html(
    score: IndexScore,
    snapshot: Snapshot,
    audit_report: dict[str, Any],
) -> str:
    """Build the HTML email content."""
    zone = score.score_zone

    # Key indicator values
    indicator_lines = []
    for name, iv in snapshot.indicators.items():
        if iv.value is not None:
            indicator_lines.append(f"<tr><td>{name}</td><td>{iv.value:.2f}</td></tr>")

    indicators_table = "".join(indicator_lines[:20])  # Top 20

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: {zone.color};">
            IMTI Score: {score.score:.1f} — {zone.value.replace('_', ' ').title()}
        </h1>
        <p style="font-size: 18px;">
            {zone.emoji} <strong>Action: {score.signal_action.value}</strong>
            <br>Exposure: {score.exposure_suggestion:.0%}
            <br>Confidence: {score.confidence:.0%}
        </p>
        <h2>Key Indicators</h2>
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background: #f0f0f0;"><th>Indicator</th><th>Value</th></tr>
            {indicators_table}
        </table>
        <p style="font-size: 12px; color: #888;">
            Timestamp: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')} IST
            <br>Market: {snapshot.market_status.value}
            <br>Sources: {audit_report.get('success_count', '?')}/{audit_report.get('total_sources', '?')} OK
        </p>
    </body>
    </html>
    """
