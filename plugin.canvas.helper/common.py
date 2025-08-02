import xbmcplugin
from utils import *

# Default property lists.
movie_properties_query = ['art', 'title', 'year', 'resume', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre', 'playcount']
tvshow_properties_query = ['art', 'title', 'year', 'mpaa', 'genre', 'plot', 'studio', 'season', 'episode', 'watchedepisodes', 'playcount']
season_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'watchedepisodes', 'playcount']
episode_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'firstaired', 'studio', 'resume', 'streamdetails', 'plot', 'playcount']
album_properties_query = ['art', 'displayartist', 'genre', 'title', 'year']#todo#, 'albumduration', 'albumlabel', 'description', 'mood', 'style', 'theme'
song_properties_query = ['title', 'year', 'art', 'album', 'displayartist', 'duration', 'track', 'genre']

# Create a list of continue watching items: movies in progress, episodes in progress,
# TV shows in progress. It collapses TV shows and episodes into one single item if
# from the same TV show.
def list_continue_watching(handle):
    # In progress movies.
    movies = call_rpc('VideoLibrary.GetMovies', {
        'filter': {'field': 'inprogress', 'operator': 'is', 'value': "true"},
        'properties': movie_properties_query + ['lastplayed']
    }).get('movies', [])

    # In progress TV shows.
    tvshows = call_rpc('VideoLibrary.GetInprogressTVShows', {'properties': ['mpaa', 'lastplayed']})
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

    # Sort in progress items according to the last played.
    sorted_items = []
    for i,movie in enumerate(movies):
        sorted_items.append({
            'type': 'movie',
            'key': movie['lastplayed'],
            'id': i
        })
    for i,episode in enumerate(next_episodes):
        sorted_items.append({
            'type': 'episode',
            'key': episode['tvshow']['lastplayed'],
            'id': i
        })
    sorted_items.sort(reverse=True, key=lambda item: item['key'])

    # Add items to list, referencing proper type.
    for item in sorted_items:
        if item['type'] == 'movie':
            li = get_movie_listitem(movies[item['id']])
        elif item['type'] == 'episode':
            li = get_episode_listitem(next_episodes[item['id']])
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=movie['title'],
            listitem=li,
            isFolder=False
        )
    
    return 0#len(sorted_items)

# Create a list of recently added TV show episodes.
def list_recently_added_tvshow_episodes(handle):
    # Load first 25 episodes not from Yoga with Adriene.
    episodes = call_rpc('VideoLibrary.GetEpisodes', {
        # Exclude Yoga with Adriene.
        'filter': {'field': 'tvshow', 'operator': 'isnot', 'value': "Yoga with Adriene"},
        # Sort by date added, descending.
        'sort': {'order': 'descending', 'method': 'dateadded'},
        # Pick first 25.
        'limits': {'start': 0, 'end': 25},
        # Only get TV show title.
        'properties': episode_properties_query
    }).get('episodes', [])

    if len(episodes) > 0:
        # Load all TV shows with title and MPAA (to be added to the episode).
        all_shows = call_rpc('VideoLibrary.GetTVShows', {
            # Only get TV show title and rating for later use.
            'properties': ['title', 'mpaa']
        }).get('tvshows', [])
        # Create map of shows.
        shows = {}
        for s in all_shows:
            shows[s['title']] = s

        # For each episode ID found, add to list.
        for episode in episodes:
            episode['tvshow'] = shows[episode['showtitle']]
            li = get_episode_listitem(episode)
            xbmcplugin.addDirectoryItem(
                handle=handle,
                url=episode['title'],
                listitem=li,
                isFolder=False
            )
            
        return 0#len(episodes)
    
    return 0

# Create a list of movies.
def list_movies(params, handle):
    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = int(params.get('limit', 0))

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
            url=movie['title'],
            listitem=li,
            isFolder=False
        )
        
    return 0#len(movies)

# Create a list of TV shows.
def list_tvshows(params, handle):
    exclude = params.get('exclude', None)
    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = int(params.get('limit', 0))

    query = {
        # Sort by requested sort, with requested order.
        'sort': { 'order': order, 'method': sort },
        # Get important TV show properties.
        'properties': tvshow_properties_query
    }
    # If exclusion specified, add to call.
    if exclude is not None:
        query['filter'] = { 'field': 'title', 'operator': 'isnot', 'value': exclude }
    # If limit specified, add to call.
    if limit > 0:
        query['limits'] = { 'start': 0, 'end': limit }

    # Load TV shows.
    tvshows = call_rpc('VideoLibrary.GetTVShows', query).get('tvshows', [])

    # For each show found add to list.
    for show in tvshows:
        li = get_tvshow_listitem(show)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=show['title'],
            listitem=li,
            isFolder=True
        )
        
    return len(tvshows)

