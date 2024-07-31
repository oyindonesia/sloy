import gspread
import json
import base64
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

class Gsheets:
    def export(self, slo, data, supplied_config, **config):
        """Export data.
        Args:
            slo (dict): Result to send.
            data (dict): SLO config.
            config (dict): Exporter config.
        """

        # Set up the credentials
        service_account = config["credentials"]
        service_account = json.loads(base64.b64decode(service_account).decode('utf-8'))
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account, scope)
        client = gspread.authorize(creds)

        # Get the sheet using sheet id and worksheet name
        sheet_id = supplied_config.get("sheet_id") if supplied_config else config.get("sheet_id")
        worksheet_name = supplied_config.get("worksheet_name") if supplied_config else config.get("worksheet_name")
            
        sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)

        values = []
        time_window = data["time_window"]
        timestamp = int(time.time())

        values.append(f"{data["name"]}")
        values.append(f"{time_window}")
        values.append(f"{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        values.append(f"{slo['method']}")

        for key, value in slo["result"].items():
            values.append(f"{key}: {value}")

        # Export the data
        sheet.append_row(values)
