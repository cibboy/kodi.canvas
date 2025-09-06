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

# Extract additional information from DB path.
def get_params_from_dbpath(dbpath):
	# Take only the part from ?info= on.
	info = dbpath[(dbpath.find('?info=') + 6):]
	# Replace :: with & to rebuild a valid url query.
	info = info.replace('::', '&')

	# Parse fake url.
	parsed = urlparse(f"?{info}")

	# Extract query parameters into a dictionary.
	params = {'type': None}
	if parsed.query is not None and parsed.query != '':
		params = dict(parse_qsl(parsed.query[0:]))

	return params

# Formats a timespan in hours, minutes and (optionally) seconds based on its duration.
def get_formatted_timespan(timespan, include_seconds=False):
	if include_seconds:
		if timespan >= 3600:
			hours = math.floor(timespan / 3600)
			minutes = math.floor((timespan - (hours * 3600)) / 60)
			seconds = math.floor(timespan - (hours * 3600) - (minutes * 60))
			if seconds == 0 and minutes == 0:
				return f"{hours}h"
			elif seconds == 0:
				return f"{hours}h{minutes}m"
			else:
				return f"{hours}h{minutes:0>2}m{seconds}s"
		elif timespan > 60:
			minutes = math.floor(timespan / 60)
			seconds = math.floor(timespan - (minutes * 60))
			if seconds == 0:
				return f"{minutes}m"
			else:
				return f"{minutes}m{seconds}s"
		else:
			return f"{timespan}s"
	else:
		if timespan >= 3600:
			hours = math.floor(timespan / 3600)
			minutes = math.floor((timespan - (hours * 3600)) / 60)
			if minutes == 0:
				return f"{hours}h"
			else:
				return f"{hours}h{minutes}m"
		else:
			return f"{math.floor(timespan / 60)}m"

# Converts an integer representing audio channels to its dot-notation.
def get_formatted_audiochannels(channels):
	if channels == 1: return '1.0'
	elif channels == 2: return '2.0'
	elif channels == 3: return '2.1'
	elif channels == 4: return '4.0'
	elif channels == 5: return '4.1'
	elif channels == 6: return '5.1'
	elif channels == 7: return '6.1'
	elif channels == 8: return '7.1'
	elif channels == 9: return '8.1'
	elif channels == 10: return '9.1'
	else: return ''
