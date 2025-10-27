import sys, re, time
import xbmc, xbmcgui
from datetime import datetime
from image import get_blurred, get_cropped_clearlogo
from media import *

# Clear custom listitem properties on home used for additional details.
def clear_listitem_properties():
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear properties.
    window.clearProperty(f"Navigation.PreviousSeason")
    window.clearProperty(f"Navigation.NextSeason")
    window.clearProperty(f"Item.Mpaa")
    window.clearProperty(f"Item.TimeRemaining")
    window.clearProperty(f"Item.ClearlogoBig")
    window.clearProperty(f"Item.Blur")
    window.clearProperty(f"Item.Contrast")

# Populate window property with additional information about the specified
# list ID's selected item. This allows the skin to work with information
# not exposed natively by Kodi.
# Explicitly request item type and ID because live-retrieving might fail
# in cases where a dialog appears rapidly before the xbmc.getInfoLabel()
# method can be invoked.
# "Debounced" to improve responsiveness.
def get_additional_media_info_from_listitem(itemtype, itemid, currentposition = 1, sync_501 = False):
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Poor man's implementation of debouncing.
    window.setProperty('ActiveItemId.Debounce', itemid)
    time.sleep(0.25)
    debounce_value = window.getProperty('ActiveItemId.Debounce')
    if debounce_value == itemid:    # Continue if there were no new requests.
        # Sync list with ID 501 if requested (used by home that has several lists).
        if sync_501: update_hidden_active_list_position(currentposition)

        # Retrieve current active list ID.
        listid = window.getProperty('ActiveListId')
        
        if listid != '' and listid is not None:
            # Retrieve current active item ID.
            active_itemid = window.getProperty('ActiveItemId')
            # Continue if working with a different item. This prevents trying to
            # access information with xbmc.getInfoLabel() when a dialog appeared
            # above the window where we are trying to run that method.
            if itemid != active_itemid and (itemid != '' or active_itemid == ''):
                # Clear properties.
                clear_listitem_properties()
                window.setProperty('Item.ClearlogoBig', 'transparent.png')
                # Set the new active item ID.
                window.setProperty('ActiveItemId', itemid)

                # If the container is showing the list of episodes of a season, compute previous
                # and next season path for navigation from videonav.
                path = xbmc.getInfoLabel(f"Container({listid}).FolderPath")
                if path is None or path == '': path = xbmc.getInfoLabel(f"Window(1110).Property(Content)")
                pattern = r"^videodb://tvshows/titles/(\d+)/(\d+)(?:/|$)"
                match = re.match(pattern, path)
                if match:
                    tvshowid = int(match.group(1))
                    season = int(match.group(2))
                    prev = season - 1
                    next = season + 1

                    # Retrieve list of available seasons in show.
                    seasons = call_rpc('VideoLibrary.GetSeasons', {
                        'tvshowid': tvshowid,
                        'properties': ['season']
                    }).get('seasons', [])
                    
                    # Look for next/previous season among those available.
                    # If found, set window property.
                    for s in seasons:
                        if s.get('season', None) == prev:
                            window.setProperty('Navigation.PreviousSeason', f"videodb://tvshows/titles/{tvshowid}/{prev}/")
                        elif s.get('season', None) == next:
                            window.setProperty('Navigation.NextSeason', f"videodb://tvshows/titles/{tvshowid}/{next}/")

                # Retrieve art based on type.
                if itemtype == 'episode':
                    # Find fanart.
                    fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(season.fanart)")
                    if (fanart is None or fanart == ''): fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(tvshow.fanart)")
                    # Find clearlogo.
                    clearlogo_original = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(tvshow.clearlogo)")
                elif itemtype == 'season':
                    # Find fanart.
                    fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(fanart)")
                    if (fanart is None or fanart == ''): fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(tvshow.fanart)")
                    # Find clearlogo.
                    clearlogo_original = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(tvshow.clearlogo)")
                elif itemtype == 'song':
                    # Find fanart.
                    fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(thumb)")
                    # Find clearlogo.
                    clearlogo_original = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(clearlogo)")
                else:
                    # Find fanart.
                    fanart = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(fanart)")
                    # Find clearlogo.
                    clearlogo_original = xbmc.getInfoLabel(f"Container({listid}).ListItem.Art(clearlogo)")

                # Get blurred background, contrast color and cropped clearlogo.
                blur, contrast = get_blurred(fanart)
                clearlogo = get_cropped_clearlogo(clearlogo_original)

                # Set properties.
                window.setProperty(f"Item.ClearlogoBig", clearlogo)
                window.setProperty(f"Item.Blur", blur)
                window.setProperty(f"Item.Contrast", contrast)

                # Retrieve type-specific additional info.
                if itemtype == 'movie':
                    info = get_additional_movie_info_from_listitem(int(itemid))
                    window.setProperty(f"Item.Mpaa", info['mpaa'])
                    window.setProperty(f"Item.TimeRemaining", info['time_remaining'])
                elif itemtype == 'tvshow':
                    info = get_additional_tvshow_info_from_listitem(int(itemid))
                    window.setProperty(f"Item.Mpaa", info['mpaa'])
                elif itemtype == 'season':
                    info = get_additional_season_info_from_listitem(int(itemid))
                    window.setProperty(f"Item.Mpaa", info['mpaa'])
                elif itemtype == 'episode':
                    info = get_additional_episode_info_from_listitem(int(itemid))
                    window.setProperty(f"Item.Mpaa", info['mpaa'])
                    window.setProperty(f"Item.TimeRemaining", info['time_remaining'])

