TOFIX:
- empty list "add content" button on home needs ACTION
- home flyout menu: mettere VideoLibrary.Clean?
- ricerca todo e sistemarli
- videonav ogni tanto torna indietro quando ci si muove rapidamente, sulla home non sembrano esserci problemi...
- choose art not available as action, needs to be a button in dialogvideoinfo.xml, id 10 (anche id 6 per refresh utile)
- episode custom nav: show list of episodes when finished scrolling. Possibilities:
  - timer stop when not scrolling
  - alarm as onstop lungo quanto il tempo di scrolling
- attempt home rewrite with simplification:
  - one "page" per menu item
  - a page is a grouplist with always at least 1 element (a list or the empty placeholder)
  - navigation between lists is with setfocus
  - pages are inside a grouplist
  - basically reintroduce some concepts of previous implementation, but attempt to implement native navigation
  - consider Control.Message(id,message) > message: movedown, moveup (https://kodi.wiki/view/List_of_built-in_functions#GUI_control_built-in's)

TODO:
- dialog in settings da fare:
  - SettingsScreenCalibration.xml: system > display
  - DialogSettings.xml (per master lock? courtesy screen "not supported"): interface > master lock
  - DialogGameControllers.xml (courtesy screen "not supported"): system > input
  - MyVideoNav.xml: media > library > videos
  - MyMusicNav.xml: media > library > music
  - MyPics.xml: media > library > pictures
  - Generici (o quasi)
    - DialogKeyboard.xml (dove serve digitare, ad esempio system > internet > proxy > server)
    - DialogNumeric.xml (dove serve digitare numeri, ad esempio interface > master lock > activate numeric only)
    - AddonBrowser.xml: system > addons > manage dependencies
    - FileBrowser.xml (ad esempio system > logging > screenshot folder)
    - Eventlog.xml: system > logging > show event log
    - DialogAddonSettings.xml (ad esempio player > discs > encoder > setting)
- manca il caricamento della lista pictures
- creare possibilità di sbiancare la cache in temp
- ricordarsi nel setup iniziale di gestire anche advancedsettings.xml per la questione rimozione splash screen originale
- playing theme in tv shows
- constant notification on home/navigation for currently playing item (escludere theme in tv shows)

- skin settings (skinsettings) > sub of interface
- pvr, profiles, file manager
- addons (addonbrowser)
- information (systeminfo)
- event log (eventlog)

- settings changes on first run:
  - system > input > enable mouse and touch screen support: false
  - services > caching > memory size: 256MB
  - services > caching > read factor: adaptive
  - player > language > preferred audio language: eng (NON ENG US!!!!)
  - player > language > preferr default audio stream: false
  - player > language > preferred subtitle language: none
  - media > videos > default select action: resume
  - media > videos > default play action: resume
  ? media > videos > show "all items" entry: false
  - media > videos > flatten tv show seasons: never
  - media > videos > select first unwatched...: always



not in spotify:
- Always Getting Over You, Angela Ammons, American Pie 2
- Right Here, Right Now, Fatboy Slim, You've Come a Long Way, Baby
- I Like The Way You Move, Bodyrockers
in spotify:
- Wake me up, Avicii (al momento live, ma non è bella)
- Maria, Ricky Martin (c'è, ma l'altra è la versione veloce)



Guidelines:
https://medium.com/you-i-tv/designing-for-10ft-ceeb202c1315

Docs:
- https://kodi.wiki/view/Skinning_Manual
- https://kodi.wiki/view/Opening_Windows_and_Dialogs
- https://kodi.wiki/view/List_of_Built_In_Controls
- https://kodi.wiki/view/InfoLabels
- https://kodi.wiki/view/Keymap
- https://kodi.wiki/view/Artwork/Accessing_with_skins_and_JSON-RPC
- https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d0/d3e/page__list_of_built_in_functions.html
- https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d4/d8c/_skin__timers.html
- https://kodi.wiki/view/Smart_playlists/XSP_Method
- https://kodi.wiki/view/Party_Mode
- https://kodi.wiki/view/Artwork/Cache
- https://forum.kodi.tv/showthread.php?tid=299107

- https://kodi.wiki/view/JSON-RPC_API
- https://kodi.wiki/view/JSON-RPC_API/Examples

- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python.html
- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmc.html
- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmcplugin.html

- https://kodi.wiki/view/Video_management
	- https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points

<!--?xsp={"rules":{"and":[{"field":"title","operator":"is","value":["$INFO[Window.Property(videoinfo_encoded_title)]"]}]},"type":"tvshows"}-->
<!--videodb://tvshows/titles/?xsp=%7b%22rules%22%3a%7b%22and%22%3a%5b%7b%22field%22%3a%22title%22%2c%22operator%22%3a%22doesnotcontain%22%2c%22value%22%3a%5b%22Pitt%22%5d%7d%5d%7d%2c%22type%22%3a%22tvshows%22%7d-->



<variable name="TVShowOnClickActionVar">
  <value condition="String.IsEqual(ListItem.Property(node.type),target_folder)">ActivateWindow(videos,$INFO[ListItem.FilenameAndPath],return)</value>
  <value condition="Skin.HasSetting(tvshow_onclick_browse)">ActivateWindow(videos,videodb://tvshows/titles/$INFO[ListItem.DBID]/,return)</value>
  <value condition="Skin.HasSetting(tvshow_onclick_continuewatching)">PlayMedia(videodb://tvshows/titles/$INFO[ListItem.DBID]/,resume)</value>
  <value condition="Skin.HasSetting(tvshow_onclick_playfrombeginning)">PlayMedia(videodb://tvshows/titles/$INFO[ListItem.DBID]/,noresume)</value>
  <value condition="Skin.HasSetting(tvshow_onclick_playnext)">QueueMedia(videodb://tvshows/titles/$INFO[ListItem.DBID]/,playnext)</value>
  <value condition="Skin.HasSetting(tvshow_onclick_queue)">QueueMedia(videodb://tvshows/titles/$INFO[ListItem.DBID]/)</value>
  <value>ActivateWindow(videos,videodb://tvshows/titles/$INFO[ListItem.DBID]/,return)</value>
</variable>



<onClick>RunScript(script.blur_fanart,
  width=1920&height=1080&radius=15&prop=MyBlurProp
)</onClick>

<control type="image" id="5000"
         posX="0" posY="0"
         width="1280" height="720">

  <texture condition="StringLength(
    Window.Property(BlurredFanart)
  ) &gt; 0">
    $INFO[Window.Property(BlurredFanart)]
  </texture>

  <texture condition="StringLength(
    Window.Property(BlurredFanart)
  ) == 0">
    special://skin/media/default_bg.jpg
  </texture>
</control>


special://temp/blurred_fanart.jpg