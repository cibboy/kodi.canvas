import math
import json
import xbmc
import xbmcgui
from image import get_blurred, get_cropped_clearlogo

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

# Build a listitem for movies.
def get_movie_listitem(movie):
    # Create movie-type listitem.
    li = xbmcgui.ListItem(label=movie['title'])
    li.setProperty('ItemType', 'movie')

    # Set internal properties.
    li.setArt(movie['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setTitle(movie['title'])
    videoinfo.setYear(movie['year'])
    videoinfo.setStudios(movie['studio'])
    videoinfo.setPlot(movie['plot'])
    videoinfo.setGenres(movie['genre'])
    videoinfo.setDuration(movie['streamdetails']['video'][0]['duration'])
    videoinfo.setResumePoint(movie['resume']['position'], movie['resume']['total'])
    videoinfo.setPlaycount(movie['playcount'])
    for video in movie['streamdetails']['video']:
        stream = xbmc.VideoStreamDetail(
            video.get('width', 0),
            video.get('height', 0),
            video.get('aspect', 0.0),
            video.get('duration', 0),
            video.get('codec', ''),
            video.get('stereomode', ''),
            video.get('language', ''),
            video.get('hdrtype', '')
        )
        videoinfo.addVideoStream(stream)
    for audio in movie['streamdetails']['audio']:
        stream = xbmc.AudioStreamDetail(
            audio.get('channels', 0),
            audio.get('codec', ''),
            audio.get('language', '')
        )
        videoinfo.addAudioStream(stream)
    for sub in movie['streamdetails']['subtitle']:
        stream = xbmc.SubtitleStreamDetail(sub.get('language', ''))
        videoinfo.addSubtitleStream(stream)

    # Get custom art.
    blur, color = get_blurred(movie['art'].get('fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(movie['art'].get('clearlogo', ''))

    # Compute duration visual string.
    duration = get_formatted_timespan(movie['streamdetails']['video'][0]['duration'])

    # Get number of audio channels.
    channels = get_formatted_audiochannels(movie['streamdetails']['audio'][0].get('channels', 0))

    # Compute watched stats.
    time_remaining = ''
    watched_percentage = 0
    if movie['resume']['position'] > 0 and movie['resume']['position'] < movie['resume']['total'] and movie['playcount'] == 0:
        time_remaining = get_formatted_timespan(movie['resume']['total'] - movie['resume']['position'])
        watched_percentage = round(movie['resume']['position'] * 100 / movie['resume']['total'])

    # Remove "Rated" from rating.
    rating = movie['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setProperty('AudioChannels', str(channels))
    li.setProperty('DurationString', duration)
    li.setProperty('TimeRemainingString', time_remaining)
    li.setProperty('WatchedPercentage', str(watched_percentage))
    li.setProperty('BlurArt', blur)
    li.setProperty('BlurArt.TextColor', color)
    li.setProperty('Clearlogo.Big', clearlogo)

    return li

# Build a listitem for TV shows.
def get_tvshow_listitem(tvshow):
    # Create tvshow-type listitem.
    li = xbmcgui.ListItem(label=tvshow['title'])
    li.setProperty('ItemType', 'tvshow')

    # Set internal properties.
    li.setArt(tvshow['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setTitle(tvshow['title'])
    videoinfo.setYear(tvshow['year'])
    videoinfo.setStudios(tvshow['studio'])
    videoinfo.setPlot(tvshow['plot'])
    videoinfo.setGenres(tvshow['genre'])
    videoinfo.setEpisode(tvshow['episode'])
    videoinfo.setSeason(tvshow['season'])
    #videoinfo.setTvShowStatus(tvshow['status'])
    videoinfo.setPlaycount(tvshow['playcount'])

    # Get custom art.
    blur, color = get_blurred(tvshow['art'].get('fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(tvshow['art'].get('clearlogo', ''), True)

    # Compute watched stats.
    watched_percentage = 0
    unwatched = 0
    if tvshow['episode'] > 0:
        watched_percentage = round(tvshow['watchedepisodes'] * 100 / tvshow['episode'])
        unwatched = tvshow['episode'] - tvshow['watchedepisodes']

    # Remove "Rated" from rating.
    rating = tvshow['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setProperty('TotalEpisodes', str(tvshow['episode']))
    li.setProperty('TotalSeasons', str(tvshow['season']))
    li.setProperty('WatchedEpisodes', str(tvshow['watchedepisodes']))
    li.setProperty('UnWatchedEpisodes', str(unwatched))
    li.setProperty('WatchedPercentage', str(watched_percentage))
    li.setProperty('BlurArt', blur)
    li.setProperty('BlurArt.TextColor', color)
    li.setProperty('Clearlogo.Big', clearlogo)
    li.setProperty('Clearlogo.Small', clearlogo_small)

    return li

# Build a listitem for seasons.
def get_season_listitem(season):
    # Create season-type listitem.
    li = xbmcgui.ListItem(label=season['title'])
    li.setProperty('ItemType', 'season')

    # Set internal properties.
    li.setArt(season['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setTitle(season['title'])
    videoinfo.setSeason(season['season'])
    videoinfo.setEpisode(season['episode'])
    videoinfo.setStudios(season.get('tvshow', {'studio': None})['studio'])
    videoinfo.setPlot(season.get('tvshow', {'plot': None})['plot'])
    videoinfo.setTvShowTitle(season['showtitle'])
    videoinfo.setPlaycount(season['playcount'])

    # Get custom art.
    tvshow_blur, tvshow_color = get_blurred(season.get('tvshow', {'art': {}})['art'].get('fanart', ''))
    season_blur, season_color = get_blurred(season['art'].get('fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(season.get('tvshow', {'art': {}})['art'].get('clearlogo', ''), True)

    # Compute watched stats.
    watched_percentage = 0
    unwatched = 0
    if season['episode'] > 0:
        watched_percentage = round(season['watchedepisodes'] * 100 / season['episode'])
        unwatched = season['episode'] - season['watchedepisodes']

    # Remove "Rated" from rating.
    rating = season.get('tvshow', {'mpaa': None})['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setArt({'tvshow.fanart': season.get('tvshow', {'art': {}})['art'].get('fanart', '')})
    li.setProperty('TotalEpisodes', str(season['episode']))
    li.setProperty('WatchedEpisodes', str(season['watchedepisodes']))
    li.setProperty('UnWatchedEpisodes', str(unwatched))
    li.setProperty('WatchedPercentage', str(watched_percentage))
    li.setProperty('BlurArt.TvShow', tvshow_blur)
    li.setProperty('BlurArt.Season', season_blur)
    li.setProperty('BlurArt.TvShow.TextColor', tvshow_color)
    li.setProperty('BlurArt.Season.TextColor',season_color)
    li.setProperty('Clearlogo.Big', clearlogo)
    li.setProperty('Clearlogo.Small', clearlogo_small)

    return li

# Build a listitem for episodes.
def get_episode_listitem(episode):
    # Create episode-type listitem.
    li = xbmcgui.ListItem(label=episode['title'])
    li.setProperty('ItemType', 'episode')

    # Set internal properties.
    li.setArt(episode['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setTitle(episode['title'])
    videoinfo.setSeason(episode['season'])
    videoinfo.setEpisode(episode['episode'])
    videoinfo.setPremiered(episode['firstaired'])
    videoinfo.setStudios(episode['studio'])
    videoinfo.setPlot(episode['plot'])
    videoinfo.setTvShowTitle(episode['showtitle'])
    videoinfo.setDuration(episode['streamdetails']['video'][0]['duration'])
    videoinfo.setResumePoint(episode['resume']['position'], episode['resume']['total'])
    videoinfo.setPlaycount(episode['playcount'])
    for video in episode['streamdetails']['video']:
        stream = xbmc.VideoStreamDetail(
            video.get('width', 0),
            video.get('height', 0),
            video.get('aspect', 0.0),
            video.get('duration', 0),
            video.get('codec', ''),
            video.get('stereomode', ''),
            video.get('language', ''),
            video.get('hdrtype', '')
        )
        videoinfo.addVideoStream(stream)
    for audio in episode['streamdetails']['audio']:
        stream = xbmc.AudioStreamDetail(
            audio.get('channels', 0),
            audio.get('codec', ''),
            audio.get('language', '')
        )
        videoinfo.addAudioStream(stream)
    for sub in episode['streamdetails']['subtitle']:
        stream = xbmc.SubtitleStreamDetail(sub.get('language', ''))
        videoinfo.addSubtitleStream(stream)

    # Get custom art.
    tvshow_blur, tvshow_color = get_blurred(episode['art'].get('tvshow.fanart', ''))
    season_blur, season_color = get_blurred(episode['art'].get('season.fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(episode['art'].get('tvshow.clearlogo', ''), True)

    # Compute duration visual string.
    duration = get_formatted_timespan(episode['streamdetails']['video'][0]['duration'])

    # Get number of audio channels.
    channels = get_formatted_audiochannels(episode['streamdetails']['audio'][0].get('channels', 0))

    # Compute watched stats.
    time_remaining = ''
    watched_percentage = 0
    if episode['resume']['position'] > 0 and episode['resume']['position'] < episode['resume']['total'] and episode['playcount'] == 0:
        time_remaining = get_formatted_timespan(episode['resume']['total'] - episode['resume']['position'])
        watched_percentage = round(episode['resume']['position'] * 100 / episode['resume']['total'])

    # Remove "Rated" from rating.
    rating = episode.get('tvshow', {'mpaa': None})['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setArt({'poster': episode['art'].get('tvshow.poster', '')})
    li.setProperty('AudioChannels', str(channels))
    li.setProperty('DurationString', duration)
    li.setProperty('TimeRemainingString', time_remaining)
    li.setProperty('WatchedPercentage', str(watched_percentage))
    li.setProperty('BlurArt.TvShow', tvshow_blur)
    li.setProperty('BlurArt.Season', season_blur)
    li.setProperty('BlurArt.TvShow.TextColor', tvshow_color)
    li.setProperty('BlurArt.Season.TextColor',season_color)
    li.setProperty('Clearlogo.Big', clearlogo)
    li.setProperty('Clearlogo.Small', clearlogo_small)

    return li

# Build a listitem for music albums.
def get_album_listitem(album):
    # Create album-type listitem.
    li = xbmcgui.ListItem(label=album['title'])
    li.setProperty('ItemType', 'album')

    # Set internal properties.
    li.setArt(album['art'])
    musicinfo = li.getMusicInfoTag()
    musicinfo.setTitle(album['title'])
    musicinfo.setYear(album['year'])
    musicinfo.setArtist(album['displayartist'])
    musicinfo.setGenres(album['genre'])
    #musicinfo.setDuration(song['albumduration'])

    # Get custom art.
    blur, color = get_blurred(album['art'].get('fanart', ''))

    # Compute duration visual string.
    #duration = get_formatted_timespan(song['albumduration'], include_seconds=True)

    # Set custom properties.
    #li.setProperty('DurationString', duration)
    li.setProperty('BlurArt', blur)
    li.setProperty('BlurArt.TextColor', color)

    return li

# Build a listitem for songs.
def get_song_listitem(song):
    # Create song-type listitem.
    li = xbmcgui.ListItem(label=song['title'])
    li.setProperty('ItemType', 'song')

    # Set internal properties.
    li.setArt(song['art'])
    musicinfo = li.getMusicInfoTag()
    musicinfo.setTitle(song['title'])
    musicinfo.setYear(song['year'])
    musicinfo.setDuration(song['duration'])
    musicinfo.setAlbum(song['album'])
    musicinfo.setTrack(song['track'])
    musicinfo.setArtist(song['displayartist'])
    musicinfo.setGenres(song['genre'])

    # Get custom art.
    blur, color = get_blurred(song['art'].get('album.thumb', ''))

    # Compute duration visual string.
    duration = get_formatted_timespan(song['duration'], include_seconds=True)

    # Set custom properties.
    li.setProperty('DurationString', duration)
    li.setProperty('BlurArt', blur)
    li.setProperty('BlurArt.TextColor', color)
    li.setProperty('Track', str(song['track']))

    return li
