#import xbmcgui, xbmcplugin, json, urllib.request
#from urllib.parse import parse_qs
import sys
import json
import xbmc
import xbmcgui
import xbmcplugin
from urllib.parse import parse_qs

handle = int(sys.argv[1])

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

# Create a list of continue watching items: movies in progress, episodes in progress,
# TV shows in progress. It collapses TV shows and episodes into one single item if
# from the same TV show.
def list_continue_watching():
    movies = call_rpc('VideoLibrary.GetMovies', {'properties': ['title', 'year', 'resume', 'art', 'plot', 'studio', 'streamdetails', 'mpaa', 'genre']})
    shows = call_rpc('VideoLibrary.GetInprogressTVShows', {'properties': ['title', 'art', 'mpaa']})

    filtered_movies = [
        m for m in movies.get('movies', [])
        if 0 < m['resume']['position'] < m['resume']['total']
    ]

    next_up = []
    for show in shows.get('tvshows', []):
        eps = call_rpc('VideoLibrary.GetEpisodes', {
            'tvshowid': show['tvshowid'],
            'filter': {
                'and': [
                    {'field': 'playcount', 'operator': 'is', 'value': "0"},
                    {'field': 'season', 'operator': 'greaterthan', 'value': "0"}
                ]
            },
            'sort': {'order': 'ascending', 'method': 'episode'},
            'properties': [
                'title',
                'season',
                'episode',
                'firstaired',
                'studio',
                'playcount',
                'resume',
                'streamdetails',
                'plot'
            ],
            'limits': {'start': 0, 'end': 1}
        }).get('episodes', [])

        candidate = None
        for e in eps:
            if 0 < e['resume']['position'] < e['resume']['total']:
                candidate = e
                break
            if e['playcount'] == 0:
                candidate = e
                break

        if candidate:
            candidate['show_title'] = show['title']
            candidate['art'] = show['art']
            candidate['mpaa'] = show['mpaa']
            next_up.append(candidate)

    for movie in filtered_movies:
        li = xbmcgui.ListItem(label=movie["label"])
        li.setArt(movie["art"])
        videoinfo = li.getVideoInfoTag()
        videoinfo.setTitle(movie["title"])
        videoinfo.setYear(movie["year"])
        videoinfo.setStudios(movie["studio"])
        videoinfo.setPlot(movie["plot"])
        videoinfo.setMpaa(movie["mpaa"])
        videoinfo.setGenres(movie["genre"])
        videoinfo.setDuration(movie["streamdetails"]["video"][0]["duration"])
        
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=movie["title"],
            listitem=li,
            isFolder=False
        )

    for episode in next_up:
        li = xbmcgui.ListItem(label=episode["label"])
        li.setArt(episode["art"])
        videoinfo = li.getVideoInfoTag()
        videoinfo.setTitle(episode["show_title"])
        videoinfo.setSeason(episode["season"])
        videoinfo.setEpisode(episode["episode"])
        videoinfo.setPremiered(episode["firstaired"])
        videoinfo.setStudios(episode["studio"])
        videoinfo.setPlot(episode["plot"])
        videoinfo.setMpaa(episode["mpaa"])
        videoinfo.setDuration(episode["streamdetails"]["video"][0]["duration"])
        videoinfo.setResumePoint(episode["resume"]["position"], episode["resume"]["total"])
        li.setProperty("EpisodeTitle", episode["title"])
        
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=episode["title"],
            listitem=li,
            isFolder=False
        )

    #todo: sort according to last played

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
    elif method == 'yoga_with_adriene':
        list_yoga_with_adriene()