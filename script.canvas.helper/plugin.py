import sys
import xbmc, xbmcplugin
from urllib.parse import urlparse, parse_qsl
from media import list_continue_watching, list_recent_episodes, list_yoga_seasons, list_single_movie, list_single_song, list_actors, list_pictures

handle = int(sys.argv[1])

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
    params = {}
    if sys.argv[2] is not None and sys.argv[2] != '':
        params = dict(parse_qsl(sys.argv[2][1:]))
    # Example result: params == {'param1': 'value1', 'param2': 'value2'}

    # Generate list.
    if method == 'continue_watching':
        list_continue_watching(handle)
    if method == 'recent_episodes':
        list_recent_episodes(handle)
    elif method == 'yoga':
        list_yoga_seasons(handle)
    elif method == 'movie':
        list_single_movie(params, handle)
    elif method == 'song':
        list_single_song(params, handle)
    elif method == 'actors':
        list_actors(params, handle)
    elif method == 'pictures':
        list_pictures(params, handle)

    # Close list.
    xbmcplugin.endOfDirectory(handle)