import io, os
import xbmc, xbmcvfs
import urllib.request as urllib
from PIL import Image, ImageFilter, ImageColor

# Converts an sRGB channel (0-255) to linear light (0-1).
def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

# Computes the relative lumnance of an RGB pixel.
def relative_luminance(rgb):
    r, g, b = rgb
    R = srgb_to_linear(r)
    G = srgb_to_linear(g)
    B = srgb_to_linear(b)
    return 0.2126729 * R + 0.7151522 * G + 0.0721750 * B

# Computes APCA contrast given 2 reference colors.
# APCA should be best for perceived contrast.
def apca_contrast(text_rgb, bg_rgb):
    # Constants from APCA v0.98g.
    blk_thr = 0.022
    scale_boost = 1.14
    scale_norm = 1.14
    lo_clip = 0.1

    Lt = relative_luminance(text_rgb)
    Lb = relative_luminance(bg_rgb)

    # Apply low-clip (avoid noise in near-black).
    if Lt < blk_thr:
        Lt += (blk_thr - Lt) ** 1.414
    if Lb < blk_thr:
        Lb += (blk_thr - Lb) ** 1.414

    # Contrast polarity matters in APCA.
    if abs(Lt - Lb) < lo_clip:
        return 0  # Too close to be legible.

    if Lb > Lt:
        # Dark text on light background.
        contrast = (Lb ** 0.56 - Lt ** 0.57) * scale_norm * 100
    else:
        # Light text on dark background.
        contrast = (Lb ** 0.65 - Lt ** 0.62) * scale_boost * 100

    return contrast

# Gets the most suitable color for text, given the background image (blurred).
def get_best_contrast_color(img):
    # Further downsize and get the pixels of the left 33%, top 67% of the image.
    # This is the part where most of the text will be drawn upon (the blurred
    # background is x-flipped where the details go).
    width = 64
    height = 36
    # Calculate crop boundaries.
    left = 0
    top = 0
    right = width * 0.33
    bottom = height * 0.67
    # Resize, then crop.
    res_img = img.convert("RGB").resize((width, height), Image.BILINEAR)
    res_img = res_img.crop((left, top, right, bottom))
    pixels = list(res_img.getdata())

    # Get an RGB array of candidate text colors.
    candidates = {
        "light": ImageColor.getrgb("#BEBEBE"),
        "dark": ImageColor.getrgb("#313131")
    }

    # Get contrast ratios for each candidate, using different metrics.
    quantile = 0.2
    scores = {}
    for label, color in candidates.items():
        contrasts = [apca_contrast(color, px) for px in pixels]
        contrasts.sort()
        idx = int(quantile * len(contrasts))
        scores[label] = abs(contrasts[idx])

    # Pick the best score (using p10 metric).
    best = max(scores.items(), key=lambda kv: kv[1])

    # Return best color.
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
        light = path.replace('.jpg', '-l.jpg')
        dark = path.replace('.jpg', '-d.jpg')
        # Create folder if missing.
        if not os.path.exists(folder): os.makedirs(folder)

        # Check if output already present. If so, use it.
        elif xbmcvfs.exists(light):
            return (light, 'light')
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
        color = get_best_contrast_color(img)

        # Save output and return output path according to contrast ratio.
        if color == 'light':
            img.save(light, 'JPEG')
            return (light, 'light')
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
