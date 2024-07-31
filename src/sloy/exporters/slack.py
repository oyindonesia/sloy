import time
from datetime import datetime
from slack_sdk import WebClient

class Slack:
    def export(self, slo, data, supplied_config=None, **config):
        """Export data.
        Args:
            slo (dict): Result to send.
            data (dict): SLO config.
            config (dict): Exporter config.
        """
        client = WebClient(token=config["token"])

        slo_name = data["name"]
        slo_description = data["description"]

        mode = data["mode"]

        if mode == "alert":
            return
        elif mode == "data":
            time_window = data["time_window"]
            timestamp = int(time.time())

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"SLO generator Report - {slo_name}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*SLO Description:*\n{slo_description}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time Window:*\n{time_window}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Timestamp:*\n{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*SLO Method:*\n{slo["method"]}",
                        },
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*SLO Results:*",
                        }
                    ]
                }
            ]

        slo_result_fields = []

        for key, value in slo["result"].items():
            if isinstance(value, float):
                value = round(value, 4)
            slo_result_fields.append({
                "type": "mrkdwn",
                "text": f"*{key}:*\n{value}"
            })

        blocks.append({
            "type": "section",
            "fields": slo_result_fields
        })
        
        channel = supplied_config.get("channel") if supplied_config else config.get("channel")

        client.chat_postMessage(
            channel=channel,
            blocks=blocks
        )
