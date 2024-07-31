import copy
import json
from datetime import datetime, timezone
from elasticsearch import Elasticsearch


class ElasticsearchBackend:
    """Backend for querying metrics from ElasticSearch.
    Args:
        client (elasticsearch.ElasticSearch): Existing ES client.
        es_config (dict): ES client configuration.
    """

    def __init__(self, client=None, **es_config):
        self.client = client
        if self.client is None:
            conf = copy.deepcopy(es_config)
            url = conf.pop("url", None)
            basic_auth = conf.pop("basic_auth", None)
            api_key = conf.pop("api_key", None)
            if url:
                conf["hosts"] = url
                if "https" not in conf["hosts"]:
                    conf["verify_certs"] = False
            if basic_auth:
                conf["basic_auth"] = (basic_auth["username"], basic_auth["password"])
            if api_key:
                conf["api_key"] = (api_key["id"], api_key["value"])
            self.client = Elasticsearch(**conf)
    
    def compute(self, timestamp, window, slo_config):
        method = slo_config["method"]
        if method == "error_rate":
            return self.error_rate(timestamp, window, slo_config)
        elif method == "percentile":
            return self.percentile(timestamp, window, slo_config)
    
    def error_rate(self, timestamp, window, slo_config):
        time_end = timestamp
        time_start = timestamp - window
        time_end = datetime.fromtimestamp(time_end).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        time_start = datetime.fromtimestamp(time_start).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        query_bad = slo_config["service_level_indicator"]["query_bad"]
        query_good = slo_config["service_level_indicator"]["query_good"]
        # Convert query from string to dict if needed
        if isinstance(query_bad, str):
            query_bad = json.loads(query_bad)
            query_good = json.loads(query_good)

        es_index = slo_config["service_level_indicator"]["es_index"]

        # add filter time range by appending to "filter" array
        range_dict = {
            "range": {
                "@timestamp": {
                    "gte": time_start,
                    "lte": time_end
                }
            }
        }
        query_bad["query"]["bool"]["filter"].append(range_dict)
        query_good["query"]["bool"]["filter"].append(range_dict)
        
        count_bad = self.client.count(index=es_index, body=query_bad, request_timeout=60)
        count_good = self.client.count(index=es_index, body=query_good, request_timeout=60)

        return {
            "method": "error_rate",
            "result": {
                "good": count_good["count"],
                "bad": count_bad["count"],
                "total": count_good["count"] + count_bad["count"],
                "error_rate": count_bad["count"] / (count_good["count"] + count_bad["count"])
            }
        }
    
    def percentile(self, timestamp, window, slo_config):
        time_end = timestamp
        time_start = timestamp - window
        time_end = datetime.fromtimestamp(time_end).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        time_start = datetime.fromtimestamp(time_start).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        query = slo_config["service_level_indicator"]["query"]
        # Convert query from string to dict if needed
        if isinstance(query, str):
            query = json.loads(query)

        percentiles = slo_config["service_level_indicator"]["percentiles"]
        if not percentiles:
            percentiles = [90.0, 95.0, 99.0]

        value_key = slo_config["service_level_indicator"]["value_key"]
        es_index = slo_config["service_level_indicator"]["es_index"]

        timerange_dict = {
            "range": {
                "@timestamp": {
                    "gte": time_start,
                    "lte": time_end
                }
            }
        }
        query["query"]["bool"]["filter"].append(timerange_dict)
        query["aggs"] = {
            "load_time_outlier": {
                "percentiles": {
                    "field": value_key,
                    "percents": percentiles
                }
            }
        }
        res = self.client.search(index=es_index, body=query, request_timeout=90)
        res = res["aggregations"]["load_time_outlier"]["values"]
        res["percentiles"] = percentiles
        
        return {
            "method": "percentile",
            "result": res
        }
