import os
import xbmcplugin
import xbmcgui
from collections import defaultdict
from utils import *


# Default property lists.
movie_properties_query = ['file', 'art', 'title', 'year', 'resume', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre', 'playcount']
season_properties_query = ['art', 'showtitle', 'title', 'season', 'episode', 'watchedepisodes', 'playcount']
episode_properties_query = ['file', 'art', 'showtitle', 'title', 'season', 'episode', 'firstaired', 'studio', 'resume', 'streamdetails', 'plot', 'playcount']


# Returns additional, non-native info from a movie.
def get_additional_movie_info(itemid):
    # Load movie details.
    query = {
        'movieid': itemid,
        'properties': ['resume', 'mpaa']
    }
    movie = call_rpc('VideoLibrary.GetMovieDetails', query).get('moviedetails', {'mpaa': '', 'resume': {}})

    # Compute remaining minutes.
    position = movie['resume'].get('position', 0)
    total = movie['resume'].get('total', 0)
    time_remaining = 0
    remaining = ''
    if position > 0 and position < total:
        time_remaining = total - position
        if time_remaining > 3600: remaining = format_timespan(time_remaining, '[H]h [m]m')
        else: remaining = format_timespan(time_remaining, '[m]m')

    # Return values.
    return {
        'mpaa': movie['mpaa'].replace('Rated ', ''),
        'time_remaining': remaining
    }

# Returns additional, non-native info from a TV show.
def get_additional_tvshow_info(itemid):
    # Load TV show details.
    query = {
        'tvshowid': itemid,
        'properties': ['mpaa']
    }
    show = call_rpc('VideoLibrary.GetTVShowDetails', query).get('tvshowdetails', {'mpaa': ''})

    # Return values.
    return {
        'mpaa': show['mpaa'].replace('Rated ', ''),
    }

# Returns additional, non-native info from a TV show season.
def get_additional_season_info(itemid):
    # Load season details.
    query = {
        'seasonid': itemid,
        'properties': ['tvshowid']
    }
    season = call_rpc('VideoLibrary.GetSeasonDetails', query).get('seasondetails', {'tvshowid': None})
    show = {'mpaa': ''}
    # Load reference TV show MPAA.
    if season['tvshowid'] is not None:
        query = {
            'tvshowid': season['tvshowid'],
            'properties': ['mpaa']
        }
        show = call_rpc('VideoLibrary.GetTVShowDetails', query).get('tvshowdetails', {'mpaa': ''})

    # Return values.
    return {
        'mpaa': show['mpaa'].replace('Rated ', ''),
    }

# Returns additional, non-native info from a TV show episode.
def get_additional_episode_info(itemid):
    # Load episode details.
    query = {
        'episodeid': itemid,
        'properties': ['resume', 'tvshowid']
    }
    episode = call_rpc('VideoLibrary.GetEpisodeDetails', query).get('episodedetails', {'tvshowid': None, 'resume': {}})
    show = {'mpaa': ''}
    # Load reference TV show MPAA.
    if episode['tvshowid'] is not None:
        query = {
            'tvshowid': episode['tvshowid'],
            'properties': ['mpaa']
        }
        show = call_rpc('VideoLibrary.GetTVShowDetails', query).get('tvshowdetails', {'mpaa': ''})

    # Compute remaining minutes.
    position = episode['resume'].get('position', 0)
    total = episode['resume'].get('total', 0)
    time_remaining = 0
    remaining = ''
    if position > 0 and position < total:
        time_remaining = total - position
        if time_remaining > 3600: remaining = format_timespan(time_remaining, '[H]h [m]m')
        else: remaining = format_timespan(time_remaining, '[m]m')

    # Return values.
    return {
        'mpaa': show['mpaa'].replace('Rated ', ''),
        'time_remaining': remaining
    }


# Finds the next episode to play, if any.
def get_next_episode(tvshowid, season, episode):
    try:
        tvshowid = int(tvshowid)
        season = int(season)
        episode = int(episode)
    except:
        tvshowid = -1
        season = -1
        episode = -1

    # Look up.
    ep = None
    if tvshowid > -1 and season > -1 and episode > -1:
        # Load all show episodes.
        episodes = call_rpc('VideoLibrary.GetEpisodes', {
            'tvshowid': tvshowid,
            # Sort by episode, ascending.
            'sort': {'order': 'ascending', 'method': 'episode'},
            'properties': ['season', 'episode']
        }).get('episodes', [])

        # Find episode:
        # - if season 0 ok to select season 0
        # - otherwise skip specials, propose actual next
        found_current = False
        for e in episodes:
            ep_num = e.get('episode', -1)
            s_num = e.get('season', -1)
            if ep_num > -1 and s_num > -1 and ep_num == episode and s_num == season:
                found_current = True
                continue
            if found_current:
                if (s_num == 0 and season == 0) or (season > 0 and s_num != 0):
                    ep = e
                    break

    # Load details if found.
    if ep is not None:
        ep = call_rpc('VideoLibrary.GetEpisodeDetails', {
            'episodeid': ep['episodeid'],
            'properties': episode_properties_query
        }).get('episodedetails', None)

    return ep


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
            'key': movie.get('lastplayed', ''),
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
        url = ''
        if item['type'] == 'movie':
            li = get_movie_listitem(movies[item['id']])
            url = movies[item['id']].get('file', '')
        elif item['type'] == 'episode':
            li = get_episode_listitem(next_episodes[item['id']])
            url = next_episodes[item['id']].get('file', '')

        xbmcplugin.addDirectoryItem(
            handle = handle,
            url = url,
            listitem = li,
            isFolder = False
        )
    
    return len(sorted_items)

# Create a list of recently added episodes: it's limited to 5 episodes per TV show,
# so one recently added doesn't clog up the whole list.
def list_recent_episodes(handle):
    # Load all episodes not from Yoga with Adriene.
    episodes = call_rpc('VideoLibrary.GetEpisodes', {
        # Exclude Yoga with Adriene.
        'filter': {'field': 'tvshow', 'operator': 'isnot', 'value': "Yoga with Adriene"},
        # Sort by date added, descending.
        'sort': {'order': 'descending', 'method': 'dateadded'},
        # Get properties.
        'properties': episode_properties_query + ['dateadded']
    }).get('episodes', [])

    if len(episodes) > 0:
        # Group by TV show title.
        grouped = defaultdict(list)
        for ep in episodes:
            grouped[ep['showtitle']].append(ep)

        # Keep max 5 per show.
        limited = []
        for show, eps in grouped.items():
            limited.extend(eps[:5])

        # Sort again by dateadded and take top 30.
        limited.sort(key=lambda e: e['dateadded'], reverse=True)
        final_list = limited[:30]

        # Load all TV shows with title to link TV show ID to episode.
        all_shows = call_rpc('VideoLibrary.GetTVShows', {
            # Only get TV show title and rating for later use.
            'properties': ['title']
        }).get('tvshows', [])
        # Group by TV show title.
        shows = defaultdict(list)
        for ep in all_shows:
            shows[ep['title']].append(ep)

        # For each episode ID found, add to list.
        for episode in final_list:
            episode['tvshow'] = shows[episode['showtitle']][0]
            li = get_episode_listitem(episode)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = episode.get('file', ''),
                listitem = li,
                isFolder = False
            )
            
        return len(episodes)
    
    return 0

