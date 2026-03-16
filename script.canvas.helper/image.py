import io, os, json, colorsys
import xbmc, xbmcvfs
import urllib.request as urllib
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageFilter, ImageColor, ImageChops

# Default colors.
DEFAULT_COLORS = {
    'accent': 'E5A00D',
    'contrast': 'DEDEDE',
    'contrast_light': 'DEDEDE',
    'contrast_dark': '212121'
}

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

# Darken an image by an amount.
def darken_subtract(img, amount):
    """
    Darken by subtracting a constant amount from each channel.
    amount: integer 0..255
    """
    mask = Image.new("RGB", img.size, (amount, amount, amount))
    return ImageChops.subtract(img, mask, scale=1.0, offset=0)  # clips at 0

# Gets the most suitable color for text, given the background image (blurred).
def get_best_contrast_color(img):
    pixels = list(img.getdata())

    # Get an RGB array of candidate text colors.
    candidates = {
        "light": ImageColor.getrgb(f"#{DEFAULT_COLORS['contrast_light']}"),
        "dark": ImageColor.getrgb(f"#{DEFAULT_COLORS['contrast_dark']}")
    }

    # Darken the image, as the final background will have an overlay
    pixels = list(darken_subtract(img, 0).getdata())
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
    return candidates[best[0]]

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
        found = True
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
                    found = False
                
        # If not found, try one last move: use the imgPath path.
        if not found:
            if imgPath.endswith('.jpg'):
                full_path = imgPath
                thumb = thumb + '.jpg'
            elif imgPath.endswith('.png'):
                full_path = imgPath
                thumb = thumb + '.png'
            elif imgPath.endswith('.jpeg'):
                full_path = imgPath
                thumb = thumb + '.jpeg'
            else:
                return

        return (full_path, thumb)
    except:
        return

# RGB to HSL conversion.
def rgb_to_hsl(r, g, b):
    r_, g_, b_ = r/255.0, g/255.0, b/255.0
    mx = max(r_, g_, b_); mn = min(r_, g_, b_)
    l = (mx + mn) / 2
    if mx == mn:
        h = s = 0.0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r_:
            h = (g_ - b_) / d + (6 if g_ < b_ else 0)
        elif mx == g_:
            h = (b_ - r_) / d + 2
        else:
            h = (r_ - g_) / d + 4
        h /= 6
    return h, s, l

# HSL to RGB conversion.
def hsl_to_rgb(h, s, l):
    if s == 0:
        r = g = b = int(round(l * 255))
        return r, g, b

    def hue2rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    q = l + s - l * s if l >= 0.5 else l * (1 + s)
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1/3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1/3)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))

# Boosts saturation and lightness of a color, with caps.
def boost_color(rgb, min_sat=0.25, max_sat=0.5, min_light=0.4, max_light=0.6):
    """
    Ensure color is saturated and light enough for accent use.
    - rgb: (r,g,b) 0..255
    - min_sat: minimum saturation (0..1)
    - min_light/max_light: acceptable lightness range (0..1)
    """
    h, s, l = rgb_to_hsl(*rgb)
    # Increase saturation if below threshold
    if s < min_sat:
        s = min(1.0, min_sat + (s * 0.5))  # boost toward min_sat, preserve some original
    # Raise lightness into target range
    if l < min_light:
        l = min_light
    elif l > max_light:
        l = max_light
    # Hard cap saturation
    s = min(s, max_sat)
    return hsl_to_rgb(h, s, l)

# Retrieves the perceptual dominant color of an image, boosting its minimum saturation and lightness (both capped).
def dominant_color_perceptual(image, reduce_bits=5, ignore_gray=True):
    """
    Returns dominant RGB tuple biased toward perceptual chroma (hue) rather than raw brightness.
    - reduce_bits: bits to keep per channel (1..8). Lower groups similar colors.
    - white_lum_threshold: RGB luminance above which a pixel is considered near-white (0..255).
    - ignore_white: if True, near-white pixels are downweighted (helps gradients to white).
    """
    img = image.convert("RGB")
    pixels = list(img.getdata())
    if not pixels:
        return (150, 150, 150)

    shift = 8 - max(1, min(8, reduce_bits))
    bins = defaultdict(lambda: {"count": 0, "r_sum": 0, "g_sum": 0, "b_sum": 0, "chroma_sum": 0.0})
    for (r, g, b) in pixels:
        rr, gg, bb = (r >> shift, g >> shift, b >> shift)
        key = (rr, gg, bb)
        bins[key]["count"] += 1
        bins[key]["r_sum"] += r
        bins[key]["g_sum"] += g
        bins[key]["b_sum"] += b

    # Scoring using HSV saturation and chroma
    best_key = None
    best_score = -1.0
    min_sat = 0.12      # raised floor to ignore more desaturated colors
    min_chroma = 12.0   # in 0..255 space: require at least this chroma (max-min) to accept
    alpha = 0.03        # controls white/gray penalization strength
    for k, v in bins.items():
        count = v["count"]
        avg_r = v["r_sum"] / count
        avg_g = v["g_sum"] / count
        avg_b = v["b_sum"] / count

        # Normalize for colorsys (0..1)
        rn, gn, bn = avg_r / 255.0, avg_g / 255.0, avg_b / 255.0
        h, s, vv = colorsys.rgb_to_hsv(rn, gn, bn)

        # Compute luminance and chroma (0..255)
        lum = 0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b
        lum_norm = lum / 255.0
        chroma = max(avg_r, avg_g, avg_b) - min(avg_r, avg_g, avg_b)

        # Hard skip: treat near-grayscale as ignored
        if s < min_sat or chroma < min_chroma:
            continue

        # Gray/white penalty: strong when both saturation and chroma are low and luminance high
        white_factor = 1.0
        if ignore_gray:
            grayness = (1.0 - s) * (1.0 - (chroma / 255.0))  # 0 for saturated, 1 for grayscale
            white_factor = max(0.01, 1.0 - (lum_norm ** alpha) * grayness)

        score = count * (s ** 1.5) * white_factor

        if score > best_score:
            best_score = score
            best_key = k

    # Fallback if no bin passed saturation floor: pick highest-value (brightest) bin's average
    if best_key is None:
        # pick the bin with max avg value (vv) to avoid random tinted noise
        best_key = max(bins.items(), key=lambda kv: (
            (kv[1]["r_sum"]/kv[1]["count"] +
            kv[1]["g_sum"]/kv[1]["count"] +
            kv[1]["b_sum"]/kv[1]["count"]) / 3.0
        ))[0]

    b = bins[best_key]
    count = b["count"]
    return (int(b["r_sum"] / count), int(b["g_sum"] / count), int(b["b_sum"] / count))

