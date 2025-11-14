import math
import json
import xbmc
from urllib.parse import urlparse, parse_qsl

# Calls a JSON-RPC method agains Kodi.
def call_rpc(method, params=None):
    payload = {
        'jsonrpc': '2.0',
        'method': method,
        'id': 1,
        'params': params or {}
    }
    r = xbmc.executeJSONRPC(json.dumps(payload))
    return json.loads(r).get('result', {})

# Formats a timespan according to the requested format.
def format_timespan(timespan, format=''):
	# Compute hours, minuts, seconds.
	hours = math.floor(timespan / 3600)
	minutes = math.floor((timespan - (hours * 3600)) / 60)
	seconds = math.floor(timespan - (hours * 3600) - (minutes * 60))

	# Replace format placeholders with actual (posibly padded) values.
	result = format
	result = result.replace('[HH]', f"{hours:0>2}")
	result = result.replace('[H]', f"{hours}")
	result = result.replace('[mm]', f"{minutes:0>2}")
	result = result.replace('[m]', f"{minutes}")
	result = result.replace('[ss]', f"{seconds:0>2}")
	result = result.replace('[s]', f"{seconds}")

	return result
