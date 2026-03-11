import sys, os, shutil, re, time
import xml.etree.ElementTree as ET
import xbmc, xbmcgui, xbmcvfs
from datetime import datetime
from image import get_blurred, get_cropped_clearlogo
from media import *
from utils import *

# Clear custom listitem properties on home used for additional details.
def clear_listitem_properties(include_navigation = True):
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear properties.
    if include_navigation:
        window.clearProperty('Navigation.PreviousSeason')
        window.clearProperty('Navigation.NextSeason')
    window.clearProperty('Details.Title')
    window.clearProperty('Details.Title2')
    window.clearProperty('Details.Studio')
    window.clearProperty('Details.VideoResolution')
    window.clearProperty('Details.VideoCodec')
    window.clearProperty('Details.AspectRatio')
    window.clearProperty('Details.HdrType')
    window.clearProperty('Details.AudioChannels')
    window.clearProperty('Details.Year')
    window.clearProperty('Details.EpisodeNumber')
    window.clearProperty('Details.EpisodePremiere')
    window.clearProperty('Details.NumberOfEpisodes')
    window.clearProperty('Details.Artist')
    window.clearProperty('Details.Duration')
    window.clearProperty('Details.Mpaa')
    window.clearProperty('Details.Status')
    window.clearProperty('Details.Genre')
    window.clearProperty('Details.TrackNumber')
    window.clearProperty('Details.EpisodesRemaining')
    window.clearProperty('Details.PercentagePlayed')
    window.clearProperty('Details.TimeRemaining')
    window.clearProperty('Details.Plot')
    window.clearProperty('Details.Director')
    window.clearProperty('Details.Writer')
    window.clearProperty('Details.FilePath')
    window.clearProperty('Details.Clearlogo')
    window.clearProperty('Details.Blur')
    window.clearProperty('Details.Contrast')
    window.clearProperty('Details.Fanart')
    window.clearProperty('Details.Thumb')

# Populate window properties with additional background information for the music player.
def get_musicplayer_bg_info(thumb):
    # Work on MusicVisualisation.xml.
    window = xbmcgui.Window(12006)

    # Get blurred background.
    blur, contrast = get_blurred(thumb)
    
    # Set properties.
    window.setProperty('MusicPlayer.Blur', blur)
    window.setProperty('MusicPlayer.Contrast', contrast)

