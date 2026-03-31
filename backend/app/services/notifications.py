import httpx
import asyncio
from app.config import settings
from app.database import log_event
from app.models.alert import ThreatAlert, Severity

class NotificationService:
    """
    Dispatches high-priority security alerts to external channels.
    Supports: Telegram, Slack.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def send_alert(self, alert: ThreatAlert):
        """
        Main entry point for sending a threat alert to all active channels.
        Only sends for CRITICAL or HIGH severity by default.
        """
        if alert.risk.severity not in [Severity.CRITICAL, Severity.HIGH]:
            return

        # 🚀 Multi-Channel Dispatch
        tasks = [
            self.send_telegram(alert),
            self.send_slack(alert)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def send_telegram(self, alert: ThreatAlert):
        """Dispatches an alert to a Telegram Chat."""
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not token or not chat_id:
            # 🛠️ MOCK MODE (For Demo/Dev)
            log_event("MOCK_NOTIFY", "Telegram", f"Critical Alert from {alert.packet.src_ip} would be sent to Telegram.")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # 📝 Format professional security message
        emoji = "🚨" if alert.risk.severity == Severity.CRITICAL else "⚠️"
        message = (
            f"{emoji} *StealthVault AI - THREAT DETECTED*\n\n"
            f"*Severity:* {alert.risk.severity.upper()}\n"
            f"*Attack:* {alert.classification.attack_type.value}\n"
            f"*Risk Score:* {alert.risk.score:.2%}\n"
            f"*Source:* `{alert.packet.src_ip}`\n"
            f"*Location:* {alert.geo_location.city}, {alert.geo_location.country}\n\n"
            f"*AI Analysis:* {alert.brain_analysis.description if alert.brain_analysis else 'Analyzing...'}\n\n"
            f"🔗 [View in Dashboard](https://stealthvault-ai.onrender.com/dashboard)"
        )

        try:
            resp = await self.client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            })
            if resp.status_code != 200:
                log_event("ERROR", "Telegram", f"Failed to send alert: {resp.text}")
        except Exception as e:
            log_event("ERROR", "Telegram", f"Connection error: {e}")

    async def send_slack(self, alert: ThreatAlert):
        """Dispatches an alert to a Slack Webhook."""
        webhook_url = settings.SLACK_WEBHOOK_URL

        if not webhook_url:
            # 🛠️ MOCK MODE (For Demo/Dev)
            log_event("MOCK_NOTIFY", "Slack", f"High Alert from {alert.packet.src_ip} would be sent to Slack.")
            return

        # 📝 Slack Block Kit formatting
        color = "#ef4444" if alert.risk.severity == Severity.CRITICAL else "#f97316"
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🛡️ StealthVault AI - {alert.risk.severity.upper()} THREAT",
                    "fields": [
                        {"title": "Attack Type", "value": alert.classification.attack_type.value, "short": True},
                        {"title": "Risk Score", "value": f"{alert.risk.score:.2%}", "short": True},
                        {"title": "Source IP", "value": str(alert.packet.src_ip), "short": True},
                        {"title": "Geo Origin", "value": f"{alert.geo_location.city}, {alert.geo_location.country}", "short": True}
                    ],
                    "footer": "StealthVault AI SOC Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }

        try:
            resp = await self.client.post(webhook_url, json=payload)
            if resp.status_code != 200:
                log_event("ERROR", "Slack", f"Failed to send alert: {resp.text}")
        except Exception as e:
            log_event("ERROR", "Slack", f"Connection error: {e}")

# Singleton
notification_service = NotificationService()
