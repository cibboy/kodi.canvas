def get_formatted_timespan(timespan, include_seconds=False):
	if include_seconds:
		if timespan >= 3600:
			hours = math.floor(timespan / 3600)
			minutes = math.floor((timespan - (hours * 3600)) / 60)
			seconds = math.floor(timespan - (hours * 3600) - (minutes * 60))
			timespan = f"{hours}h{minutes:0>2}m{seconds:0>2}s"
		elif timespan > 60:
			minutes = math.floor(timespan / 60)
			seconds = math.floor(timespan - (minutes * 60))
			timespan = f"{minutes}m{seconds:0>2}s"
		else:
			timespan = f"{timespan}s"
	else:
		if timespan >= 3600:
			hours = math.floor(timespan / 3600)
			minutes = math.floor((timespan - (hours * 3600)) / 60)
			timespan = f"{hours}h{minutes}m"
		else:
			timespan = f"{math.floor(timespan / 60)}m"