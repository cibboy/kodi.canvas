import sys
import xbmc, xbmcgui
from media import list_media

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
    page_active_id = window.getProperty(f"ActivePage.{page}")

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
    window.setProperty(f"ActivePage.{page}", page_active_id)
    window.setProperty('ActivePage', page)
    window.setProperty('ActiveListId', page_active_id)

# When changing the focused list inside a page on home.
def onfocus_home_page_item(page, listid):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Update window properties.
    window.setProperty(f"ActivePage.{page}", str(listid))
    window.setProperty('ActivePage', page)
    window.setProperty('ActiveListId', str(listid))

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

# Reload home status.
def reload_home():
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Pretend load on home page items, so the loading animation is smoother.
    window.setProperty('IsLoading.101', 'true')
    window.setProperty('IsLoading.102', 'true')
    window.setProperty('IsLoading.103', 'true')
    window.setProperty('IsLoading.104', 'true')

    # Update nonce to force lists to reload.
    nonce = window.getProperty('Nonce')
    if nonce is None or nonce == '': nonce = 0
    else: nonce = int(nonce)
    nonce += 1
    window.setProperty('Nonce', str(nonce))

    # Focus back to first element of menu (home).
    xbmc.executebuiltin('SetFocus(1,0)')

# Navigates to the active settings page (interface settings as fallback)
# using the last visited page from window properies.
def home_to_active_settings(page):
    if page is None or page == '':
        page = 'appearancesettings'
    
    xbmc.executebuiltin(f"ActivateWindow({page})")


# Handles onclick event on media item that requires navigating to the media details custom window.
def onclick_media_item(item_type, item_id):
    # Set properties on destination window, then navigate there.
    xbmc.executebuiltin(f"SetProperty(ItemDetails.Type,{item_type},1101)")
    xbmc.executebuiltin(f"SetProperty(ItemDetails.Id,{item_id},1101)")
    xbmc.executebuiltin('ActivateWindow(1101)')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]
        # Reload home.
        if method == 'reload_home':
            reload_home()
        # Navigates to active settings page from modal menu on home.
        elif method == 'home_to_active_settings':
            home_to_active_settings(sys.argv[2])
        # Handle window property updates when changing the selected main menu item.
        elif method == 'onchange_home_menu':
            onchange_home_menu(sys.argv[2])
        # Handle window property updates when focusing on a different list inside the same home page.
        elif method == 'onfocus_home_page_item':
            onfocus_home_page_item(sys.argv[2], sys.argv[3])
        # Handle moving up or down inside the same home page.
        elif method == 'onmove_home_page_item':
            onmove_home_page_item(sys.argv[2], sys.argv[3])
        
        # Handle onclick event on media item that requires navigating to the media details custom window.
        elif method == 'onclick_media_item':
            onclick_media_item(sys.argv[2], sys.argv[3])