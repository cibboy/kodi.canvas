import sys
import math
import json
import xbmc
import xbmcgui
import xbmcplugin
from image import get_blurred, get_cropped_clearlogo

handle = int(sys.argv[1])

# Default property lists.
movie_properties_query = ['title', 'year', 'resume', 'art', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre']
episode_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'firstaired', 'studio', 'playcount', 'resume', 'streamdetails', 'plot']
song_properties_query = ['title', 'year', 'art', 'album', 'artist', 'duration']

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

    # Get custom art.
    blur = get_blurred(movie['art'].get('fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(movie['art'].get('clearlogo', ''))

    # Compute duration visual string.
    duration = movie['streamdetails']['video'][0]['duration']
    if duration >= 3600:
        hours = math.floor(duration / 3600)
        minutes = math.floor((duration - (hours * 3600)) / 60)
        duration = f"{hours}h{minutes}m"
    else:
        duration = f"{math.floor(duration / 60)}m"

    # Remove "Rated" from rating.
    rating = movie['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    videoinfo.setMpaa(rating)
    li.setProperty('DurationString', duration)
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

    # Get custom art.
    tvshow_blur = get_blurred(episode['art'].get('tvshow.fanart', ''))
    season_blur = get_blurred(episode['art'].get('season.fanart', ''))
    clearlogo, clearlogo_small = get_cropped_clearlogo(episode['art'].get('tvshow.clearlogo', ''), True)

    # Compute duration visual string.
    duration = episode['streamdetails']['video'][0]['duration']
    if duration >= 3600:
        hours = math.floor(duration / 3600)
        minutes = math.floor((duration - (hours * 3600)) / 60)
        duration = f"{hours}h{minutes}m"
    else:
        duration = f"{math.floor(duration / 60)}m"

    # Remove "Rated" from rating.
    rating = episode.get('tvshow', {'mpaa': None})['mpaa']
    if rating is not None:
        rating = rating.replace('Rated ', '')
    else:
        rating = ''

    # Set custom properties.
    li.setArt({'poster': episode['art'].get('tvshow.poster', '')})
    videoinfo.setMpaa(rating)
    li.setProperty('DurationString', duration)
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
    musicinfo.setArtist(', '.join(song['artist']))

    # Get custom art.
    blur = get_blurred(song['art'].get('album.thumb', ''))#todo: not working (usual problem of escaping, that must not be done?)

    # Compute duration visual string.
    duration = song['duration']
    if duration >= 3600:
        hours = math.floor(duration / 3600)
        minutes = math.floor((duration - (hours * 3600)) / 60)
        seconds = math.floor(duration - (hours * 3600) - (minutes * 60))
        duration = f"{hours}h{minutes:0>2}m{seconds:0>2}s"
    elif duration > 60:
        minutes = math.floor(duration / 60)
        seconds = math.floor(duration - (minutes * 60))
        duration = f"{minutes}m{seconds:0>2}s"
    else:
        duration = f"{duration}s"

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
def list_continue_watching():
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

# Create a list of recently added TV show episodes.
def list_recently_added_tvshow_episode():
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

# Create a list of recently added movies.
def list_recently_added_movies():
    # Load recently added movies.
    movies = call_rpc('VideoLibrary.GetMovies', {
        # Sort by date added, descending.
        'sort': {'order': 'descending', 'method': 'dateadded'},
        # Pick the first 25.
        'limits': {'start': 0, 'end': 25},
        # Get important movie properties.
        'properties': movie_properties_query
    }).get('movies', [])

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

# Create a list of recently added songs.
def list_recently_added_songs():
    # Load recently added songs.
    songs = call_rpc('AudioLibrary.GetSongs', {
        # Sort by date added, descending.
        'sort': {'order': 'descending', 'method': 'dateadded'},
        # Pick the first 25.
        'limits': {'start': 0, 'end': 25},
        # Get important song properties.
        'properties': song_properties_query
    }).get('songs', [])

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

# Create a list of seasons of Yoga with Adriene.
def list_yoga_with_adriene():
    #todo
    a = 0

if __name__ == '__main__':
    method = sys.argv[0].replace('plugin://script.canvas.helper/', '')
    if method.endswith('/'):
        method = method[:-1]

    if method == 'continue_watching':
        list_continue_watching()
    elif method == 'recently_added_tvshow_episode':
        list_recently_added_tvshow_episode()
    elif method == 'recently_added_movies':
        list_recently_added_movies()
    elif method == 'recently_added_songs':
        list_recently_added_songs()
    elif method == 'yoga_with_adriene':
        list_yoga_with_adriene()