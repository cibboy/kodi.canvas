import sys, os, shutil, re, time
import xml.etree.ElementTree as ET
import xbmc, xbmcgui, xbmcvfs
from datetime import datetime
from image import get_blurred, get_cropped_clearlogo, DEFAULT_COLORS
from media import *
from utils import *

# Reset window properties about colors to defaults.
def reset_colors(window = None):
    if window is None:
        # All properties reside on home window.
        window = xbmcgui.Window(10000)

    #todo: add all
    window.setProperty('Colors.Accent.Foreground.Default',DEFAULT_COLORS['accent'])
    window.setProperty('Colors.Accent.Foreground2.Default',DEFAULT_COLORS['accent2'])
    window.setProperty('Colors.Accent.AltForeground.Default',DEFAULT_COLORS['accent_alt'])
    window.setProperty('Colors.Contrast.Foreground.Default',DEFAULT_COLORS['contrast_fg_light'])
    window.setProperty('Colors.Contrast.Highlight.Default',DEFAULT_COLORS['contrast_highlight_light'])

    window.setProperty('Colors.Accent.Foreground',DEFAULT_COLORS['accent'])
    window.setProperty('Colors.Accent.AltForeground',DEFAULT_COLORS['accent_alt'])
    window.setProperty('Colors.Contrast.Foreground',DEFAULT_COLORS['contrast_fg_light'])
    window.setProperty('Colors.Contrast.Highlight',DEFAULT_COLORS['contrast_highlight_light'])

# Returns a properly formatted string for the duration, according to requirements.
def get_duration(item_ref, hours, minutes, seconds):
    ret = ''
    added_hours = False
    added_minutes = False

    if hours is True:
        try:
            dur_h = int(xbmc.getInfoLabel(f"{item_ref}.Duration(h)"))
            if dur_h > 0:
                added_hours = True
                ret = f"{dur_h}h"
        except: pass
    if minutes is True:
        try:
            dur_m = int(xbmc.getInfoLabel(f"{item_ref}.Duration(m)"))
            dur_mm = xbmc.getInfoLabel(f"{item_ref}.Duration(mm)")
            if dur_m > 0:
                added_minutes = True
                if added_hours is True: ret = ret + f"{dur_mm}m"
                else: ret = f"{dur_m}m"
        except: pass
    if seconds is True:
        try:
            dur_s = xbmc.getInfoLabel(f"{item_ref}.Duration(s)")
            dur_ss = xbmc.getInfoLabel(f"{item_ref}.Duration(ss)")
            if added_minutes is True: ret = ret + f"{dur_ss}s"
            else: ret = f"{dur_s}s"
        except: pass

    return ret

# Clear custom listitem properties on home used for details.
def clear_listitem_properties(include_navigation = True):
    # All properties reside on home window.
    window = xbmcgui.Window(10000)

    # Clear properties.
    if include_navigation:
        window.clearProperty('Navigation.PreviousSeason')
        window.clearProperty('Navigation.NextSeason')
    window.clearProperty('Details.DBID.Debounce')
    window.clearProperty('Details.DBID')
    window.clearProperty('Details.ItemType')
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
    window.clearProperty('Details.Watched')
    window.clearProperty('Details.AllNew')
    window.clearProperty('Details.HasEngSubs')
    window.clearProperty('Details.HasItaSubs')
    reset_colors(window)

# Populate window properties with background information for the music player.
def populate_musicplayer_bg_info(thumb):
    # Work on MusicVisualisation.xml.
    window = xbmcgui.Window(12006)

    # Get blurred background.
    blur, colors = get_blurred(thumb)
    
    # Set properties.
    window.setProperty('MusicPlayer.Blur', blur)
    window.setProperty('MusicPlayer.Contrast', colors['contrast'])
    window.setProperty('MusicPlayer.Contrast.Foreground', colors['contrast_fg'])
    window.setProperty('MusicPlayer.Contrast.Highlight', colors['contrast_highlight'])