# Populate window properties with information about the requested item to be used in details.
def populate_listitem_info(window, itemtype, itemid, item_ref, find_navigation):
    title = ''
    title2 = ''
    studio = ''
    video_res = ''
    video_codec = ''
    aspect_ratio = ''
    hdr_type = ''
    audio_channels = ''
    audio_channels_s1 = ''      #todo: Only on dialog info and player
    audio_channels_s2 = ''      #todo: Only on dialog info and player
    audio_lang_s1 = ''          #todo: Only on dialog info and player
    audio_lang_s2 = ''          #todo: Only on dialog info and player
    audio_codec_s1 = ''         #todo: Only on dialog info and player
    audio_codec_s2 = ''         #todo: Only on dialog info and player
    year = ''
    ep_number = ''
    ep_premiere = ''
    num_episodes = ''
    artist = ''
    duration = ''
    mpaa = ''
    status = ''
    genre = ''
    track_number = ''
    eps_remaining = ''
    perc_played = ''
    time_remaining = ''
    plot = ''
    director = ''
    writer = ''
    filepath = ''
    fanart = ''
    clearlogo_original = ''
    watched = 'false'
    all_new = 'false'
    has_eng_sub = 'false'
    has_ita_sub = 'false'

    # Retrieve info based on type.
    if itemtype == 'episode':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.TVShowTitle")
        title2 = xbmc.getInfoLabel(f"{item_ref}.Title")
        # Find episode-specific info.
        ep_s = xbmc.getInfoLabel(f"{item_ref}.Season")
        ep_e = xbmc.getInfoLabel(f"{item_ref}.Episode")
        ep_number = f"S{ep_s}·E{ep_e}"
        ep_premiere = xbmc.getInfoLabel(f"{item_ref}.Premiered")
        # Find duration.
        try:
            dur_h = int(xbmc.getInfoLabel(f"{item_ref}.Duration(h)"))
            dur_m = xbmc.getInfoLabel(f"{item_ref}.Duration(mm)")
            if dur_h > 0: duration = f"{dur_h}h {dur_m}m"
            else: duration = f"{dur_m}m"
        except: pass
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.PercentPlayed")
        # Find if watched.
        try:
            # Watched is true if playcount is > 0 and we're not currently playing it.
            if int(xbmc.getInfoLabel(f"{item_ref}.PlayCount") > 0) and time_remaining == '': watched = 'true'
        except: pass
        # Find subs.
        for i in range(20):
            if xbmc.getInfoLabel(f"{item_ref}.Property(SubtitleLanguage.{i+1})") == 'eng': has_eng_sub = 'true'
            elif xbmc.getInfoLabel(f"{item_ref}.Property(SubtitleLanguage.{i+1})") == 'ita': has_ita_sub = 'true'
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(season.fanart)")
        if (fanart is None or fanart == ''): fanart = xbmc.getInfoLabel(f"{item_ref}.Art(tvshow.fanart)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(tvshow.clearlogo)")
        # Find additional info not natively exposed.
        info = get_additional_episode_info(int(itemid))
        mpaa = info['mpaa']
        time_remaining = info['time_remaining']

    elif itemtype == 'season':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.TVShowTitle")
        title2 = xbmc.getInfoLabel(f"{item_ref}.Title")
        # Find year.
        year = xbmc.getInfoLabel(f"{item_ref}.Year")
        # Find season-specific info.
        eps_w = xbmc.getInfoLabel(f"{item_ref}.Property(WatchedEpisodes)")
        eps_t = xbmc.getInfoLabel(f"{item_ref}.Property(TotalEpisodes)")
        eps_remaining = f"{eps_w} of {eps_t} watched"
        try:
            num_eps_t = int(eps_t)
            if num_eps_t == 1: num_episodes = '1 episode'
            else: num_episodes = f"{num_eps_t} episodes"
            num_eps_w = int(eps_w)
            if num_eps_w == 0: all_new = 'true'
            # Watched is true if watched all episodes (and there are episodes).
            if num_eps_t == num_eps_w and num_eps_t > 0: watched = 'true'
        except: pass
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.Property(WatchedEpisodePercent)")
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(fanart)")
        if fanart is None or fanart == '': fanart = xbmc.getInfoLabel(f"{item_ref}.Art(tvshow.fanart)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(tvshow.clearlogo)")
        # Find additional info not natively exposed.
        info = get_additional_season_info(int(itemid))
        mpaa = info['mpaa']

    elif itemtype == 'tvshow':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.Title")
        # Find year.
        year = xbmc.getInfoLabel(f"{item_ref}.Year")
        # Find TV show-specific info.
        status = xbmc.getInfoLabel(f"{item_ref}.Status")
        eps_w = xbmc.getInfoLabel(f"{item_ref}.Property(WatchedEpisodes)")
        eps_t = xbmc.getInfoLabel(f"{item_ref}.Property(TotalEpisodes)")
        eps_remaining = f"{eps_w} of {eps_t} watched"
        try:
            num_eps_t = int(eps_t)
            num_eps_w = int(eps_w)
            if num_eps_w == 0: all_new = 'true'
            # Watched is true if watched all episodes (and there are episodes).
            if num_eps_t == num_eps_w and num_eps_t > 0: watched = 'true'
        except: pass
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.Property(WatchedEpisodePercent)")
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(fanart)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(clearlogo)")
        # Find additional info not natively exposed.
        info = get_additional_tvshow_info(int(itemid))
        mpaa = info['mpaa']

    elif itemtype == 'movie':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.Title")
        # Find year.
        year = xbmc.getInfoLabel(f"{item_ref}.Year")
        # Find duration.
        try:
            dur_h = int(xbmc.getInfoLabel(f"{item_ref}.Duration(h)"))
            dur_m = xbmc.getInfoLabel(f"{item_ref}.Duration(mm)")
            if dur_h > 0: duration = f"{dur_h}h {dur_m}m"
            else: duration = f"{dur_m}m"
        except: pass
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.PercentPlayed")
        # Find if watched.
        try:
            # Watched is true if playcount is > 0 and we're not currently playing it.
            if int(xbmc.getInfoLabel(f"{item_ref}.PlayCount") > 0) and time_remaining == '': watched = 'true'
        except: pass
        # Find subs.
        for i in range(20):
            if xbmc.getInfoLabel(f"{item_ref}.Property(SubtitleLanguage.{i+1})") == 'eng': has_eng_sub = 'true'
            elif xbmc.getInfoLabel(f"{item_ref}.Property(SubtitleLanguage.{i+1})") == 'ita': has_ita_sub = 'true'
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(fanart)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(clearlogo)")
        # Find additional info not natively exposed.
        info = get_additional_movie_info(int(itemid))
        mpaa = info['mpaa']
        time_remaining = info['time_remaining']

    elif itemtype == 'song':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.Title")
        title2 = xbmc.getInfoLabel(f"{item_ref}.Album")
        # Find year.
        year = xbmc.getInfoLabel(f"{item_ref}.Year")
        # Find artist.
        artist = xbmc.getInfoLabel(f"{item_ref}.Artist")
        # Find track number.
        track_number = xbmc.getInfoLabel(f"{item_ref}.TrackNumber")
        # Find duration.
        try:
            dur_h = int(xbmc.getInfoLabel(f"{item_ref}.Duration(h)"))
            dur_m = xbmc.getInfoLabel(f"{item_ref}.Duration(m)")
            dur_mm = xbmc.getInfoLabel(f"{item_ref}.Duration(mm)")
            dur_s = xbmc.getInfoLabel(f"{item_ref}.Duration(ss)")
            if dur_h > 0: duration = f"{dur_h}h {dur_mm}m {dur_s}s"
            else: duration = f"{dur_m}m {dur_s}s"
        except: pass
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.PercentPlayed")
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(thumb)")
        if fanart is None or fanart == '':
            fanart = xbmc.getInfoLabel(f"{item_ref}.Art(album.thumb)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(clearlogo)")

    elif itemtype == 'album':
        # Find titles.
        title = xbmc.getInfoLabel(f"{item_ref}.Title")
        # Find year.
        year = xbmc.getInfoLabel(f"{item_ref}.Year")
        # Find artist.
        artist = xbmc.getInfoLabel(f"{item_ref}.Artist")
        # Find fanart.
        fanart = xbmc.getInfoLabel(f"{item_ref}.Art(thumb)")
        if fanart is None or fanart == '':
            fanart = xbmc.getInfoLabel(f"{item_ref}.Art(album.thumb)")
        # Find clearlogo.
        clearlogo_original = xbmc.getInfoLabel(f"{item_ref}.Art(clearlogo)")

    # Retrieve common info.
    studio = xbmc.getInfoLabel(f"{item_ref}.Studio")
    video_res = xbmc.getInfoLabel(f"{item_ref}.VideoResolution")
    video_codec = xbmc.getInfoLabel(f"{item_ref}.VideoCodec")
    aspect_ratio = xbmc.getInfoLabel(f"{item_ref}.VideoAspect")
    hdr_type = xbmc.getInfoLabel(f"{item_ref}.HdrType").upper()
    if hdr_type == 'HDR10': hdr_type = 'HDR'
    elif hdr_type == 'DOLBYVISION': hdr_type = 'Dolby Vision'
    audio_channels = format_audio_channels(xbmc.getInfoLabel(f"{item_ref}.AudioChannels"))
    audio_channels_s1 = format_audio_channels(xbmc.getInfoLabel(f"{item_ref}.Property(AudioChannels.1)"))
    audio_channels_s2 = format_audio_channels(xbmc.getInfoLabel(f"{item_ref}.Property(AudioChannels.2)"))
    audio_lang_s1 = xbmc.getInfoLabel(f"{item_ref}.Property(AudioLanguage.1)")
    audio_lang_s2 = xbmc.getInfoLabel(f"{item_ref}.Property(AudioLanguage.2)")
    audio_codec_s1 = xbmc.getInfoLabel(f"{item_ref}.Property(AudioCodec.1)")
    audio_codec_s2 = xbmc.getInfoLabel(f"{item_ref}.Property(AudioCodec.2)")
    genre = xbmc.getInfoLabel(f"{item_ref}.Genre(comma)")
    plot = xbmc.getInfoLabel(f"{item_ref}.Plot")
    director = xbmc.getInfoLabel(f"{item_ref}.Director(comma)")
    writer = xbmc.getInfoLabel(f"{item_ref}.Writer(comma)")
    filepath = xbmc.getInfoLabel(f"{item_ref}.FileNameAndPath")

    # Get blurred background, contrast color and cropped clearlogo.
    blur, contrast = get_blurred(fanart)
    clearlogo = get_cropped_clearlogo(clearlogo_original)

    # Set properties.
    window.setProperty('Details.ItemType', itemtype)
    window.setProperty('Details.Title', title)
    window.setProperty('Details.Title2', title2)
    window.setProperty('Details.Studio', studio)
    window.setProperty('Details.VideoResolution', video_res)
    window.setProperty('Details.VideoCodec', video_codec)
    window.setProperty('Details.AspectRatio', aspect_ratio)
    window.setProperty('Details.HdrType', hdr_type)
    window.setProperty('Details.AudioChannels', audio_channels)
    window.setProperty('Details.AudioChannels.1', audio_channels_s1)
    window.setProperty('Details.AudioChannels.2', audio_channels_s2)
    window.setProperty('Details.AudioLanguage.1', audio_lang_s1)
    window.setProperty('Details.AudioLanguage.2', audio_lang_s2)
    window.setProperty('Details.AudioCodec.1', audio_codec_s1)
    window.setProperty('Details.AudioCodec.2', audio_codec_s2)
    window.setProperty('Details.Year', year)
    window.setProperty('Details.EpisodeNumber', ep_number)
    window.setProperty('Details.EpisodePremiere', ep_premiere)
    window.setProperty('Details.NumberOfEpisodes', num_episodes)
    window.setProperty('Details.Artist', artist)
    window.setProperty('Details.Duration', duration)
    window.setProperty('Details.Mpaa', mpaa)
    window.setProperty('Details.Status', status)
    window.setProperty('Details.Genre', genre)
    window.setProperty('Details.TrackNumber', track_number)
    window.setProperty('Details.EpisodesRemaining', eps_remaining)
    window.setProperty('Details.PercentagePlayed', perc_played)
    window.setProperty('Details.TimeRemaining', time_remaining)
    window.setProperty('Details.Plot', plot)
    window.setProperty('Details.Director', director)
    window.setProperty('Details.Writer', writer)
    window.setProperty('Details.FilePath', filepath)
    window.setProperty('Details.Clearlogo', clearlogo)
    window.setProperty('Details.Blur', blur)
    window.setProperty('Details.Contrast', contrast)
    window.setProperty('Details.Fanart', fanart)
    window.setProperty('Details.Thumb', xbmc.getInfoLabel(f"{item_ref}.Art(thumb)"))
    window.setProperty('Details.Watched', watched)
    window.setProperty('Details.AllNew', all_new)
    window.setProperty('Details.HasEngSubs', has_eng_sub)
    window.setProperty('Details.HasItaSubs', has_ita_sub)

    # If the container is showing the list of episodes of a season, compute previous
    # and next season path for navigation from videonav.
    if find_navigation:
        path = xbmc.getInfoLabel(f"{item_ref.replace('.ListItem', '')}.FolderPath")
        if path is None or path == '': path = xbmc.getInfoLabel('Window(1110).Property(Content)')
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