# Resets selection additional information.
def reset_listitem_selection():
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear properties.
    clear_listitem_properties()
    window.clearProperty('ActiveListId')
    window.clearProperty('ActiveItemId')

# Updates the position of the hidden list of items that mimics the active
# one (used for details).
def update_hidden_active_list_position(position):
    # Get current window.
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Get control and set position.
    pos = int(position)
    window.getControl(501).selectItem(pos - 1)


# Navigates to the first visible candidate in the list and returns its ID and type (list or empty list placeholder).
def navigate_candidates(candidates, window):
    # Find the first available candidate, move there.
    for c in candidates:
        more = None
        # If the candidate is a dict, there is additional routing involved.
        # The component should be identified as 96{id}.
        if type(c) is dict:
            more = c['then']
            c = c['first']

        # Find the group control containing the required list ID.
        # 98{id} is for lists, 97{id} is for empty list placeholder.
        # 96{id} is a router, but rerouting must happen here to maintain
        # proper focus sequence when using side menu.
        # Keep track to type.
        control = None
        control_type = ''
        try:
            control = window.getControl(int(f"98{c}"))
            control_type = 'list'
        except:
            try:
                control = window.getControl(int(f"97{c}"))
                control_type = 'empty_placeholder'
            except:
                try:
                    control = window.getControl(int(f"96{c}"))
                    control_type = 'router'
                except:
                    control = None
                    control_type = ''

        # If the control was found and it's visible set focus to the requested control ID.
        if control is not None and control.isVisible():
            xbmc.executebuiltin(f"SetFocus({c})")

            # If additional routing is necessary, do that now.
            ret = { 'id': c, 'type': control_type }
            if more is not None: ret = navigate_candidates(more, window)
            
            # Flag visibility of empty list placeholder if found such object.
            if ret['type'] == 'empty_placeholder': window.setProperty('EmptyListPlaceholder', str(ret['id']))
            # Remove empty list placeholder flag if list found.
            else: window.clearProperty('EmptyListPlaceholder')

            return ret
    
    return { 'id': None, 'type': None }

