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

# Converts a single-number audio channel definition into a dot-notation one.
def format_audio_channels(value):
	value = str(value)
	if value == '1': return '1.0'
	elif value == '2': return '2.0'
	elif value == '3': return '2.1'
	elif value == '4': return '4.0'
	elif value == '5': return '4.1'
	elif value == '6': return '5.1'
	elif value == '7': return '6.1'
	elif value == '8': return '7.1'
	elif value == '9': return '8.1'
	elif value == '10': return '9.1'
	else: return value