# Populate window properties with additional information about the playing
# item. It's supposed to be used on OSDs.
def populate_listitem_info_from_player():
    # All properties reside on home window.
    window = xbmcgui.Window(10000)
    # Retrieve current window.
    current_windowid = xbmcgui.getCurrentWindowId()

    # Define the active player.
    player = ''
    if current_windowid == 12005: player = 'VideoPlayer'        # VideoOSD
    elif current_windowid == 12006: player = 'MusicPlayer'      # MusicOSD

    active_itemid = window.getProperty('Player.Item.DBID')
    itemid = xbmc.getInfoLabel(f"{player}.DBID")
    itemtype = window.getProperty('Player.Item.DBTYPE')
    # Continue if working with a different item. This prevents trying to
    # access information with xbmc.getInfoLabel() when a dialog appeared
    # above the window where we are trying to run that method.
    if itemid != active_itemid and (itemid != '' or active_itemid == ''):
        # Set the new active item ID and type.
        window.setProperty('Player.Item.DBID', itemid)
        # Set the current file full path.
        window.setProperty('Player.Item.FilenameAndPath', xbmc.getInfoLabel('Player.FilenameAndPath'))
        # Populate properties.
        populate_listitem_info(window, itemtype, itemid, player, False)

# Populate window properties with additional information about the specified
# list ID's selected item. This allows the skin to work with information
# not exposed natively by Kodi.
# Explicitly request item type and ID because live-retrieving might fail
# in cases where a dialog appears rapidly before the xbmc.getInfoLabel()
# method can be invoked.
# "Debounced" to improve responsiveness.
def populate_listitem_info_from_listitem(itemtype, itemid):
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Poor man's implementation of debouncing.
    window.setProperty('Item.DBID.Debounce', itemid)
    time.sleep(0.3)
    debounce_value = window.getProperty('Item.DBID.Debounce')
    if debounce_value == itemid:    # Continue if there were no new requests.

        # Retrieve current active list ID.
        listid = window.getProperty('ActiveListId')
        
        if listid != '' and listid is not None:
            # Retrieve current active item ID.
            active_itemid = window.getProperty('Item.DBID')
            # Continue if working with a different item. This prevents trying to
            # access information with xbmc.getInfoLabel() when a dialog appeared
            # above the window where we are trying to run that method.
            if itemid != active_itemid and (itemid != '' or active_itemid == ''):
                # Set the new active item ID.
                window.setProperty('Item.DBID', itemid)
                # Populate properties.
                populate_listitem_info(window, itemtype, itemid, f"Container({listid}).ListItem", True)