# Performs navigation on home between lists according to availability.
def navigate_home_lists(currentid, direction):
    # Retrieve home window.
    window = xbmcgui.Window(10000)

    currentid = int(currentid)
    candidates = []

    # Each list has one or more potential next list.
    if currentid == 0:                            # Startup
        candidates = [101, 102, 103, 104, 105]
    elif currentid == 101:                        # Continue watching
        if direction == 'down': candidates = [102, 103, 104, 106, 107]
    elif currentid == 102:                        # Recent episodes
        if direction == 'down': candidates = [103, 104, 106, 107]
        else: candidates = [101]
    elif currentid == 103:                        # Recent movies
        if direction == 'down': candidates = [104, 106, 107]
        else: candidates = [102, 101]
    elif currentid == 104:                        # Recent music
        if direction == 'down': candidates = [106, 107]
        else: candidates = [103, 102, 101]
    elif currentid == 105:                        # No continue watching/recent content
        if direction == 'down': candidates = [106, 107]
    elif currentid == 106 or currentid == 107:    # Movies/no movies
        if direction == 'down': candidates = [108, 109]
        else: candidates = [104, 103, 102, 101, 105]
    elif currentid == 108 or currentid == 109:    # TV shows/no TV shows
        if direction == 'down': candidates = [110, 111]
        else: candidates = [106, 107]
    elif currentid == 110 or currentid == 111:    # Yoga/no yoga
        if direction == 'down': candidates = [112, 113]
        else: candidates = [108, 109]
    elif currentid == 112 or currentid == 113:    # Music/no music
        if direction == 'down': candidates = [{'first': 114, 'then': [302]}, 115]
        else: candidates = [110, 111]
    elif currentid == 114 or currentid == 115:    # Pictures/no pictures
        if direction == 'up': candidates = [112, 113]
    elif currentid == 302:                        # Actual full-height wall of pictures
        if direction == 'up': candidates = [{'first': 301, 'then': [112, 113]}]
    
    # Find the first available candidate, move there.
    navigate_candidates(candidates, window)

# Performs navigation on home between menu items (synchronizes lists).
def navigate_home_menu(currentid, direction):
    # Retrieve home window.
    window = xbmcgui.Window(10000)

    # Activate guard against side effects while doing movements/computations
    # (triggers on items, focus changes, background changes...)
    window.setProperty('Menu.Moving', 'true')

    currentid = int(currentid)
    candidates = []
    next = -1

    # Each item has one or more potential next list.
    if currentid == 201:    # Home
        if direction == 'down':
            candidates = [106, 107]
            next = 202
    elif currentid == 202:  # Movies
        if direction == 'down':
            candidates = [108, 109]
            next = 203
        else:
            candidates = [101, 102, 103, 104, 105]
            next = 201
    elif currentid == 203:  # TV shows
        if direction == 'down':
            candidates = [110, 111]
            next = 204
        else:
            candidates = [106, 107]
            next = 202
    elif currentid == 204:  # Yoga
        if direction == 'down':
            candidates = [112, 113]
            next = 205
        else:
            candidates = [108, 109]
            next = 203
    elif currentid == 205:  # Music
        if direction == 'up':
            candidates = [110, 111]
            next = 204
        else:
            candidates = [{'first': 114, 'then': [302]}, 115]
            next = 206
    elif currentid == 206:  # Pictures
        if direction == 'down': next = 207
        else:
            candidates = [{'first': 301, 'then': [112, 113]}]
            next = 205
    elif currentid == 207:  # Menu
        if direction == 'up': next = 206

    # Rapidly set next active menu ID, so visually there is no artifact.
    if next != -1: window.setProperty('Menu.ActiveId', str(next))
    
    # Find the first available candidate, move there to sync selection.
    result = navigate_candidates(candidates, window)

    # Then move to the next menu item.
    if next != -1: xbmc.executebuiltin(f"SetFocus({next})")

    # If a empty list placeholder candidate was found, wait a moment to let Kodi stabilize the skin, the reset info.
    if result['type'] == 'empty_placeholder':
        time.sleep(0.2)
        reset_listitem_selection()

    # If a list candidate was found, wait a moment to let Kodi stabilize the skin, then mimic item onfocus.
    if result['type'] == 'list':
        time.sleep(0.2)
        update_hidden_active_list_position(xbmc.getInfoLabel(f"Container({result['id']}).CurrentItem"))
        window.setProperty(f"ActiveListId", str(result['id']))
        get_additional_media_info_from_listitem(xbmc.getInfoLabel(f"Container({result['id']}).ListItem.DBTYPE"), xbmc.getInfoLabel(f"Container({result['id']}).ListItem.DBID"))

    # Remove the guard.
    window.clearProperty('Menu.Moving')