# Create a list of Yoga With Adriene seasons.
def list_yoga_seasons(handle):
    # Find reference TV show.
    tvshow = None
    shows = call_rpc('VideoLibrary.GetTVShows', {
        # Filter on title.
        'filter': {'field': 'title', 'operator': 'is', 'value': 'Yoga with Adriene'},
        # Get important TV show properties.
        'properties': ['mpaa', 'studio', 'plot', 'art']
    }).get('tvshows', [])

    if len(shows) > 0:
        tvshow = shows[0]

    # Add items if show found.
    if tvshow is not None:
        query = {
            # Filter by TV show.
            'tvshowid': tvshow['tvshowid'],
            # Get important season properties.
            'properties': season_properties_query
        }

        # Get seasons.
        seasons = call_rpc('VideoLibrary.GetSeasons', query).get('seasons', [])
        # Sort by requested sort, with requested order (JSON-RPC sorting might not work on season number...).
        seasons.sort(key=lambda s:s['season'], reverse=False)

        # For each season, add to list.
        specials = None
        for season in seasons:
            season['tvshow'] = tvshow
            # Skip specials to add at the end.
            if int(season.get('season', -1)) == 0:
                specials = season
                continue
            li = get_season_listitem(season)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = f"videodb://tvshows/titles/{tvshow['tvshowid']}/{li.getVideoInfoTag().getSeason()}/",
                listitem = li,
                isFolder = True
            )
        # Add specials to the end, if present.
        if specials is not None:
            li = get_season_listitem(specials)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = f"videodb://tvshows/titles/{tvshow['tvshowid']}/{li.getVideoInfoTag().getSeason()}/",
                listitem = li,
                isFolder = True
            )

        return len(seasons)

    return 0