# Resets selection additional information.
def reset_listitem_selection():
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear properties.
    clear_listitem_properties()
    window.clearProperty('ActiveListId')
    window.clearProperty('Item.DBID')

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
        window.setProperty(f"ActiveListId", str(result['id']))
        populate_listitem_info_from_listitem(xbmc.getInfoLabel(f"Container({result['id']}).ListItem.DBTYPE"), xbmc.getInfoLabel(f"Container({result['id']}).ListItem.DBID"))

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
    tvshowid = ''
    season = ''
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
            'playcount': count,
            'resume': {'position': 0, 'total': 0}
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
            'playcount': count,
            'resume': {'position': 0, 'total': 0}
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

    # Set window property to show the list.
    xbmc.executebuiltin('SetProperty(ShowList,true,1110)')
    # Set focus with computed offset.
    xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
    # Kodi is stupid, sometimes it says it the list has focus, but it doesn't.
    # So we need to force it again while the focused episoded is not the requested one.
    time.sleep(0.1)
    xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
    count = 0
    current = xbmcgui.getCurrentWindowId()
    if current != 11110: return
    try: selected = int(xbmc.getInfoLabel('Container(501).ListItem.DBID'))
    except: return
    while count < 10 and selected != episode:
        count += 1
        xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
        time.sleep(1)
        current = xbmcgui.getCurrentWindowId()
        if current != 11110: return
        try: selected = int(xbmc.getInfoLabel('Container(501).ListItem.DBID'))
        except: return


