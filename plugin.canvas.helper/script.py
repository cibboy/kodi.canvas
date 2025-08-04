import sys
import xbmc, xbmcgui
from common import list_objects

# Given a set of IDs, find the first one with content using custom window properties.
def find_home_next_content(ids, window, hint=None):
    # If we have a hint, make sure it has content.
    if hint is not None and hint != '':
        if window.getProperty(f"List.{hint}.HasContent") == 'true':
            return hint

    # Otherwise use list of IDs in sequence to find first ID with content.
    for i in ids:
        if window.getProperty(f"List.{i}.HasContent") == 'true':
            return i
    
    return None

# Returns the active list ID for each page on home, taking into consideration
# potential empty lists. For multi-list pages, it first checks for an ID already
# set in custom property and returns it if it has content.
def find_home_active_id(page, window):
    page_active_id = window.getProperty(f"Home.ActivePage.{page}")

    # Home.
    if page == 'home':
        return find_home_next_content(['101', '102', '103', '104'], window, page_active_id)
    # Movies.
    elif page == 'movies':
        if page_active_id is not None and page_active_id != '': return page_active_id
        else: return '111'
    # TV shows.
    elif page == 'tvshows':
        if page_active_id is not None and page_active_id != '': return page_active_id
        else: return '121'
    # TV shows.
    elif page == 'yoga':
        if page_active_id is not None and page_active_id != '': return page_active_id
        else: return '131'
    # Music.
    elif page == 'music':
        if page_active_id is not None and page_active_id != '': return page_active_id
        else: return '141'
    # Pictures.
    elif page == 'pictures':
        if page_active_id is not None and page_active_id != '': return page_active_id
        else: return '151'

# When changing the focused item in the home menu.
def onchange_home_menu(page):
    # Highlighting menu keeps things as they are.
    if page == 'menu':
        return

    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Find the list that last had focus and has content in that page (or the default one).
    page_active_id = find_home_active_id(page, window)

    # Update window properties.
    window.setProperty(f"Home.ActivePage.{page}", page_active_id)
    window.setProperty('Home.ActivePage', page)
    window.setProperty('Home.ActiveListId', page_active_id)

# When changing the focused list inside a page on home.
def onfocus_home_page_item(page, listid):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Update window properties.
    window.setProperty(f"Home.ActivePage.{page}", str(listid))
    window.setProperty('Home.ActivePage', page)
    window.setProperty('Home.ActiveListId', str(listid))

# When moving up or down inside the "home" page on home.
def onmove_home_page_item(listid, direction):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    if listid == '101' and direction == 'down':
        id = find_home_next_content(['102', '103', '104'], window)
        if id is not None: xbmc.executebuiltin(f"SetFocus({id})")
    elif listid == '102':
        if direction == 'up':
            id = find_home_next_content(['101'], window)
            if id is not None: xbmc.executebuiltin(f"SetFocus({id})")
        elif direction == 'down':
            id = find_home_next_content(['103', '104'], window)
            if id is not None: xbmc.executebuiltin(f"SetFocus({id})")
    elif listid == '103':
        if direction == 'up':
            id = find_home_next_content(['102', '101'], window)
            if id is not None: xbmc.executebuiltin(f"SetFocus({id})")
        elif direction == 'down':
            id = find_home_next_content(['104'], window)
            if id is not None: xbmc.executebuiltin(f"SetFocus({id})")
    elif listid == '104' and direction == 'up':
        id = find_home_next_content(['103', '102', '101'], window)
        if id is not None: xbmc.executebuiltin(f"SetFocus({id})")

# Reset home status.
def init_home():
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Move to the first menu item to reset things, then
    # immediately to the hidden button while loading.
    xbmc.executebuiltin('SetFocus(1,0)')
    xbmc.executebuiltin('SetFocus(9999)')

    # Preload lists.
    window.setProperty('Home.IsLoading', 'true')
    list_objects('continue_watching', {'listid': 101}, 1)   # Continue watching
    list_objects('recently_added_tvshow_episodes', {'listid': 102}, 2)  # Recently added episodes
    list_objects('movies', {'listid': 103, 'sort': 'dateadded', 'order': 'descending', 'limit': 25}, 3) # Recently added movies
    list_objects('songs', {'listid': 104, 'sort': 'dateadded', 'order': 'descending', 'limit': 25}, 4)  # Recently added music
    list_objects('movies', {'listid': 110}, 10)     # All movies
    list_objects('tvshows', {'listid': 121, 'exclude': 'Yoga with Adriene'}, 20)    # All TV shows
    list_objects('seasons', {'listid': 131, 'showtitle': 'Yoga with Adriene'}, 30)  # Yoga
    list_objects('songs', {'listid': 141}, 40)      # All music
    list_objects('pictures', {'listid': 151}, 50)   # Pictures
    window.setProperty('Home.IsLoading', 'false')
    
    # Briefly set focus on the first available home item, then return to the main menu.
    # This allows to properly set focuses as well as loading the right item details
    # for when the focus is on the main menu instead of the items themeselves.
    focus = find_home_next_content(['101', '102', '103', '104'], window)
    xbmc.executebuiltin(f"SetFocus({focus},0)")
    xbmc.executebuiltin('SetFocus(1,0)')

# Opens DialogButtonMenu.xml. Equivalent to ActivateWindow(shutdownmenu), but works
# with onback from home and later using a button to move to another window.
def open_home_sidemenu():
    dialog = xbmcgui.Window(10111)  # DialogButtonMenu.xml
    dialog.show()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]
        # Reset home status.
        if method == 'init_home':
            init_home()
        # Opens side menu in home.
        elif method == 'open_home_sidemenu':
            open_home_sidemenu()
        # Handle window property updates when changing the selected main menu item.
        elif method == 'onchange_home_menu':
            onchange_home_menu(sys.argv[2])
        # Handle window property updates when focusing on a different list inside the same home page.
        elif method == 'onfocus_home_page_item':
            onfocus_home_page_item(sys.argv[2], sys.argv[3])
        # Handle moving up or down inside the same home page.
        elif method == 'onmove_home_page_item':
            onmove_home_page_item(sys.argv[2], sys.argv[3])