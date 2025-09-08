import xbmcplugin
import xbmcgui
from utils import *
from image import get_blurred, get_cropped_clearlogo

# Default property lists.
movie_properties_query = ['art', 'title', 'year', 'resume', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre', 'playcount']
tvshow_properties_query = ['art', 'title', 'year', 'mpaa', 'genre', 'plot', 'studio', 'season', 'episode', 'watchedepisodes', 'playcount']
season_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'watchedepisodes', 'playcount']
episode_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'firstaired', 'studio', 'resume', 'streamdetails', 'plot', 'playcount']
album_properties_query = ['art', 'displayartist', 'genre', 'title', 'year']#todo#, 'albumduration', 'albumlabel', 'description', 'mood', 'style', 'theme'
song_properties_query = ['title', 'year', 'art', 'album', 'displayartist', 'duration', 'track', 'genre']


# Build a listitem for movies.
def get_movie_listitem(movie):
    # Create movie-type listitem.
    li = xbmcgui.ListItem(label=movie['title'])
    li.setProperty('ItemType', 'movie')

    # Set internal properties.
    li.setArt(movie['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(movie['movieid'])
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
    li.setProperty('FormattedGenre', ', '.join(movie['genre']))

    return li

# Build a listitem for TV shows.
def get_tvshow_listitem(tvshow):
    # Create tvshow-type listitem.
    li = xbmcgui.ListItem(label=tvshow['title'])
    li.setProperty('ItemType', 'tvshow')

    # Set internal properties.
    li.setArt(tvshow['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(tvshow['tvshowid'])
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
    li.setProperty('FormattedGenre', ', '.join(tvshow['genre']))

    return li

# Build a listitem for seasons.
def get_season_listitem(season):
    # Create season-type listitem.
    li = xbmcgui.ListItem(label=season['title'])
    li.setProperty('ItemType', 'season')

    # Set internal properties.
    li.setArt(season['art'])
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(season['seasonid'])
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
    li.setProperty('tvshowid', str(season.get('tvshow', {'tvshowid': -1})['tvshowid']))
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
    videoinfo.setDbId(episode['episodeid'])
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
    li.setProperty('tvshowid', str(episode.get('tvshow', {'tvshowid': -1})['tvshowid']))
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
    musicinfo.setDbId(album['albumid'], 'album')
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
    li.setProperty('FormattedGenre', ', '.join(album['genre']))

    return li

# Build a listitem for songs.
def get_song_listitem(song):
    # Create song-type listitem.
    li = xbmcgui.ListItem(label=song['title'])
    li.setProperty('ItemType', 'song')

    # Set internal properties.
    li.setArt(song['art'])
    musicinfo = li.getMusicInfoTag()
    musicinfo.setDbId(song['songid'], 'song')
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
    li.setProperty('FormattedGenre', ', '.join(song['genre']))

    return li

# Build a listitem for actors.
def get_actor_listitem(actor):
    # Create song-type listitem.
    li = xbmcgui.ListItem(label=actor['name'])
    li.setProperty('ItemType', 'person')

    # Set custom properties.
    li.setProperty('Name', actor['name'])
    li.setProperty('Role', actor['role'])
    li.setProperty('Thumbnail', actor.get('thumbnail', ''))

    return li


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
    
    return len(sorted_items)

#todo: integrate into list_episodes()?
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
            
        return len(episodes)
    
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
            url=f"videodb://movies/titles/{li.getVideoInfoTag().getDbId()}/",
            listitem=li,
            isFolder=False
        )
        
    return len(movies)

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
            url=f"videodb://tvshows/titles/{li.getVideoInfoTag().getDbId()}/",
            listitem=li,
            isFolder=True
        )
        
    return len(tvshows)

# Create a list of seasons.
def list_seasons(params, handle):
    showtitle = params.get('showtitle', None)
    dbpath = params.get('dbpath', None)

    tvshow = None
    
    # Work with DB path.
    if dbpath is not None:
        # Extract TV show ID from DB path.
        info = get_params_from_dbpath(dbpath)
        if info.get('tvshowid', None) is not None:
            tvshow = call_rpc('VideoLibrary.GetTVShowDetails', {
                'tvshowid': int(info['tvshowid']),
                # Get important TV show properties.
                'properties': ['mpaa', 'studio', 'plot', 'art']
            }).get('tvshowdetails', None)

    # Otherwise filter on TV show title.
    elif showtitle is not None:
        # Find reference TV show.
        shows = call_rpc('VideoLibrary.GetTVShows', {
            # Filter on title.
            'filter': {'field': 'title', 'operator': 'is', 'value': showtitle},
            # Get important TV show properties.
            'properties': ['mpaa', 'studio', 'plot', 'art']
        }).get('tvshows', [])

        if len(shows) > 0:
            tvshow = shows[0]

    # Add items if show found.
    if tvshow is not None:
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
                url=f"videodb://tvshows/titles/{li.getProperty('tvshowid')}/{li.getVideoInfoTag().getSeason()}/",
                listitem=li,
                isFolder=True
            )

        return len(seasons)

    return 0

# Create a list of episodes.
def list_episodes(params, handle):
    dbpath = params.get('dbpath', None)

    # Work with DB path.
    if dbpath is not None:
        # Extract TV show ID and season NUMBER from DB path.
        info = get_params_from_dbpath(dbpath)
        tvshowid = info.get('tvshowid', None)
        season = info.get('season', None)
        episode_number = info.get('episode', -1)
        
        # Load list of episodes using TV show ID and season.
        if tvshowid is not None and season is not None:
            episodes = call_rpc('VideoLibrary.GetEpisodes', {
                'tvshowid': int(tvshowid),
                'season': int(season),
                'sort': {'order': 'ascending', 'method': 'episode'},
                'properties': episode_properties_query
            }).get('episodes', [])
            
            if len(episodes) > 0:
                # Load TV show with title and MPAA (to be added to the episode).
                tvshow = call_rpc('VideoLibrary.GetTVShowDetails', {
                    'tvshowid': int(tvshowid),
                    # Get important TV show properties.
                    'properties': ['title', 'mpaa']
                }).get('tvshowdetails', None)

                # For each episode ID found, add to list.
                for episode in episodes:
                    # Include only episodes of the required season
                    # (basically exclude specials).
                    if episode['season'] == int(season):
                        episode['tvshow'] = tvshow
                        li = get_episode_listitem(episode)
                        xbmcplugin.addDirectoryItem(
                            handle=handle,
                            url=f"videodb://tvshows/titles/{li.getProperty('tvshowid')}/{li.getVideoInfoTag().getSeason()}/{li.getVideoInfoTag().getDbId()}/",
                            listitem=li,
                            isFolder=False
                        )
                    
                return (len(episodes), int(episode_number) - 1)
    
    return (0, -1)

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
        
    return len(songs)

# Create a list of pictures.
def list_pictures(params, handle):
    #todo
    pictures = []
    
    return len(pictures)


# Create a list of actors.
def list_actors(params, handle):
    # Retrieve DB path from parameters.
    dbpath = params.get('dbpath', None)

    # Get info from path.
    info = get_params_from_dbpath(dbpath)

    item = None

    # Movies.
    if info['type'] == 'movie' and info.get('movieid', None) is not None:
        item = call_rpc('VideoLibrary.GetMovieDetails', { 'movieid': int(info['movieid']), 'properties': ['cast'] }).get('moviedetails', None)
    # TV shows.
    if info['type'] == 'tvshow' and info.get('tvshowid', None) is not None:
        item = call_rpc('VideoLibrary.GetTVShowDetails', { 'tvshowid': int(info['tvshowid']), 'properties': ['cast'] }).get('tvshowdetails', None)
    # Seasons and episodes (always showing episodes).
    if info['type'] == 'episode':
        episodeid = info.get('episodeid', None)
        if episodeid is not None and episodeid != '':
            item = call_rpc('VideoLibrary.GetEpisodeDetails', { 'episodeid': int(episodeid), 'properties': ['cast'] }).get('episodedetails', None)

    # Add actors.
    if item is not None:
        # For each actor found add to list.
        actors = item.get('cast', [])
        for actor in actors:
            li = get_actor_listitem(actor)
            xbmcplugin.addDirectoryItem(
                handle=handle,
                url=actor['name'],
                listitem=li,
                isFolder=False
            )
            
        return len(actors)
    
    return 0


# Scaffolding for list generation.
def list_media(method, params, handle):
    listid = params.get('listid', None)
    windowid = xbmcgui.getCurrentWindowId()
    window = xbmcgui.Window(windowid)

    # Set loading indicator for list.
    if listid is not None: window.setProperty(f"List.{listid}.IsLoading", 'true')

    count = 0
    shift = -1
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
    elif method == 'episodes':
        count,shift = list_episodes(params, handle)
    elif method == 'albums':
        count = list_albums(params, handle)
    elif method == 'songs':
        count = list_songs(params, handle)
    elif method == 'pictures':
        count = list_pictures(params, handle)

    elif method == 'actors':
        count = list_actors(params, handle)

    # Use custom property to indicate there is content, so visibility can be set
    # on that property and work properly.
    if count > 0: window.setProperty(f"List.{listid}.HasContent", 'true')
    else: window.setProperty(f"List.{listid}.HasContent", 'false')

    # Set loading indicator for list to false.
    if listid is not None: window.setProperty(f"List.{listid}.IsLoading", 'false')

    # If on home, look for refocus parameter. This is a hint on to which
    # menu item to refocus when done loading.
    # It's necessary to load details when the focus is not on lists.
    if windowid == 10000:
        refocus = params.get('home_refocus_when_done', None)
        
        if refocus is not None:
            expected_page = ''
            # Populate expected page.
            if refocus == '0': expected_page = 'home'
            elif refocus == '1': expected_page = 'movies'
            elif refocus == '2': expected_page = 'tvshows'
            elif refocus == '3': expected_page = 'yoga'
            elif refocus == '4': expected_page = 'music'
            elif refocus == '5': expected_page = 'pictures'

            # Refocus on requested ID if the expected page is the active one.
            active_page = window.getProperty('ActivePage')
            if active_page == expected_page:
                xbmc.executebuiltin(f"SetFocus(1,{refocus})")

    # Close list.
    xbmcplugin.endOfDirectory(handle)

    # If a shift is requested, refocus the list item to that id.
    if shift > -1 and listid is not None:
        # Retrieve currently selected control ID.
        selected_button = window.getFocusId()
        # Shift the list to the required item.
        xbmc.executebuiltin(f"SetFocus({listid},{shift},absolute)")
        # Refocus to currently selected control.
        xbmc.executebuiltin(f"SetFocus({selected_button})")