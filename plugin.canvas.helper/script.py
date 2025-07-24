import sys
import xbmcgui

#todo: actual implementation of search according to filled components
# Returns the default list ID for each page on home, taking into consideration
# potential empty lists. It DOES NOT return the currently active list for that list.
def find_home_active_id(page):
    # Home.
    if page == 'home':
        return '101'
    # Movies.
    elif page == 'movies':
        return '110'
    # TV shows.
    elif page == 'tvshows':
        return '120'
    # TV shows.
    elif page == 'yoga':
        return '130'
    # Music.
    elif page == 'music':
        return '140'
    # Pictures.
    elif page == 'pictures':
        return '150'

# When changing the focused item in the home menu.
def onchange_home_menu(page):
    # Highlighting menu keeps things as they are.
    if page == 'menu':
        return

    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # For multilist page, find the list that last had focus in that page (or the default one).
    page_active_id = window.getProperty(f"Home.ActivePage.{page}")
    if page_active_id is None or page_active_id == '':
        page_active_id = find_home_active_id(page)
    page_active_id = str(page_active_id)

    # Update window properties.
    window.setProperty(f"Home.ActivePage.{page}", page_active_id)
    window.setProperty('Home.ActivePage', page)
    window.setProperty('Home.ActiveListId', page_active_id)

# When changing the focused list inside a page on home.
def onfocus_home_page_item(page, list_id):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Update window properties.
    window.setProperty(f"Home.ActivePage.{page}", str(list_id))
    window.setProperty('Home.ActivePage', page)
    window.setProperty('Home.ActiveListId', str(list_id))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]
        # Handle window property updates when changing the selected main menu item.
        if method == 'onchange_home_menu':
            onchange_home_menu(sys.argv[2])
        # Handle window property updates when focusing on a different list inside the same home page.
        elif method == 'onfocus_home_page_item':
            onfocus_home_page_item(sys.argv[2], sys.argv[3])