import copy
import json
import base64
import numpy as np
from datetime import datetime, timezone
from google.cloud.logging import Client
from google.oauth2 import service_account

class CloudloggingBackend:
    """Backend for querying metrics from Google Cloud Logging.
    Args:
        client (google.cloud.logging.Client): Existing gcl client.
        gcl_config (dict): gcl client configuration.
    """

    def __init__(self, client=None, **gcl_config):
        self.client = client
        if self.client is None:
            conf = copy.deepcopy(gcl_config)
            credentials = conf.pop("credentials", None)
            credentials = json.loads(base64.b64decode(credentials).decode('utf-8'))
            credentials = service_account.Credentials.from_service_account_info(credentials)    
            project_id = conf.pop("project_id", None)
            self.client = Client(project=project_id, credentials=credentials)
    
    def compute(self, timestamp, window, slo_config):
        method = slo_config["method"]
        if method == "error_rate":
            return self.error_rate(timestamp, window, slo_config)
        elif method == "percentile":
            return self.percentile(timestamp, window, slo_config)
    
    def query(self, timestamp, window, filter_str):
        time_start = timestamp - window
        time_start = datetime.fromtimestamp(time_start).astimezone(timezone.utc)
        time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        timestamp_str = f' AND timestamp>="{time_start.strftime(time_format)}"'
        filter_str += timestamp_str

        return self.client.list_entries(filter_=filter_str, page_size=1000)
    
    def count(self, events):
        count = 0
        for _ in events:
            count += 1
        return count
    
    def error_rate(self, timestamp, window, slo_config):
        measurement = slo_config["service_level_indicator"]
        filter_good = measurement["filter_good"]
        filter_bad = measurement["filter_bad"]

        good_events = self.query(
            timestamp=timestamp,
            window=window,
            filter_str=filter_good,
        )
        count_good = self.count(good_events)

        bad_events = self.query(
            timestamp=timestamp,
            window=window,
            filter_str=filter_bad,
        )
        count_bad = self.count(bad_events)

        return {
            "method": "error_rate",
            "result": {
                "good": count_good,
                "bad": count_bad,
                "total": count_good + count_bad,
                "error_rate": count_bad / (count_good + count_bad)
            }
        }
    
    def percentile(self, timestamp, window, slo_config):
        query = slo_config["service_level_indicator"]["query"]
        value_key = slo_config["service_level_indicator"]["value_key"]
        percentiles = slo_config["service_level_indicator"]["percentiles"]
        if not percentiles:
            percentiles = [90.0, 95.0, 99.0]

        events = self.query(
            timestamp=timestamp,
            window=window,
            filter_str=query,
        )

        entries = []
        for entry in events:
            duration = entry.http_request[value_key]
            duration = float(duration[:-1])
            if duration is not None:
                entries.append(duration)

        res = {}
        for percentile in percentiles:
            res[str(percentile)] = np.percentile(entries, percentile).item()

        res["percentiles"] = percentiles
        
        return {
            "method": "percentile",
            "result": res
        }