def navigate_home_from_menu_to_lists(currentid):
    window = xbmcgui.Window(10000)
    currentid = int(currentid)

    # Pictures might go to standard set of lists if empty or to full height list if present.
    if currentid == 206:
        try:
            control = window.getControl(98302)
            if control is not None and control.isVisible(): xbmc.executebuiltin('SetFocus(300)')
            else: xbmc.executebuiltin('SetFocus(100)')
        except:
            xbmc.executebuiltin('SetFocus(100)')
    # All the others (except menu) go to the standard set of lists.
    elif currentid != 207: xbmc.executebuiltin('SetFocus(100)')

# Prepares window properties and performs navigation for custom video nav for movies and episodes.
def navigate_movie_episode_videonav(containerid):
    # Clear up previous information, if any.
    xbmc.executebuiltin('ClearProperty(Content.Type,1110)')
    xbmc.executebuiltin('ClearProperty(Content,1110)')
    xbmc.executebuiltin('ClearProperty(Navigation.TvShowId,1110)')
    xbmc.executebuiltin('ClearProperty(Navigation.Season,1110)')
    xbmc.executebuiltin('ClearProperty(Navigation.Episode,1110)')
    xbmc.executebuiltin('ClearProperty(ShowList,1110)')

    # Retrieve info from selected item.
    type = xbmc.getInfoLabel(f"Container({containerid}).ListItem.DBTYPE")
    content = 'special://skin/playlists/empty.xsp'
    episode = ''
    if type == 'movie':
        movieid = xbmc.getInfoLabel(f"Container({containerid}).ListItem.DBID")
        content = f"plugin://script.canvas.helper/movie/?dbid={movieid}"
    elif type == 'episode':
        tvshowid = xbmc.getInfoLabel(f"Container({containerid}).ListItem.TVShowDBID")
        if tvshowid == '' or tvshowid is None: tvshowid = xbmc.getInfoLabel(f"Container({containerid}).ListItem.Property(TvShowId)")
        season = xbmc.getInfoLabel(f"Container({containerid}).ListItem.Season")
        episode = xbmc.getInfoLabel(f"Container({containerid}).ListItem.DBID")
        # Force sorting through xsp encoded json becauses navigating from the listo of recently added episodes might not provide a sorted list by default.
        content = f"videodb://tvshows/titles/{tvshowid}/{season}/?xsp=%7B%22type%22%3A%20%22episodes%22%2C%22order%22%3A%20%7B%22method%22%3A%20%22episode%22%2C%22order%22%3A%20%22ascending%22%7D%7D"

    # Set info about current item.
    xbmc.executebuiltin(f"SetProperty(Content.Type,{type},1110)")
    xbmc.executebuiltin(f"SetProperty(Content,{content},1110)")
    xbmc.executebuiltin(f"SetProperty(Navigation.TvShowId,{tvshowid},1110)")
    xbmc.executebuiltin(f"SetProperty(Navigation.Season,{season},1110)")
    xbmc.executebuiltin(f"SetProperty(Navigation.Episode,{episode},1110)")

    # Navigate to destination window.
    xbmc.executebuiltin('ActivateWindow(1110)')

# Navigates to the active settings page (interface settings as fallback)
# using the last visited page from window properies.
def navigate_home_to_active_settings(page):
    if page is None or page == '':
        page = 'appearancesettings'
    
    xbmc.executebuiltin(f"ActivateWindow({page})")

# Navigates to the specified TV show. This is necessary because simply
# replacing the window when already on MyVideoNav.xml does not work and
# requires simulating the action to go up one level.
def navigate_to_show(dbpath):
    # In on MyVideoNav.xml, go up one level.
    if xbmcgui.getCurrentWindowId() == 10025: xbmc.executebuiltin('Action(parentfolder)')
    # Else replace with window with the requested path.
    else: xbmc.executebuiltin(f"ActivateWindow(Videos,{dbpath},return)")


