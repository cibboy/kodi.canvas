import xbmcplugin
from utils import *
from media import *

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