# Removes the requested movie/episode/season/TV show from library.
def remove_video_item(type, id, close_dialog):
    # Retrieve item path.
    path = None
    title = ''
    if type == 'movie':
        item = call_rpc('VideoLibrary.GetMovieDetails', { 'movieid': int(id), 'properties': ['file'] }).get('moviedetails', {})
        path = item.get('file', None)
        title = item.get('label', '')
    elif type == 'tvshow':
        item = call_rpc('VideoLibrary.GetTVShowDetails', { 'tvshowid': int(id), 'properties': ['file'] }).get('tvshowdetails', {})
        path = item.get('file', None)
        title = item.get('label', '')
    elif type == 'episode':
        item = call_rpc('VideoLibrary.GetEpisodeDetails', { 'episodeid': int(id), 'properties': ['file'] }).get('episodedetails', {})
        path = item.get('file', None)
        title = item.get('label', '')

    # Continue only if a path was found.
    if path is not None:
        # Ask for confirmation
        if xbmcgui.Dialog().yesno(f"Remove {type}", f"Would you really remove '{title}' from the library?"):
            xbmc.log(f"Removing {type} with ID {id}", xbmc.LOGINFO)

            # Remove item from library.
            if type == 'movie':
                call_rpc('VideoLibrary.RemoveMovie', { 'movieid': int(id) })
            elif type == 'tvshow':
                call_rpc('VideoLibrary.RemoveTVShow', { 'tvshowid': int(id) })
            elif type == 'episode':
                call_rpc('VideoLibrary.RemoveEpisode', { 'episodeid': int(id) })

            # Ask for confirmation to remove actual item.
            if xbmcgui.Dialog().yesno("Confirm delete", f"Would you like to delete the selected file(s)?\nWarning - this action can't be undone!\n{path}"):
                xbmc.log(f"Deletind item at path {path}", xbmc.LOGINFO)

                # Remove actual item.
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): shutil.rmtree(path)

            # Close dialog if requested.
            if str(close_dialog) == 'true':
                xbmc.executebuiltin('Action(Close)')


