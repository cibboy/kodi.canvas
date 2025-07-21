import sys, io, os, time
import xbmc, xbmcvfs, xbmcgui
import urllib.request as urllib
from PIL import Image, ImageFilter

# Searches the required image, returns its full path and potential edited cache path.
def get_image(imgPath):
    try:
        # Some paths require unquoting to get a valid cached thumb hash.
        if imgPath.startswith("image://") and 'https' in imgPath:
            imgPath = urllib.unquote(imgPath.replace('image://', ''))
            if imgPath.endswith('/'):
                imgPath = imgPath[:-1]

        # Get thumbnail path in cache.
        cache = xbmcvfs.translatePath('special://profile/Thumbnails')
        thumb = xbmc.getCacheThumbName(imgPath)
        thumb = thumb[:-4]
        full_path = os.path.join(cache, thumb[0], thumb + '.jpg')
        if (xbmcvfs.exists(full_path)):
            thumb = thumb + '.jpg'
        else:
            full_path = os.path.join(cache, thumb[0], thumb + '.png')
            if (xbmcvfs.exists(full_path)):
                thumb = thumb + '.png'
            else:
                full_path = os.path.join(cache, thumb[0], thumb + '.jpeg')
                if (xbmcvfs.exists(full_path)):
                    thumb = thumb + '.jpeg'
                else:
                    return

        # Compute output path from input path.
        out = xbmcvfs.translatePath('special://temp/temp/' + thumb)

        return (full_path, out)
    except:
        return

# Takes an art path, downsizes it, blurs it, saves in into temp and returns the new path.
# It avoids re-sizing, re-blurring if already in cache.
def get_blurred(imgPath):
    try:
        # Clear background property.
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        window.clearProperty('ActiveItem.BackgroundBlur')

        # Load paths.
        full_path, out = get_image(imgPath)

        # Check if output already present. If so, use it.
        if xbmcvfs.exists(out):
            window.setProperty('ActiveItem.BackgroundBlur', out)
            return

        # Resize and blur.
        with xbmcvfs.File(xbmcvfs.translatePath(full_path), 'rb') as f:
            image_bytes = f.readBytes()
        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((int(480), int(270)), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=float(80)))

        # Save output.
        img.save(out, 'JPEG')

        # Set output path in property.
        window.setProperty('ActiveItem.BackgroundBlur', out)
    except:
        return

# Takes an clearlogo path, crops it to the actual content, saves in into temp and returns the new path.
# It creates 2 version, the original size, cropped, and a smaller one, cropped as well.
# It avoids re-cropping if already in cache.
def get_cropped_clearlogo(imgPath):
    try:
        # Clear clearlogo property.
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        window.clearProperty('ActiveItem.Clearlogo.Big')
        window.clearProperty('ActiveItem.Clearlogo.Small')

        # Load paths.
        full_path, out = get_image(imgPath)
        out_small = out.replace('.png', '-small.png')

        # Check if output already present. If so, use it.
        done = True
        if xbmcvfs.exists(out):
            window.setProperty('ActiveItem.Clearlogo.Big', out)
        else:
            done = False
        if xbmcvfs.exists(out_small):
            window.setProperty('ActiveItem.Clearlogo.Small', out_small)
        else:
            done = False
        if done:
            return

        # Crop.
        with xbmcvfs.File(xbmcvfs.translatePath(full_path), 'rb') as f:
            image_bytes = f.readBytes()
        img = Image.open(io.BytesIO(image_bytes))
        try:
            # Errors with single channel L conversion to RGBa so catch exceptions
            img_rgba = img.convert('RGBa')
            img = img.crop(img_rgba.getbbox())
        except Exception:
            # If we get a conversion error just try getting bounding box with current channel
            # We'll probably be okay with single channel texture since Kodi now handles these better
            img = img.crop(img.getbbox())

        # Resize for small version.
        width, height = img.size
        img_small = img.resize((120, int(120*height/width)), Image.LANCZOS)

        # Save output.
        img.save(out, 'PNG')
        img_small.save(out_small, 'PNG')

        # Set output path in property.
        window.setProperty('ActiveItem.Clearlogo.Big', out)
        window.setProperty('ActiveItem.Clearlogo.Small', out_small)
    except:
        return