# Populate window properties with information about the requested item to be used in details.
def populate_listitem_info(window, itemtype, itemid, item_ref, find_navigation):
    if window.getProperty('Details.DoNotProcess') == 'true': return

    title = ''
    title2 = ''
    studio = ''
    video_res = ''
    video_codec = ''
    aspect_ratio = ''
    hdr_type = ''
    audio_channels = ''
    audio_channels_s1 = ''
    audio_channels_s2 = ''
    audio_lang_s1 = ''
    audio_lang_s2 = ''
    audio_codec_s1 = ''
    audio_codec_s2 = ''
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
        duration = get_duration(item_ref, True, True, False)
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.PercentPlayed")
        # Find if watched.
        try:
            # Watched is true if playcount is > 0 and we're not currently playing it.
            if int(xbmc.getInfoLabel(f"{item_ref}.PlayCount")) > 0 and time_remaining == '': watched = 'true'
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
        duration = get_duration(item_ref, True, True, False)
        # Find percentage played.
        perc_played = xbmc.getInfoLabel(f"{item_ref}.PercentPlayed")
        # Find if watched.
        try:
            pc = xbmc.getInfoLabel(f"{item_ref}.PlayCount")
            # Watched is true if playcount is > 0 and we're not currently playing it.
            if int(xbmc.getInfoLabel(f"{item_ref}.PlayCount")) > 0 and time_remaining == '': watched = 'true'
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
        duration = get_duration(item_ref, True, True, True)
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
    blur, colors = get_blurred(fanart)
    clearlogo = get_cropped_clearlogo(clearlogo_original)

    # Set properties (only if we're still working on the same item).
    current = window.getProperty('Details.DBID')
    if current == itemid:
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
        window.setProperty('Details.Contrast', colors['contrast'])
        window.setProperty('Details.Fanart', fanart)
        window.setProperty('Details.Thumb', xbmc.getInfoLabel(f"{item_ref}.Art(thumb)"))
        window.setProperty('Details.Watched', watched)
        window.setProperty('Details.AllNew', all_new)
        window.setProperty('Details.HasEngSubs', has_eng_sub)
        window.setProperty('Details.HasItaSubs', has_ita_sub)
        window.setProperty('Colors.Accent.Foreground', colors['accent'])
        window.setProperty('Colors.Accent.AltForeground', colors['accent_alt'])
        window.setProperty('Colors.Contrast.Foreground', colors['contrast_fg'])
        window.setProperty('Colors.Contrast.Highlight', colors['contrast_highlight'])

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

# Populate window properties with information about the playing
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
        # Preload next episode if this is a TV show episode
        if itemtype == 'episode':
            tvshowid = xbmc.getInfoLabel('VideoPlayer.TVShowDBID')
            season = xbmc.getInfoLabel('VideoPlayer.Season')
            episode = xbmc.getInfoLabel('VideoPlayer.Episode')
            load_nextup(tvshowid, season, episode)