# Finds the next episode to play, if any.
def load_nextup(tvshowid, season, episode):
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear up.
    window.clearProperty('Player.NextItem.Title')
    window.clearProperty('Player.NextItem.Season')
    window.clearProperty('Player.NextItem.Episode')
    window.clearProperty('Player.NextItem.Premiered')
    window.clearProperty('Player.NextItem.Duration')
    window.clearProperty('Player.NextItem.Plot')
    window.clearProperty('Player.NextItem.Thumb')
    window.clearProperty('Player.NextItem.File')
    window.clearProperty('Player.NextItem.Present')

    ep = get_next_episode(tvshowid, season, episode)

    # Populate if found.
    if ep is not None:
        window.setProperty('Player.NextItem.Title', ep.get('title', ''))
        window.setProperty('Player.NextItem.Season', str(ep.get('season', '')))
        window.setProperty('Player.NextItem.Episode', str(ep.get('episode', '')))
        window.setProperty('Player.NextItem.Premiered', ep.get('firstaired', ''))
        window.setProperty('Player.NextItem.Plot', ep.get('plot', ''))
        window.setProperty('Player.NextItem.Thumb', ep.get('art', {}).get('thumb', ''))
        window.setProperty('Player.NextItem.File', ep.get('file', ''))
        window.setProperty('Player.NextItem.Present', 'true')
        # Direct compute of duration string.
        duration = int(ep.get('streamdetails', {}).get('video', [{}])[0].get('duration', -1))
        if duration == -1: duration = ''
        elif duration > 3600: duration = format_timespan(duration, '[H]h [m]m')
        else: duration = format_timespan(duration, '[m]m')
        window.setProperty('Player.NextItem.Duration', duration)
        # Set focus on play next. Set focus after a second, otherwise it's lost somehow...
        time.sleep(1)
        xbmc.executebuiltin('SetFocus(2)')
    else:
        # Set focus on currently playing. Set focus after a second, otherwise it's lost somehow...
        time.sleep(1)
        xbmc.executebuiltin('SetFocus(1)')


