import io, os, json, colorsys
import xbmc, xbmcvfs
import urllib.request as urllib
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageFilter, ImageColor, ImageChops

# Default colors.
DEFAULT_COLORS = {
    'accent': 'E5A00D',
    'accent2': 'B67F09',
    'accent_alt': '7B5C1B',
    'contrast_fg_light': 'DEDEDE',
    'contrast_highlight_light': 'F1F1F1',
    'contrast_fg_dark': '212121',
    'contrast_highlight_dark': '0E0E0E'
}

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

# Open an image and resizes it to usable dimensions if requested.
def open_usable_image(path, resize, resize_dimensions = (120, 67)):
    with xbmcvfs.File(xbmcvfs.translatePath(path), 'rb') as f:
        image_bytes = f.readBytes()
    img = Image.open(io.BytesIO(image_bytes))
    if resize:
        img = img.resize(resize_dimensions, Image.LANCZOS)

    return img

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

# Weight hues by perceptual salience. Warm colors (red, orange, pink) are more visually dominant.
def get_hue_salience(h):
    # h is 0..1 (0=red, 0.33=green, 0.66=blue, 1=red)
    if h < 0.05 or h > 0.95:  # Red range
        return 1.3
    elif 0.05 <= h < 0.15:    # Red-orange range
        return 1.25
    elif 0.15 <= h < 0.3:     # Orange-yellow range
        return 1.15
    elif 0.3 <= h < 0.5:      # Green range
        return 0.9
    elif 0.5 <= h < 0.65:     # Blue range (pure blue)
        return 0.85
    elif 0.65 <= h < 0.8:     # Blue-purple range
        return 0.55
    else:                      # Purple range (0.8-1.0)
        return 0.5

# Extracts the dominant color from an image.
def dominant_color_perceptual(image, reduce_bits=5, ignore_gray=True):
    img = image.convert("RGB")
    pixels = list(img.getdata())
    if not pixels:
        return (150, 150, 150)

    # Compute average image color (background baseline)
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    
    shift = 8 - max(1, min(8, reduce_bits))
    bins = defaultdict(lambda: {"count": 0, "r_sum": 0, "g_sum": 0, "b_sum": 0})
    
    for (r, g, b) in pixels:
        rr, gg, bb = (r >> shift, g >> shift, b >> shift)
        key = (rr, gg, bb)
        bins[key]["count"] += 1
        bins[key]["r_sum"] += r
        bins[key]["g_sum"] += g
        bins[key]["b_sum"] += b

    best_key = None
    best_score = -1.0
    min_sat = 0.12
    min_chroma = 12.0
    alpha = 0.03
    
    for k, v in bins.items():
        count = v["count"]
        avg_r_bin = v["r_sum"] / count
        avg_g_bin = v["g_sum"] / count
        avg_b_bin = v["b_sum"] / count

        rn, gn, bn = avg_r_bin / 255.0, avg_g_bin / 255.0, avg_b_bin / 255.0
        h, s, vv = colorsys.rgb_to_hsv(rn, gn, bn)

        lum = 0.299 * avg_r_bin + 0.587 * avg_g_bin + 0.114 * avg_b_bin
        lum_norm = lum / 255.0
        chroma = max(avg_r_bin, avg_g_bin, avg_b_bin) - min(avg_r_bin, avg_g_bin, avg_b_bin)

        if s < min_sat or chroma < min_chroma:
            continue

        white_factor = 1.0
        if ignore_gray:
            grayness = (1.0 - s) * (1.0 - (chroma / 255.0))
            white_factor = max(0.01, 1.0 - (lum_norm ** alpha) * grayness)

        # Contrast against image average
        delta_r = abs(avg_r_bin - avg_r)
        delta_g = abs(avg_g_bin - avg_g)
        delta_b = abs(avg_b_bin - avg_b)
        contrast = (delta_r + delta_g + delta_b) / 3.0  # 0..255
        contrast_norm = contrast / 255.0

        # Combine: area * saturation * contrast * hue_salience
        score = (count ** 0.6) * (s ** 0.8) * (contrast_norm ** 1.2) * white_factor * get_hue_salience(h)

        if score > best_score:
            best_score = score
            best_key = k

    if best_key is None:
        best_key = max(bins.items(), key=lambda kv: (
            (kv[1]["r_sum"]/kv[1]["count"] +
            kv[1]["g_sum"]/kv[1]["count"] +
            kv[1]["b_sum"]/kv[1]["count"]) / 3.0
        ))[0]

    b = bins[best_key]
    count = b["count"]
    return (int(b["r_sum"] / count), int(b["g_sum"] / count), int(b["b_sum"] / count))

# Generate multiple accent colors for different UI contexts.
def generate_ui_accents(rgb, overlay_opacity=0.3):
    def normalize_saturation(s, target_range=(0.35, 0.65)):
        """
        Remap saturation to a target range.
        - Desaturated colors get boosted toward the range
        - Overly saturated colors get tamed
        """
        min_sat, max_sat = target_range
        
        if s < min_sat:
            # Boost weak saturation, but preserve some original character
            s = min_sat + (s * 0.3)
        elif s > max_sat:
            # Reduce overly vibrant saturation
            s = max_sat - ((s - max_sat) * 0.5)
        
        return max(0, min(1, s))  # Clamp to 0..1

    h, s, l = rgb_to_hsl(*rgb)
    
    # Adjust base target lightness based on overlay darkness
    # Heavier overlay = need brighter accent
    base_lightness = 0.75 + (overlay_opacity * 0.1)  # 0.75–0.85 range
    base_lightness = min(base_lightness, 0.9)  # Cap at 0.9
    
    # Normalize saturation: boost weak colors, tame overly vibrant ones
    normalized_sat = normalize_saturation(s, target_range=(0.35, 0.65))
    
    return {
        'foreground': hsl_to_rgb(h, normalized_sat * 0.6, base_lightness - 0.15),
        'alternate': hsl_to_rgb(h, normalized_sat * 0.4, base_lightness - 0.45),
    }

