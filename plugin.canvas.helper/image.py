import io, os
import xbmc, xbmcvfs
import urllib.request as urllib
from PIL import Image, ImageFilter, ImageColor

# Computes luminance of an RGB value.
def relative_luminance(rgb):
    def linearize_channel(c):
        x = c / 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    
    r, g, b = rgb
    R = linearize_channel(r)
    G = linearize_channel(g)
    B = linearize_channel(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B

# Computes the contrast ratio between 2 colors.
def contrast_ratio(text_rgb, bg_rgb):
    Lt = relative_luminance(text_rgb)
    Lb = relative_luminance(bg_rgb)
    lighter = max(Lt, Lb)
    darker  = min(Lt, Lb)
    return (lighter + 0.05) / (darker + 0.05)

# Gets the most suitable color for text, given the background image (blurred).
def get_inverse_from_contrast(img):
    quantile = 0.10

    # Further downsize and get the pixels.
    res_img = img.convert("RGB").resize((64, 36), Image.BILINEAR)
    pixels = list(res_img.getdata())

    # Get an RGB array of candidate text colors
    candidates = {
        "light": ImageColor.getrgb("#AAAAAA"),  # Willingly darker than actual color, for better results in computation.
        "mid": ImageColor.getrgb("#464646"),
        "dark": ImageColor.getrgb("#313131")
    }

    # Get contrast ratios for each candidate, using different metrics.
    scores = {}
    for label, color in candidates.items():
        contrasts = [contrast_ratio(color, px) for px in pixels]
        contrasts.sort()
        idx = int(quantile * len(contrasts))
        scores[label] = {
            "p10": contrasts[idx],
            "median": contrasts[len(contrasts) // 2],
            "worst": contrasts[0],
            "best": contrasts[-1]
        }

    # Pick the best score (using p10 metric).
    best = max(scores.items(), key=lambda kv: kv[1]["p10"])

    # Return true if best color is #313131 (requires inversion).
    return best[0]

# Searches the required image, returns its full path and potential edited cache path.
def get_image(imgPath):
    try:
        # Some paths require unquoting to get a valid cached thumb hash.
        if imgPath.startswith('image://') and not imgPath.startswith('image://music') and not imgPath.startswith('image://video'):
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

        return (full_path, thumb)
    except:
        return

# Takes an art path, downsizes it, blurs it, saves in into temp and returns the new path.
# It avoids re-sizing, re-blurring if already in cache.
def get_blurred(imgPath):
    try:
        # Load paths.
        full_path, thumb = get_image(imgPath)
        # Compute output paths from input path.
        folder = xbmcvfs.translatePath('special://temp/temp/canvas.blur/')
        path = xbmcvfs.translatePath('special://temp/temp/canvas.blur/' + thumb.replace('.png', '.jpg').replace('.jpeg', '.jpg'))
        light = path.replace('.jpg', '-light.jpg')
        mid = path.replace('.jpg', '-mid.jpg')
        dark = path.replace('.jpg', '-dark.jpg')
        # Create folder if missing.
        if not os.path.exists(folder): os.makedirs(folder)

        # Check if output already present. If so, use it.
        if xbmcvfs.exists(light):
            return (light, 'light')
        elif xbmcvfs.exists(mid):
            return (mid, 'mid')
        elif xbmcvfs.exists(dark):
            return (dark, 'dark')

        # Resize and blur.
        with xbmcvfs.File(xbmcvfs.translatePath(full_path), 'rb') as f:
            image_bytes = f.readBytes()
        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((int(480), int(270)), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(radius=float(80)))

        # Compute a contrast ratio between the blurred image and reference
        # text colors, in order to understand which text color is best
        # suited against the background.
        color = get_inverse_from_contrast(img)

        # Save output and return output path according to contrast ratio.
        if color == 'light':
            img.save(light, 'JPEG')
            return (light, 'light')
        elif color == 'mid':
            img.save(mid, 'JPEG')
            return (mid, 'mid')
        elif color == 'dark':
            img.save(dark, 'JPEG')
            return (dark, 'dark')
    except:
        return ('', 'light')

# Takes an clearlogo path, crops it to the actual content, saves in into temp and returns the new path.
# It creates 2 version, the original size, cropped, and a smaller one, cropped as well.
# It avoids re-cropping if already in cache.
def get_cropped_clearlogo(imgPath, add_small=False):
    try:
        # Load paths.
        full_path, thumb = get_image(imgPath)
        # Compute output path from input path.
        folder = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/')
        out = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/' + thumb)
        if add_small: out_small = out.replace('.png', '-small.png')
        else: out_small = None
        # Create folder if missing.
        if not os.path.exists(folder): os.makedirs(folder)

        # Check if output already present. If so, use it.
        done = True
        if not xbmcvfs.exists(out): done = False
        if add_small and not xbmcvfs.exists(out_small): done = False
        if done: return (out, out_small)

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
