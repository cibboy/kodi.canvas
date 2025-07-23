import math

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