# Create a list with the single requested movie.
def list_single_movie(params, handle):
    movieid = int(params.get('dbid', -1))
    if movieid > -1:
        # Find requested movie.
        movie = call_rpc('VideoLibrary.GetMovieDetails', {
            'movieid': movieid,
            'properties': movie_properties_query
        }).get('moviedetails', None)

        if movie is not None:
            li = get_movie_listitem(movie)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = movie.get('file', ''),
                listitem = li,
                isFolder = False
            )

            return 1

    return 0

# Create a list with the single requested song.
def list_single_song(params, handle):
    songid = int(params.get('dbid', -1))
    if songid > -1:
        # Find requested song.
        song = call_rpc('AudioLibrary.GetSongDetails', {
            'songid': songid,
            'properties': ['title']
        }).get('songdetails', None)

        if song is not None:
            li = get_song_listitem(song)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = '',
                listitem = li,
                isFolder = False
            )

            return 1

    return 0

# Create a list of actors.
def list_actors(params, handle):
    # Retrieve item type and ID from parameters.
    type = params.get('dbtype', None)
    id = params.get('dbid', None)

    item = None

    # Seasons don't have cast, so retrieve tvshow and use that.
    if type == 'season' and id is not None:
        type = 'tvshow'
        id = call_rpc('VideoLibrary.GetSeasonDetails', { 'seasonid': int(id), 'properties': ['tvshowid'] }).get('seasondetails', {}).get('tvshowid', 0)

    # Movies.
    if type == 'movie' and id is not None:
        item = call_rpc('VideoLibrary.GetMovieDetails', { 'movieid': int(id), 'properties': ['cast'] }).get('moviedetails', None)
    # TV shows.
    elif type == 'tvshow' and id is not None:
        item = call_rpc('VideoLibrary.GetTVShowDetails', { 'tvshowid': int(id), 'properties': ['cast'] }).get('tvshowdetails', None)
    # Episodes.
    elif type == 'episode' and id is not None:
        item = call_rpc('VideoLibrary.GetEpisodeDetails', { 'episodeid': int(id), 'properties': ['cast'] }).get('episodedetails', None)

    # Add actors.
    if item is not None:
        # For each actor found add to list.
        actors = item.get('cast', [])
        for actor in actors:
            li = get_actor_listitem(actor)
            xbmcplugin.addDirectoryItem(
                handle = handle,
                url = f"videodb://actors/{actor.get('id', '')}/",
                listitem = li,
                isFolder = False
            )
            
        return len(actors)
    
    return 0

