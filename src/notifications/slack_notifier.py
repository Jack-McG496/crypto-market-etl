import requests
from src.config.settings import SLACK_TIMEOUT, SLACK_WEBHOOK_URL
from src.utils.logger import get_logger

logger = get_logger(__name__)

def send_slack_alert(alert) -> bool:

    webhook = SLACK_WEBHOOK_URL

    if not webhook:
        logger.warning("Slack webhook not configured")
        return False

    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Crypto Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Coin:*\n{alert['coin_id']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{alert['severity']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{alert['alert_type']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{alert['analytics_timestamp']}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert["message"]
                }
            }
        ]
    }

    try:

        response = requests.post(
            webhook,
            json=payload,
            timeout=SLACK_TIMEOUT
        )

        response.raise_for_status()

        logger.info("Slack notification sent")

        return True

    except Exception:
        logger.exception("Failed sending Slack notification")
        return False