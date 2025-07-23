import io, os
import xbmc, xbmcvfs
import urllib.request as urllib
from PIL import Image, ImageFilter

# Searches the required image, returns its full path and potential edited cache path.
def get_image(imgPath):
    try:
        # Some paths require unquoting to get a valid cached thumb hash.
        if imgPath.startswith('image://') and not imgPath.startswith('image://music'):
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
        # Load paths.
        full_path, out = get_image(imgPath)

        # Check if output already present. If so, use it.
        if xbmcvfs.exists(out):
            return out

        # Resize and blur.
        with xbmcvfs.File(xbmcvfs.translatePath(full_path), 'rb') as f:
            image_bytes = f.readBytes()
        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((int(480), int(270)), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=float(80)))

        # Save output.
        img.save(out, 'JPEG')

        # Return output path.
        return out
    except:
        return ''

# Takes an clearlogo path, crops it to the actual content, saves in into temp and returns the new path.
# It creates 2 version, the original size, cropped, and a smaller one, cropped as well.
# It avoids re-cropping if already in cache.
def get_cropped_clearlogo(imgPath, add_small=False):
    try:
        # Load paths.
        full_path, out = get_image(imgPath)
        if add_small:
            out_small = out.replace('.png', '-small.png')
        else:
            out_small = None

        # Check if output already present. If so, use it.
        done = True
        if not xbmcvfs.exists(out):
            done = False
        if add_small and not xbmcvfs.exists(out_small):
            done = False
        if done:
            return (out, out_small)

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
        if add_small:
            width, height = img.size
            img_small = img.resize((180, int(180*height/width)), Image.LANCZOS)

        # Save output.
        img.save(out, 'PNG')
        if add_small:
            img_small.save(out_small, 'PNG')

        # Return output paths.
        return (out, out_small)
    except:
        if add_small:
            return ('', '')
        else:
            return ('', None)