# Populate window properties with information about the specified
# list ID's selected item. This allows the skin to work with information
# not exposed natively by Kodi.
# Explicitly request item type and ID because live-retrieving might fail
# in cases where a dialog appears rapidly before the xbmc.getInfoLabel()
# method can be invoked.
# "Debounced" to improve responsiveness.
def populate_listitem_info_from_listitem(listid):
    if listid != '' and listid is not None:
        # All properties reside on home window.
        window = xbmcgui.Window(10000)

        # Retrieve item type and ID.
        listitem = f"Container({listid}).ListItem"
        itemtype = xbmc.getInfoLabel(f"{listitem}.DBTYPE")
        itemid = xbmc.getInfoLabel(f"{listitem}.DBID")

        # Poor man's implementation of debouncing.
        window.setProperty('Details.DBID.Debounce', itemid)
        time.sleep(0.3)
        debounce_value = window.getProperty('Details.DBID.Debounce')
        if debounce_value == itemid:    # Continue if there were no new requests.
            # Retrieve current active item ID.
            active_itemid = window.getProperty('Details.DBID')
            # Continue if working with a different item. This prevents trying to
            # access information with xbmc.getInfoLabel() when a dialog appeared
            # above the window where we are trying to run that method.
            if itemid != active_itemid and (itemid != '' or active_itemid == ''):
                # Set the new active item ID.
                window.setProperty('Details.DBID', itemid)
                # Populate properties.
                populate_listitem_info(window, itemtype, itemid, listitem, True)


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
        # Force sorting through xsp encoded json becauses navigating from the list of recently added episodes might not provide a sorted list by default.
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
    # First of all, signal to details renderer that no update needs to run for the time being.
    window = xbmcgui.Window(10000)
    window.setProperty('Details.DoNotProcess', 'true')

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

    # Set focus with computed offset.
    xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
    # Kodi is stupid, sometimes it says it the list has focus, but it doesn't.
    # So we need to force it again while the focused episoded is not the requested one.
    time.sleep(0.1)
    xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
    count = 0
    current = xbmcgui.getCurrentWindowId()
    if current == 11110:
        try:
            selected = int(xbmc.getInfoLabel('Container(501).ListItem.DBID'))
            while count < 10 and selected != episode:
                count += 1
                xbmc.executebuiltin(f"SetFocus(501,{offset},absolute)")
                time.sleep(1)
                current = xbmcgui.getCurrentWindowId()
                if current != 11110: break
                try: selected = int(xbmc.getInfoLabel('Container(501).ListItem.DBID'))
                except: break
        except: pass

    # Activate processing of details.
    window.clearProperty('Details.DoNotProcess')

    # Set window property to show the list (give time for animation to complete).
    time.sleep(0.2)
    xbmc.executebuiltin('SetProperty(ShowList,true,1110)')


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
                    # Set the theme flag, then play (force no repeat, just in case it was active).
                    window.setProperty('Player.PlayingTheme', 'true')
                    player.play(cache_theme, windowed=True, startpos=0)
                    xbmc.executebuiltin('PlayerControl(RepeatOff)')

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
def clear_custom_cache(type = None):
    # Retrieve folders. If found, delete them.
    blur_folder = xbmcvfs.translatePath('special://temp/temp/canvas.blur/')
    clearlogo_folder = xbmcvfs.translatePath('special://temp/temp/canvas.clearlogo/')
    theme_folder = xbmcvfs.translatePath('special://temp/temp/canvas.theme/')

    if os.path.exists(blur_folder) and (type is None or type == 'blur'):
        xbmc.log(f"Removing {blur_folder}", xbmc.LOGINFO)
        shutil.rmtree(blur_folder)
    if os.path.exists(clearlogo_folder) and (type is None or type == 'clearlogo'):
        xbmc.log(f"Removing {clearlogo_folder}", xbmc.LOGINFO)
        shutil.rmtree(clearlogo_folder)
    if os.path.exists(theme_folder) and (type is None or type == 'theme'):
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
            if len(sys.argv) > 2: clear_custom_cache(sys.argv[2])
            else: clear_custom_cache()
        
        # Get info from player media for skin usage.
        elif method == 'populate_listitem_info_from_player':
            populate_listitem_info_from_player()
        # Get info from media for skin usage.
        elif method == 'populate_listitem_info_from_listitem':
            populate_listitem_info_from_listitem(sys.argv[2])
        # Get background info for music player.
        elif method == 'populate_musicplayer_bg_info':
            populate_musicplayer_bg_info(sys.argv[2])
        # Reset window properties about colors to defaults.
        elif method == 'reset_colors':
            reset_colors()

        # Clear custom listitem properties on home used for details.
        elif method == 'clear_listitem_properties':
            clear_listitem_properties()
        
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
