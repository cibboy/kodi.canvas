import sys
import math
import json
import xbmc
import xbmcgui
import xbmcplugin
from urllib.parse import urlparse, parse_qsl
from image import get_blurred, get_cropped_clearlogo
from utils import get_formatted_timespan

handle = int(sys.argv[1])

# Default property lists.
movie_properties_query = ['title', 'year', 'resume', 'art', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre', 'playcount']
episode_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'firstaired', 'studio', 'resume', 'streamdetails', 'plot', 'playcount']
song_properties_query = ['title', 'year', 'art', 'album', 'artist', 'duration', 'track', 'genre']

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
    videoinfo.setPlayCount(movie['playcount'])

    # Get custom art.
    blur = get_blurred(movie['art'].get('fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(movie['art'].get('clearlogo', ''))

    # Compute duration visual string.
    duration = get_formatted_timespan(movie['streamdetails']['video'][0]['duration'])

    # Compute watched stats.
    time_remaining = ''
    watched_percentage = 0
    if movie['resume']['position'] > 0 and movie['resume']['position'] < movie['resume']['total'] and movie['playcount'] == 0:
        time_remaining = get_formatted_timespan(movie['resume']['total'] - movie['resume']['position'])
        watched_percentage = movie['resume']['position'] * 100 / movie['resume']['total']

    # Remove "Rated" from rating.
    rating = movie['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setProperty('DurationString', duration)
    li.setProperty('TimeRemainingString', time_remaining)
    li.setProperty('WatchedPercentage', watched_percentage)
    li.setProperty('BlurArt', blur)
    li.setProperty('Clearlogo.Big', clearlogo)

    return li

# Build a listitem for TV shows.
def get_tvshow_listitem():
    #todo
    a = 0

# Build a listitem for seasons.
def get_season_listitem():
    #todo
    a = 0

# Build a listitem for episodes.
def get_episode_listitem(episode):
    # Create movie-type listitem.
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
    videoinfo.setPlayCount(movie['playcount'])

    # Get custom art.
    tvshow_blur = get_blurred(episode['art'].get('tvshow.fanart', ''))
    season_blur = get_blurred(episode['art'].get('season.fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(episode['art'].get('tvshow.clearlogo', ''), True)

    # Compute duration visual string.
    duration = get_formatted_timespan(episode['streamdetails']['video'][0]['duration'])

    # Compute watched stats.
    time_remaining = ''
    watched_percentage = 0
    if movie['resume']['position'] > 0 and movie['resume']['position'] < movie['resume']['total'] and movie['playcount'] == 0:
        time_remaining = get_formatted_timespan(movie['resume']['total'] - movie['resume']['position'])
        watched_percentage = movie['resume']['position'] * 100 / movie['resume']['total']

    # Remove "Rated" from rating.
    rating = episode.get('tvshow', {'mpaa': None})['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setArt({'poster': episode['art'].get('tvshow.poster', '')})
    li.setProperty('DurationString', duration)
    li.setProperty('TimeRemainingString', time_remaining)
    li.setProperty('WatchedPercentage', watched_percentage)
    li.setProperty('BlurArt.TvShow', tvshow_blur)
    li.setProperty('BlurArt.Season', season_blur)
    li.setProperty('Clearlogo.Big', clearlogo)
    li.setProperty('Clearlogo.Small', clearlogo_small)

    return li

# Build a listitem for music albums.
def get_album_listitem():
    #todo
    a = 0

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
    musicinfo.setArtist(', '.join(song['artist']))
    musicinfo.setGenres(song['genre'])

    # Get custom art.
    blur = get_blurred(song['art'].get('album.thumb', ''))

    # Compute duration visual string.
    duration = get_formatted_timespan(song['duration'], include_seconds=True)

     # Set custom properties.
    li.setProperty('DurationString', duration)
    li.setProperty('BlurArt', blur)

    return li

# Build a listitem for pictures.
def get_picture_listitem():
    #todo
    a = 0

# Create a list of continue watching items: movies in progress, episodes in progress,
# TV shows in progress. It collapses TV shows and episodes into one single item if
# from the same TV show.
def list_continue_watching(params):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'true')

    # All movies, then filter them for those in progress.
    movies = call_rpc('VideoLibrary.GetMovies', {'properties': movie_properties_query})
    movies = [
        m for m in movies.get('movies', [])
        if 0 < m['resume']['position'] < m['resume']['total']
    ]

    # In progress TV shows.
    tvshows = call_rpc('VideoLibrary.GetInprogressTVShows', {'properties': ['mpaa']})
    # For each show, find the next episode.
    next_episodes = []
    for tvshow in tvshows.get('tvshows', []):
        next_episode = call_rpc('VideoLibrary.GetEpisodes', {
            # Filter by show ID.
            'tvshowid': tvshow['tvshowid'],
            # Then find those with a playcount of 0, excluding specials.
            'filter': {
                'and': [
                    {'field': 'playcount', 'operator': 'is', 'value': "0"},
                    {'field': 'season', 'operator': 'greaterthan', 'value': "0"}
                ]
            },
            # Sort by episode, ascending.
            'sort': {'order': 'ascending', 'method': 'episode'},
            # Pick the first.
            'limits': {'start': 0, 'end': 1},
            'properties': episode_properties_query
        }).get('episodes', [])

        if next_episode is not None and len(next_episode) > 0:
            next_episode = next_episode[0]
            next_episode['tvshow'] = tvshow
            next_episodes.append(next_episode)

    #todo: sort movies, episodes by last viewed, then add
    
    for movie in movies:
        li = get_movie_listitem(movie)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=movie['title'],#todo
            listitem=li,
            isFolder=False
        )

    for episode in next_episodes:
        li = get_episode_listitem(episode)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=episode['title'],#todo
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(handle)

    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'false')

# Create a list of recently added TV show episodes.
def list_recently_added_tvshow_episodes(params):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'true')

    # Load all episodes.
    all_episodes = call_rpc('VideoLibrary.GetEpisodes', {
        # Sort by date added, descending.
        'sort': {'order': 'descending', 'method': 'dateadded'},
        # Only get TV show title.
        'properties': ['showtitle']
    }).get('episodes', [])

    # Get first 20 episodes that are not Yoga with Adriene.
    episodes = []
    count = 0
    for e in all_episodes:
        # Stop at 25.
        if count == 25:
            break
        
        # If not Yoga with Adriene, add to list.
        if e['showtitle'].lower() != 'yoga with adriene':
            episodes.append(e)
            count += 1

    if len(episodes) > 0:
        # Load all TV shows.
        all_shows = call_rpc('VideoLibrary.GetTVShows', {
            # Only get TV show title and rating for later use.
            'properties': ['title', 'mpaa']
        }).get('tvshows', [])
        # Create map of shows.
        shows = {}
        for s in all_shows:
            shows[s['title']] = s

        # For each episode ID found, get details and add to list.
        for e in episodes:
            episode = call_rpc('VideoLibrary.GetEpisodeDetails', {'episodeid': e['episodeid'], 'properties': episode_properties_query}).get('episodedetails', None)
            if episode is not None:
                # Add show info, then create listitem.
                episode['tvshow'] = shows[e['showtitle']]
                li = get_episode_listitem(episode)
                xbmcplugin.addDirectoryItem(
                    handle=handle,
                    url=episode['title'],#todo
                    listitem=li,
                    isFolder=False
                )

    xbmcplugin.endOfDirectory(handle)

    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'false')

# Create a list of movies.
def list_movies(params):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'true')

    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = params.get('limit', 0)

    query = {
        # Sort by requested sort, with requested order.
        'sort': { 'order': order, 'method': sort },
        # Get important movie properties.
        'properties': movie_properties_query
    }
     # If limit specified, add to call.
    if limit > 0:
        query['limits'] = { 'start': 0, 'end': limit }

    # Load movies.
    movies = call_rpc('VideoLibrary.GetMovies', query).get('movies', [])

    # For each movie found add to list.
    for movie in movies:
        li = get_movie_listitem(movie)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=movie['title'],#todo
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(handle)

    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'false')