# Open an image and resizes it to usable dimensions if requested.
def open_usable_image(path, resize, resize_dimensions = (120, 67)):
    with xbmcvfs.File(xbmcvfs.translatePath(path), 'rb') as f:
        image_bytes = f.readBytes()
    img = Image.open(io.BytesIO(image_bytes))
    if resize:
        img = img.resize(resize_dimensions, Image.LANCZOS)

    return img

# Takes an art path, downsizes it, blurs it, saves in into temp and returns the new path.
# It avoids re-sizing, re-blurring if already in cache.
def get_blurred(imgPath):
    try:
        # Load paths.
        canvas_cache = 'special://temp/temp/canvas.blur/'
        full_path, thumb = get_image(imgPath)
        name = thumb.replace('.png', '.jpg').replace('.jpeg', '.jpg').replace('.jpg', '')
        folder = xbmcvfs.translatePath(canvas_cache)
        
        # Create folder if missing.
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Search for cached blur file. The name should be the same as Kodi's cache.
        blur_file = xbmcvfs.translatePath(canvas_cache + name + '.jpg')
        have_blur = xbmcvfs.exists(blur_file)

        # Search for color info file.
        color_file = xbmcvfs.translatePath(canvas_cache + name + '.json')
        have_color = xbmcvfs.exists(color_file)

        contrast = None
        accent = None

        # Load info from color file, if present.
        if have_color:
            with open(color_file) as f:
                colors = json.load(f)
                contrast = colors.get('contrast', None)
                accent = colors.get('accent', None)

        # If we don't have contrast/accent information, or we are missing the blur file, compute them.
        if accent is None or contrast is None or not have_blur:
            # Extract accent as dominant color of resized fanart.
            img = open_usable_image(full_path, True)
            accent = boost_color(dominant_color_perceptual(img))
            accent = '%02x%02x%02x' % accent
            # Compute best text contrast from blurred variant.
            img = img.filter(ImageFilter.GaussianBlur(radius=float(15)))
            contrast = get_best_contrast_color(img)
            contrast = '%02x%02x%02x' % contrast

            # Save blurred variant.
            img.save(blur_file, 'JPEG')
            # Save color info.
            with open(color_file, 'w') as f:
                json.dump({'contrast': contrast, 'accent': accent}, f)

        legacy = 'light'
        if contrast == DEFAULT_COLORS['contrast_dark']: legacy = 'dark'
        return (blur_file, {'contrast': contrast, 'accent': accent, 'legacy_contrast': legacy})
    except:
        return ('', {'contrast': DEFAULT_COLORS['contrast'], 'accent': DEFAULT_COLORS['accent'], 'legacy_contrast': 'light'})

# Takes an clearlogo path, crops it to the actual content, saves in into temp and returns the new path.
# It creates 2 version, the original size, cropped, and a smaller one, cropped as well.
# It avoids re-cropping if already in cache.
def get_cropped_clearlogo(imgPath):
    try:
        # Load paths.
        full_path, thumb = get_image(imgPath)
        # Compute output path from input path.
        folder = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/')
        out = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/' + thumb)
        # Create folder if missing.
        if not os.path.exists(folder): os.makedirs(folder)

        # Check if output already present. If so, use it.
        if xbmcvfs.exists(out): return out

        # Crop.
        with xbmcvfs.File(xbmcvfs.translatePath(full_path), 'rb') as f:
            image_bytes = f.readBytes()
        img = Image.open(io.BytesIO(image_bytes))
        try:
            # Errors with single channel L conversion to RGBa so catch exceptions
            img_rgba = img.convert('RGBa')
            img = img.crop(img_rgba.getbbox())
        except:
            # If we get a conversion error just try getting bounding box with current channel
            # We'll probably be okay with single channel texture since Kodi now handles these better
            img = img.crop(img.getbbox())

        # Save output.
        img.save(out, 'PNG')

        # Return output paths.
        return out
    except:
        return ''