# Create a list of pictures.
def list_pictures(params, handle):
    type = params.get('type', None)
    total = 0

    # Get all picture sources.
    sources = call_rpc('Files.GetSources', { 'media': 'pictures' }).get('sources', [])
    # For each source, get all directories.
    for s in sources:
        source_dir = s.get('file', None)
        if source_dir is not None:
            dirs = call_rpc('Files.GetDirectory', { 'directory': source_dir }).get('files', [])
            # For each directory create a list item if requesting albums, otherwise work recursively.
            for d in dirs:
                if type == 'album':
                    total += 1
                    li = xbmcgui.ListItem(label = f"{d.get('label', '')}")
                    li.setProperty('Type', 'picturealbum')
                    xbmcplugin.addDirectoryItem(
                        handle = handle,
                        url = d.get('file', ''),
                        listitem = li,
                        isFolder = True
                    )
                else:
                    path = d.get('file', None)
                    if path is not None:
                        pics = get_pictures_recursive(path)
                        for p in pics:
                            total += 1
                            li = xbmcgui.ListItem(label = f"{p.get('label', '')}")
                            li.setProperty('Type', 'picture')
                            pic_path = p.get('file', '')
                            if pic_path != '': li.setProperty('Album', os.path.basename(os.path.dirname(pic_path)))
                            xbmcplugin.addDirectoryItem(
                                handle = handle,
                                url = pic_path,
                                listitem = li,
                                isFolder = False
                            )
                            
    return total

# Recursive function to retrieve pictures.
def get_pictures_recursive(path):
    ret = []

    # Get elements in path.
    dirs = call_rpc('Files.GetDirectory', { 'directory': path }).get('files', [])
    for e in dirs:
        elem_type = e.get('filetype', '')
        p = e.get('file', None)
        # If element is a file, add to list.
        if elem_type == 'file':
            p = p.lower()
            if p.endswith('.jpg') or p.endswith('.jpeg') or p.endswith('.png') or p.endswith('.gif'):
                ret.append(e)
        # Otherwise search recursively.
        elif elem_type == 'directory':
            if p is not None: ret.extend(get_pictures_recursive(p))

    return ret


# Build a listitem for movies.
def get_movie_listitem(movie):
    # Create movie-type listitem.
    li = xbmcgui.ListItem(label = movie.get('title', ''))

    # Set internal properties.
    li.setArt(movie.get('art', {}))
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(int(movie.get('movieid', -1)))
    videoinfo.setMediaType('movie')
    videoinfo.setTitle(movie.get('title', ''))
    videoinfo.setYear(int(movie.get('year', -1)))
    videoinfo.setStudios(movie.get('studio', []))
    videoinfo.setPlot(movie.get('plot', ''))
    videoinfo.setMpaa(movie.get('mpaa', ''))
    videoinfo.setGenres(movie.get('genre', []))
    videoinfo.setDuration(int(movie.get('streamdetails', {}).get('video', [{}])[0].get('duration', 0)))
    videoinfo.setResumePoint(float(movie.get('resume', {}).get('position', 0)), float(movie.get('resume', {}).get('total', 0)))
    videoinfo.setPlaycount(int(movie.get('playcount', 0)))
    for video in movie.get('streamdetails', {}).get('video', []):
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
    for audio in movie.get('streamdetails', {}).get('audio', []):
        stream = xbmc.AudioStreamDetail(
            audio.get('channels', 0),
            audio.get('codec', ''),
            audio.get('language', '')
        )
        videoinfo.addAudioStream(stream)
    for sub in movie.get('streamdetails', {}).get('subtitle', []):
        stream = xbmc.SubtitleStreamDetail(sub.get('language', ''))
        videoinfo.addSubtitleStream(stream)

    return li