# Plays the TV show theme, if available and if allowed.
def play_show_theme():
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    tvshowid = ''

    # Attempt to retrieve TV show ID.
    path = xbmc.getInfoLabel('Container(501).FolderPath')
    if path is None or path == '': path = xbmc.getInfoLabel('Window(1110).Property(Content)')
    pattern = r"^videodb://tvshows/titles/(\d+)(?:/|$)"
    match = re.match(pattern, path)
    if match: tvshowid = match.group(1)

    # If found, look for theme mp3 file.
    if tvshowid is not None and tvshowid != '':
        # Create cache folder if missing.
        cache_folder = xbmcvfs.translatePath('special://temp/temp/canvas.theme/')
        if not os.path.exists(cache_folder): os.makedirs(cache_folder)
        
        # Check if theme already present. If not look for it in TV show folder.
        cache_theme = xbmcvfs.translatePath('special://temp/temp/canvas.theme/' + tvshowid + '.mp3')
        if not xbmcvfs.exists(cache_theme):
            # Retrieve TV show folder.
            folder = call_rpc('VideoLibrary.GetTVShowDetails', {
                'tvshowid': int(tvshowid),
                'properties': ['file']
            }).get('tvshowdetails', {}).get('file', '')

            # Look for theme.
            if folder is not None and folder != '':
                theme = folder + 'theme.mp3'
                # If found, copy it over to cache.
                if os.path.exists(theme):
                    shutil.copyfile(theme, cache_theme)

        # Play theme if available in cache and allowed to play:
        # - not already playing
        # - nothing else playing
        # - in MyVideoNav.xml (10025) or MovieEpisodeVideoNav.xml (11110)
        player = xbmc.Player()
        theme_playing = window.getProperty('Player.PlayingTheme')
        if xbmcvfs.exists(cache_theme):
            if not player.isPlaying() or (theme_playing == 'true' and player.getPlayingFile() != cache_theme):
                current = xbmcgui.getCurrentWindowId()
                if current == 10025 or current == 11110:
                    # Set the theme flag, the play in loop.
                    window.setProperty('Player.PlayingTheme', 'true')
                    player.play(cache_theme, windowed=True, startpos=0)
                    xbmc.executebuiltin('PlayerControl(RepeatOne)')

# Play the album showing in music nav.
def play_full_album(container_path):
    path = None

    # Extract actual path from container path.
    pattern = r"^musicdb://albums/(\d+)(?:/|$)"
    match = re.match(pattern, container_path)
    if match:
        path = f"musicdb://albums/{match.group(1)}"

    # Play if path is valid.
    if path is not None: xbmc.executebuiltin(f"PlayMedia({path})")

# Start a slideshow of all pictures, recursively (only first source supported).
def play_all_pictures():
    sources = call_rpc('Files.GetSources', { 'media': 'pictures' }).get('sources', [])
    if len(sources) > 0:
        dir = sources[0].get('file', None)
        if dir is not None: xbmc.executebuiltin(f"RecursiveSlideShow({dir})")


# Apply first run customizations.
def apply_customizations():
    # Change settings.
    call_rpc('Settings.SetSettingValue', {'setting': 'input.enablemouse', 'value': False})
    call_rpc('Settings.SetSettingValue', {'setting': 'filecache.memorysize', 'value': 256})
    call_rpc('Settings.SetSettingValue', {'setting': 'filecache.readfactor', 'value': 0})
    call_rpc('Settings.SetSettingValue', {'setting': 'locale.audiolanguage', 'value': 'English'})
    call_rpc('Settings.SetSettingValue', {'setting': 'locale.language', 'value': 'resource.language.en_us'})
    call_rpc('Settings.SetSettingValue', {'setting': 'locale.country', 'value': 'Central Europe'})
    call_rpc('Settings.SetSettingValue', {'setting': 'locale.shortdateformat', 'value': 'D/M/YYYY'})
    call_rpc('Settings.SetSettingValue', {'setting': 'locale.subtitlelanguage', 'value': 'none'})
    call_rpc('Settings.SetSettingValue', {'setting': 'videoplayer.preferdefaultflag', 'value': False})
    call_rpc('Settings.SetSettingValue', {'setting': 'myvideos.selectaction', 'value': 2})
    call_rpc('Settings.SetSettingValue', {'setting': 'myvideos.playaction', 'value': 1})
    call_rpc('Settings.SetSettingValue', {'setting': 'videolibrary.showallitems', 'value': False})
    call_rpc('Settings.SetSettingValue', {'setting': 'videolibrary.flattentvshows', 'value': 0})
    call_rpc('Settings.SetSettingValue', {'setting': 'videolibrary.tvshowsselectfirstunwatcheditem', 'value': 1})
    call_rpc('Settings.SetSettingValue', {'setting': 'videolibrary.updateonstartup', 'value': True})
    call_rpc('Settings.SetSettingValue', {'setting': 'musiclibrary.updateonstartup', 'value': True})
    call_rpc('Settings.SetSettingValue', {'setting': 'filelists.allowfiledeletion', 'value': True})
    call_rpc('Settings.SetSettingValue', {'setting': 'filelists.showparentdiritems', 'value': False})

    # Update advancedsettings.xml
    xml = xbmcvfs.translatePath('special://userdata/advancedsettings.xml')
    if os.path.exists(xml):
        # Load existing XML.
        tree = ET.parse(xml)
        root = tree.getroot()

        # Look for "splash" element.
        found = False
        for child in root:
            if child.tag == 'splash':
                found = True
                break

        # Add "splash" element if not found.
        if not found:
            splash = ET.SubElement(root, 'splash')
            splash.text = 'false'
            tree = ET.ElementTree(root)
            tree.write(xml, encoding="utf-8", xml_declaration=False)
    else:
        # Write file with only splash removal option.
        with open(xml, 'w') as f:
            f.writelines([
                '<advancedsettings version="1.0">\n',
                '    <splash>false</splash>\n',
                '</advancedsettings>'
            ])