# Create a list of seasons.
def list_seasons(params, handle):
    showtitle = params.get('showtitle', None)
    
    # Filter on TV show title must be set.
    if showtitle is not None:
        # Find reference TV show.
        tvshow = call_rpc('VideoLibrary.GetTVShows', {
            # Filter on title.
            'filter': {'field': 'title', 'operator': 'is', 'value': showtitle},
            # Get important TV show properties.
            'properties': ['mpaa', 'studio', 'plot', 'art']
        }).get('tvshows', [])

        if len(tvshow) > 0:
            tvshow = tvshow[0]

            sort = params.get('sort', 'season')
            order = params.get('order', 'ascending')
            limit = int(params.get('limit', 0))
            query = {
                # Filter by TV show.
                'tvshowid': tvshow['tvshowid'],
                # Get important season properties.
                'properties': season_properties_query
            }
            # If limit specified, add to call.
            if limit > 0:
                query['limits'] = { 'start': 0, 'end': limit }

            # Get seasons.
            seasons = call_rpc('VideoLibrary.GetSeasons', query).get('seasons', [])
            # Sort by requested sort, with requested order (JSON-RPC sorting might not work on season number...).
            seasons.sort(key=lambda s:s[sort], reverse=(order == 'descending'))

            # For each season, add to list.
            for season in seasons:
                season['tvshow'] = tvshow
                li = get_season_listitem(season)
                xbmcplugin.addDirectoryItem(
                    handle=handle,
                    url=season['title'],
                    listitem=li,
                    isFolder=True
                )

            return len(seasons)

    return 0

# Create a list of albums.
def list_albums(params, handle):
    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = int(params.get('limit', 0))

    query = {
        # Sort by requested sort, with requested order.
        'sort': { 'order': order, 'method': sort },
        # Get important TV show properties.
        'properties': album_properties_query
    }
    # If limit specified, add to call.
    if limit > 0:
        query['limits'] = { 'start': 0, 'end': limit }

    # Load albums.
    albums = call_rpc('AudioLibrary.GetAlbums', query).get('albums', [])

    # For each album found add to list.
    for album in albums:
        li = get_album_listitem(album)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=album['title'],
            listitem=li,
            isFolder=True
        )
    
    return len(albums)

# Create a list of songs.
def list_songs(params, handle):
    sort = params.get('sort', 'title')
    order = params.get('order', 'ascending')
    limit = int(params.get('limit', 0))
    albumid = params.get('albumid', None)
    album = params.get('album', None)

    query = {
        # Sort by requested sort, with requested order.
        'sort': { 'order': order, 'method': sort },
        # Get important movie properties.
        'properties': song_properties_query
    }
     # If limit specified, add to call.
    if limit > 0:
        query['limits'] = { 'start': 0, 'end': limit }
     # If album specified, add to call.
    if albumid is not None:
        query['filter'] = { 'field': 'albumid', 'operator': 'is', 'value': albumid }
    elif album is not None:
        query['filter'] = { 'field': 'album', 'operator': 'is', 'value': album }

    # Load songs.
    songs = call_rpc('AudioLibrary.GetSongs', query).get('songs', [])

    # For each movie found add to list.
    for song in songs:
        li = get_song_listitem(song)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=song['title'],
            listitem=li,
            isFolder=False
        )
        
    return 0#len(songs)

# Create a list of pictures.
def list_pictures(params, handle):
    #todo
    pictures = []
    
    return len(pictures)

# Scaffolding for list generation.
def list_objects(method, params, handle):
    listid = params.get('listid', None)
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    count = 0
    # Call appropriate method.
    if method == 'continue_watching':
        count = list_continue_watching(handle)
    elif method == 'recently_added_tvshow_episodes':
        count = list_recently_added_tvshow_episodes(handle)
    elif method == 'movies':
        count = list_movies(params, handle)
    elif method == 'tvshows':
        count = list_tvshows(params, handle)
    elif method == 'seasons':
        count = list_seasons(params, handle)
    elif method == 'albums':
        count = list_albums(params, handle)
    elif method == 'songs':
        count = list_songs(params, handle)
    elif method == 'pictures':
        count = list_pictures(params, handle)

    # Use custom property to indicate there is content, so visibility can be set
    # on that property and work properly.
    if count > 0: window.setProperty(f"List.{listid}.HasContent", 'true')
    else: window.setProperty(f"List.{listid}.HasContent", 'false')

    # Close list.
    xbmcplugin.endOfDirectory(handle)