# Return the value of infolabel, retying multiple times if not available.
def get_infolabel_with_retry(infolabel, limit=10):
    # Try to resolve unresolved infolabel.
    count = 0
    while count < limit:
        value = xbmc.getInfoLabel(infolabel)
        if value is not None and value != '':
            return value
        else:
            count += 1
            time.sleep(1)
    
    return None

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

# Returns the art property to use on home for blurring the background
# based on the active list ID.
def get_home_active_id_blur_art(active_id):
    if active_id == '104' or active_id == '140':
        return 'album.thumb'
    else:
        return 'fanart'

# Returns the art property to use on home for cropping the clearlogo
# based on the active list ID.
def get_home_active_id_clearlogo(active_id):
    if active_id == '102':
        return 'tvshow.clearlogo'
    else:
        return 'clearlogo'

# When changing the focused item in the home menu.
def home_menu_onchange(page):
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
    window.clearProperty('ActiveItem.BackgroundBlur')
    window.clearProperty('ActiveItem.Clearlogo.Big')
    window.clearProperty('ActiveItem.Clearlogo.Small')
    
    # Call blur function for the active element's reference art.
    reference_art = get_home_active_id_blur_art(page_active_id)
    blur_art = str(get_infolabel_with_retry(f"Container({page_active_id}).ListItem.Art({reference_art})"))
    get_blurred(blur_art)
    # Call clearlogo crop function for the active element.
    reference_art = get_home_active_id_clearlogo(page_active_id)
    clearlogo_art = str(get_infolabel_with_retry(f"Container({page_active_id}).ListItem.Art({reference_art})"))
    get_cropped_clearlogo(clearlogo_art)

# When changing the focused list inside a page on home.
def home_page_item_onfocus(page, list_id):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Update window properties.
    window.setProperty(f"Home.ActivePage.{page}", str(list_id))
    window.setProperty('Home.ActivePage', page)
    window.setProperty('Home.ActiveListId', str(list_id))
    window.clearProperty('ActiveItem.BackgroundBlur')
    window.clearProperty('ActiveItem.Clearlogo.Big')
    window.clearProperty('ActiveItem.Clearlogo.Small')

    #control = window.getControl(int(list_id))

    #xbmc.log('id: ' + str(list_id), xbmc.LOGINFO)
    #xbmc.log('item: ' + str(control.getSelectedItem()), xbmc.LOGINFO)

    # Call blur function for the active element's reference art.
    reference_art = get_home_active_id_blur_art(list_id)
    blur_art = str(get_infolabel_with_retry(f"Container({list_id}).ListItem.Art({reference_art})"))
    get_blurred(blur_art)
    # Call clearlogo crop function for the active element.
    reference_art = get_home_active_id_clearlogo(list_id)
    clearlogo_art = str(get_infolabel_with_retry(f"Container({list_id}).ListItem.Art({reference_art})"))
    get_cropped_clearlogo(clearlogo_art)

# When changing the focused item in a list inside a page on home.
def home_page_listitem_onchange(list_id):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

    # Update window properties.
    window.clearProperty('ActiveItem.BackgroundBlur')
    window.clearProperty('ActiveItem.Clearlogo.Big')
    window.clearProperty('ActiveItem.Clearlogo.Small')

    # Call blur function for the active element's reference art.
    reference_art = get_home_active_id_blur_art(list_id)
    blur_art = str(get_infolabel_with_retry(f"Container({list_id}).ListItem.Art({reference_art})"))
    get_blurred(blur_art)
    # Call clearlogo crop function for the active element.
    reference_art = get_home_active_id_clearlogo(list_id)
    clearlogo_art = str(get_infolabel_with_retry(f"Container({list_id}).ListItem.Art({reference_art})"))
    get_cropped_clearlogo(clearlogo_art)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]
        # Handle window property updates when changing the selected main menu item.
        if method == 'home_menu_onchange':
            home_menu_onchange(sys.argv[2])
        # Handle window property updates when focusing on a different list inside the same home page.
        elif method == 'home_page_item_onfocus':
            home_page_item_onfocus(sys.argv[2], sys.argv[3])
        # Handle window property updates when changing item in a list inside the same home page.
        elif method == 'home_page_listitem_onchange':
            home_page_listitem_onchange(sys.argv[2])