# Clear custom cache (blur bg, cropped clearlogos, themes).
def clear_custom_cache():
    # Retrieve folders. If found, delete them.
    blur_folder = xbmcvfs.translatePath('special://temp/temp/canvas.blur/')
    clearlogo_folder = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/')
    theme_folder = xbmcvfs.translatePath('special://temp/temp/canvas.theme/')

    if os.path.exists(blur_folder):
        xbmc.log(f"Removing {blur_folder}", xbmc.LOGINFO)
        shutil.rmtree(blur_folder)
    if os.path.exists(clearlogo_folder):
        xbmc.log(f"Removing {clearlogo_folder}", xbmc.LOGINFO)
        shutil.rmtree(clearlogo_folder)
    if os.path.exists(theme_folder):
        xbmc.log(f"Removing {theme_folder}", xbmc.LOGINFO)
        shutil.rmtree(theme_folder)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        method = sys.argv[1]

        # Apply first run customizations.
        if method == 'apply_customizations':
            apply_customizations()
        # Clear custom cache.
        elif method == 'clear_custom_cache':
            clear_custom_cache()
        
        # Get additional info from player media for skin usage.
        elif method == 'populate_listitem_info_from_player':
            populate_listitem_info_from_player()
        # Get additional info from media for skin usage.
        elif method == 'populate_listitem_info_from_listitem':
            populate_listitem_info_from_listitem(sys.argv[2], sys.argv[3])
        # Get background info for music player.
        elif method == 'get_musicplayer_bg_info':
            get_musicplayer_bg_info(sys.argv[2])
       
        # Removes additional info previously loaded.
        elif method == 'clear_listitem_properties':
            clear_listitem_properties()
        # Resets the selection for additional media in order to remove artifacts.
        elif method == 'reset_listitem_selection':
            reset_listitem_selection()
        
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
        # Remove video item.
        elif method == 'remove_video_item':
            remove_video_item(sys.argv[2], sys.argv[3], sys.argv[4])
        
        # Finds the next episode to play, if any.
        elif method == 'load_nextup':
            load_nextup(sys.argv[2], sys.argv[3], sys.argv[4])

        # Play TV show theme, if available.
        elif method == 'play_show_theme':
            play_show_theme()
        
        # Play the album showing in music nav.
        elif method == 'play_full_album':
            play_full_album(sys.argv[2])
        
        # Start a slideshow of all pictures, recursively (only first source supported).
        elif method == 'play_all_pictures':
            play_all_pictures()
        
        # Test method.
        elif method == 'ping':
            timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            if len(sys.argv) > 2: xbmc.log(f'ping {timestamp} - {sys.argv[2]}',xbmc.LOGINFO)
            else: xbmc.log(f'ping {timestamp}',xbmc.LOGINFO)