# Build a listitem for seasons.
def get_season_listitem(season):
    # Create season-type listitem.
    li = xbmcgui.ListItem(label = season.get('title', ''))

    # Set internal properties.
    li.setArt(season.get('art', {}))
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(int(season.get('seasonid', -1)))
    videoinfo.setMediaType('season')
    videoinfo.setTitle(season.get('title', ''))
    videoinfo.setSeason(int(season.get('season', -1)))
    videoinfo.setEpisode(int(season.get('episode', -1)))
    videoinfo.setStudios(season.get('tvshow', {'studio': []}).get('studio', []))
    videoinfo.setPlot(season.get('tvshow', {'plot': ''}).get('plot', ''))
    videoinfo.setTvShowTitle(season.get('showtitle', ''))
    videoinfo.setPlaycount(int(season.get('playcount', 0)))

    # Compute watched stats.
    total = int(season.get('episode', 0))
    watched_percentage = 0
    watched = int(season.get('watchedepisodes', 0))
    unwatched = 0
    if total > 0:
        watched_percentage = int(round(watched * 100 / total))
        unwatched = total - watched

    # Set custom properties.
    li.setProperty('TotalEpisodes', str(total))
    li.setProperty('WatchedEpisodes', str(watched))
    li.setProperty('UnWatchedEpisodes', str(unwatched))
    li.setProperty('WatchedEpisodePercent', str(watched_percentage))
    li.setProperty('TvShowId', str(season.get('tvshow', {}).get('tvshowid', '')))

    return li

# Build a listitem for episodes.
def get_episode_listitem(episode):
    # Create episode-type listitem.
    li = xbmcgui.ListItem(label = episode.get('title', ''))

    # Set internal properties.
    li.setArt(episode.get('art', {}))
    videoinfo = li.getVideoInfoTag()
    videoinfo.setDbId(int(episode.get('episodeid', -1)))
    videoinfo.setMediaType('episode')
    videoinfo.setTitle(episode.get('title', ''))
    videoinfo.setSeason(int(episode.get('season', -1)))
    videoinfo.setEpisode(int(episode.get('episode', -1)))
    videoinfo.setPremiered(episode.get('firstaired', ''))
    videoinfo.setStudios(episode.get('studio', []))
    videoinfo.setPlot(episode.get('plot', ''))
    videoinfo.setTvShowTitle(episode.get('showtitle', ''))
    videoinfo.setDuration(int(episode.get('streamdetails', {}).get('video', [{}])[0].get('duration', 0)))
    videoinfo.setResumePoint(float(episode.get('resume', {}).get('position', 0)), float(episode.get('resume', {}).get('total', 0)))
    videoinfo.setPlaycount(int(episode.get('playcount', 0)))
    for video in episode.get('streamdetails', {}).get('video', []):
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
    for audio in episode.get('streamdetails', {}).get('audio', []):
        stream = xbmc.AudioStreamDetail(
            audio.get('channels', 0),
            audio.get('codec', ''),
            audio.get('language', '')
        )
        videoinfo.addAudioStream(stream)
    for sub in episode.get('streamdetails', {}).get('subtitle', []):
        stream = xbmc.SubtitleStreamDetail(sub.get('language', ''))
        videoinfo.addSubtitleStream(stream)
    
    # Set custom properties.
    li.setProperty('TvShowId', str(episode.get('tvshow', {}).get('tvshowid', '')))

    return li

# Build a listitem for songs (title only, used only in player to trigger info reload).
def get_song_listitem(song):
    # Create movie-type listitem.
    li = xbmcgui.ListItem(label = song.get('title', ''))

    return li

# Build a listitem for actors.
def get_actor_listitem(actor):
    # Create song-type listitem.
    li = xbmcgui.ListItem(label = actor.get('name', ''))

    # Set custom properties.
    li.setProperty('Name', actor.get('name', ''))
    li.setProperty('Role', actor.get('role', ''))
    li.setProperty('Thumbnail', actor.get('thumbnail', ''))

    return li