# Create a list of songs.
def list_songs(params):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'true')

    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = params.get('limit', 0)

    query = {
        # Sort by requested sort, with requested order.
        'sort': { 'order': order, 'method': sort },
        # Get important movie properties.
        'properties': song_properties_query
    }
     # If limit specified, add to call.
    if limit > 0:
        query['limits'] = { 'start': 0, 'end': limit }

    # Load songs.
    songs = call_rpc('AudioLibrary.GetSongs', query).get('songs', [])

    # For each movie found add to list.
    for song in songs:
        li = get_song_listitem(song)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=song['title'],#todo
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(handle)

    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'false')

# Create a list of seasons of Yoga with Adriene.
def list_yoga_with_adriene(params):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'true')

    # Set loading.
    if listid is not None:
        window.setProperty(f"ListLoading.{listid}", 'false')

if __name__ == '__main__':
    # Parse the full plugin URL.
    parsed = urlparse(sys.argv[0])
    # Example result:
    # parsed.path == "/mymethod/"
    # parsed.query == "param1=value1&param2=value2"

    # Strip leading/trailing slashes, split on "/"", take first segment as requested method.
    segments = parsed.path.strip('/').split('/')
    if not segments or not segments[0]:
        xbmc.log('No plugin method supplied', xbmc.LOGERROR)
    method = segments[0]

    # Parse parameters in a dictionary.
    params = dict(parse_qsl(parsed.query))
    # Example result: params == {'param1': 'value1', 'param2': 'value2'}

    if method == 'continue_watching':
        list_continue_watching(params)
    elif method == 'recently_added_tvshow_episodes':
        list_recently_added_tvshow_episodes(params)
    elif method == 'movies':
        list_movies(params)
    elif method == 'songs':
        list_songs(params)
    elif method == 'yoga_with_adriene':
        list_yoga_with_adriene(params)