# Toggles watched/unwatched status on an item. Necessary due to some bug in Kodi that prevents
# the builtin action to work in the custom video nav for episodes and movies.
def toggle_watched(item_type, itemid, watched):
    count = 0
    if watched == 'true': count = 1

    # Movies.
    if item_type == 'movie':
        call_rpc('VideoLibrary.SetMovieDetails', {
            'movieid': int(itemid),
            'playcount': count
        })
    # TV shows.
    elif item_type == 'tvshow':
        call_rpc('VideoLibrary.SetTVShowDetails', {
            'tvshowid': int(itemid),
            'playcount': count
        })
    # Seasons (need to revert to builtin action, as there is no JSON-RPC call).
    elif item_type == 'season':
        xbmc.executebuiltin('Action(ToggleWatched)')
    # Episodes.
    elif item_type == 'episode':
        call_rpc('VideoLibrary.SetEpisodeDetails', {
            'episodeid': int(itemid),
            'playcount': count
        })


# When navigating to custom video nav with episodes, set the active element of
# the list to the actual episode. This function should be called by the timer
# when the list is done loading.
def set_active_episode():
    showid = -1
    season = -1
    episode = -1

    # Retrive TV show ID, season and episode DBID from window properties.
    try :
        showid = int(xbmc.getInfoLabel(f"Window(1110).Property(Navigation.TvShowId)"))
        season = int(xbmc.getInfoLabel(f"Window(1110).Property(Navigation.Season)"))
        episode = int(xbmc.getInfoLabel(f"Window(1110).Property(Navigation.Episode)"))
    except:
        showid = -1
        season = -1
        episode = -1

    offset = 0
    # If properties are there, load season episodes through JSON-RPC, then
    # find the offset of the episode from the beginning of the list.
    # Otherwise simply go to the first element.
    if showid > -1 and season > -1 and episode > -1:
        # Load list of episodes.
        episodes = call_rpc('VideoLibrary.GetEpisodes', {
            'tvshowid': showid,
            'season': season,
            # Sort by episode, ascending.
            'sort': {'order': 'ascending', 'method': 'episode'},
            # Only get DBID (included by default).
            'properties': []
        }).get('episodes', [])

        # Look for episode using DBID, use the offset.
        for i,e in enumerate(episodes):
            if e.get('episodeid', -1) == episode:
                offset = i
                break

    # Set focus with computed offset.
    xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
    # Set window property to show the list.
    xbmc.executebuiltin('SetProperty(ShowList,true,1110)')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]
        
        # Get additional info from media for skin usage.
        if method == 'get_additional_media_info_from_listitem':
            get_additional_media_info_from_listitem(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        # Removes additional info previously loaded.
        if method == 'clear_listitem_properties':
            clear_listitem_properties()
        # Resets the selection for additional media in order to remove artifacts.
        elif method == 'reset_listitem_selection':
            reset_listitem_selection()
        # Updates the position of the hidden list of items that mimics the active
        # one (used for details).
        elif method == 'update_hidden_active_list_position':
            update_hidden_active_list_position(sys.argv[2])
        # Navigate between home lists according to availability.
        elif method == 'navigate_home_lists':
            navigate_home_lists(sys.argv[2], sys.argv[3])
        # Navigate between home menu items synchronizing lists.
        elif method == 'navigate_home_menu':
            navigate_home_menu(sys.argv[2], sys.argv[3])
        # Navigate from home menu items to lists.
        elif method == 'navigate_home_from_menu_to_lists':
            navigate_home_from_menu_to_lists(sys.argv[2])
        # Navigate to custom video nav for movies and episodes.
        elif method == 'navigate_movie_episode_videonav':
            navigate_movie_episode_videonav(sys.argv[2])
        # Navigates to active settings page from modal menu on home.
        elif method == 'navigate_home_to_active_settings':
            navigate_home_to_active_settings(sys.argv[2])
        # Navigates to TV show of a specific episode.
        elif method == 'navigate_to_show':
            navigate_to_show(sys.argv[2])
        # Sets watched/unwatched status.
        elif method == 'toggle_watched':
            toggle_watched(sys.argv[2], sys.argv[3], sys.argv[4])
        # Move active element to requested episode (retrieved from window properties).
        elif method == 'set_active_episode':
            set_active_episode()

        # Test method.
        elif method == 'ping':
            timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            xbmc.log(f'ping {timestamp}',xbmc.LOGINFO)