# Extract color information from image for best text contrast over that image.
def get_contrast_color_info(img, overlay_darkness=0.4):
    # Calculate WCAG contrast ratio.
    def contrast_ratio(lum1, lum2):
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

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
    
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    
    avg_lum = relative_luminance((avg_r, avg_g, avg_b))
    
    # Simulate the overlay effect: darken the luminance
    # Overlay works by blending with black.
    simulated_lum = avg_lum * (1.0 - overlay_darkness)

    white_lum = 1.0  # White is always luminance 1.0
    black_lum = 0.0  # Black is always luminance 0.0
    
    white_contrast = contrast_ratio(simulated_lum, white_lum)
    black_contrast = contrast_ratio(simulated_lum, black_lum)
    
    # Choose the text color with better contrast
    if white_contrast > black_contrast:
        if white_contrast - black_contrast < 1.0: return {'base': 'light', 'darken_bg': True}
        else: return {'base': 'light', 'darken_bg': False} 
    else:
        if black_contrast - white_contrast < 2.0: return {'base': 'light', 'darken_bg': True}
        else: return {'base': 'dark', 'darken_bg': False}

# Extracts color information from images. Uses cached information, if present.
def get_colors(cache_name, img_path, blur_path):
    try:
        # Load paths.
        canvas_cache = 'special://temp/temp/canvas.color/'
        folder = xbmcvfs.translatePath(canvas_cache)

        # Create folder if missing.
        if not os.path.exists(folder):
            os.makedirs(folder)

        contrast = None
        needs_darken_bg = False
        dominant = None

        # Search for color info file.
        color_file = xbmcvfs.translatePath(canvas_cache + cache_name + '.json')
        # Load info from color file, if present.
        if xbmcvfs.exists(color_file):
            with open(color_file) as f:
                color_info = json.load(f)
                contrast = color_info.get('contrast', None)
                needs_darken_bg = color_info.get('needs_darken_bg', False)
                dominant_hex = color_info.get('dominant', None)
                dominant = ImageColor.getrgb(f"#{dominant_hex}")

        # If we don't have color information, compute it.
        if dominant is None or contrast is None:
            # Extract accent as dominant color of resized fanart.
            img = open_usable_image(img_path, True)
            dominant = dominant_color_perceptual(img)
            # Compute best text contrast from blurred variant.
            img = open_usable_image(blur_path, False)
            info = get_contrast_color_info(img)
            contrast = info['base']
            #todo: darken_bg

            # Save color info.
            with open(color_file, 'w') as f:
                json.dump({'contrast': contrast, 'needs_darken_bg': needs_darken_bg, 'dominant': '%02x%02x%02x' % dominant}, f)

        # Further modify dominant color to extract accent colors.
        accents = generate_ui_accents(dominant)
        accents_fg = accents['foreground']
        accent_alt = accents['alternate']
        accent_fg_hex = '%02x%02x%02x' % accents_fg
        accent_alt_hex = '%02x%02x%02x' % accent_alt

        # Real contrast colors.
        if contrast == 'light':
            contrast_fg_hex = DEFAULT_COLORS['contrast_fg_light']
            contrast_highlight_hex = DEFAULT_COLORS['contrast_highlight_light']
        else:
            contrast_fg_hex = DEFAULT_COLORS['contrast_fg_dark']
            contrast_highlight_hex = DEFAULT_COLORS['contrast_highlight_dark']
        #todo: add bg darkening info

        return {
            'contrast': contrast,
            'contrast_fg': contrast_fg_hex,
            'contrast_highlight': contrast_highlight_hex,
            'accent': accent_fg_hex,
            'accent_alt': accent_alt_hex
        }   #todo: add bg darkening info
    except Exception as t:
        xbmc.log(str(t),xbmc.LOGINFO)
        xbmc.log(str(t.__traceback__.tb_lineno),xbmc.LOGINFO)
        return {
            'contrast': 'light',
            'contrast_fg': DEFAULT_COLORS['contrast_fg_light'],
            'contrast_highlight': DEFAULT_COLORS['contrast_highlight_light'],
            'accent': DEFAULT_COLORS['accent'],
            'accent_alt': DEFAULT_COLORS['accent_alt']
        }   #todo: add bg darkening info


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

        # Search for cached blur file. The name should be the same as Kodi's cache (consider v1 cases as well).
        blur_file = xbmcvfs.translatePath(canvas_cache + name + '.jpg')
        if not xbmcvfs.exists(blur_file): blur_file = xbmcvfs.translatePath(canvas_cache + name + '-l.jpg')
        if not xbmcvfs.exists(blur_file): blur_file = xbmcvfs.translatePath(canvas_cache + name + '-d.jpg')

        if not xbmcvfs.exists(blur_file):
            blur_file = xbmcvfs.translatePath(canvas_cache + name + '.jpg')
            img = open_usable_image(full_path, True)
            img = img.filter(ImageFilter.GaussianBlur(radius=float(15)))
            # Save blurred variant.
            img.save(blur_file, 'JPEG')

        return blur_file, name
    except:
        return '', ''

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
