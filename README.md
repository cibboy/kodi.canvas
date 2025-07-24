TOFIX:
- aggiunti genre e track audio in plugin (per genre è potenzialmente una lista, quindi bisognerà fare delle prove con ulteriore scraping e aggiornamento tag mp3, che è stata aggiunta alla details info line 2)
- albumstrip ha l'offset dalla label della strip troppo piccolo (visually compare to posterstrip)
- dettagli sotto item in albumstrip (le scritte sono troppo grandi)

TODO:
- rifare diffuse shadow (per seguire meglio i border radius più stretto che uso)
- aggiungere resolution e audio channels in info1 per video
- gestione loading liste (per cui ora c'è il supporto tramite window property)
- addon:
	- smart playlist per yoga with adriene con le stagioni (non l'attuale che è un trick)

Guidelines:
https://medium.com/you-i-tv/designing-for-10ft-ceeb202c1315

Docs:
- https://kodi.wiki/view/Skinning_Manual
- https://kodi.wiki/view/Opening_Windows_and_Dialogs
- https://kodi.wiki/view/List_of_Built_In_Controls
- https://kodi.wiki/view/InfoLabels
- https://kodi.wiki/view/Artwork/Accessing_with_skins_and_JSON-RPC
- https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d0/d3e/page__list_of_built_in_functions.html
- https://kodi.wiki/view/Smart_playlists/XSP_Method
- https://kodi.wiki/view/Party_Mode
- https://kodi.wiki/view/Artwork/Cache

- https://kodi.wiki/view/JSON-RPC_API
- https://kodi.wiki/view/JSON-RPC_API/Examples

- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python.html
- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmc.html
- https://xbmc.github.io/docs.kodi.tv/master/kodi-dev-kit/group__python__xbmcplugin.html

- https://kodi.wiki/view/Video_management
	- https://kodi.wiki/view/HOW-TO:Modify_automatic_watch_and_resume_points

<!--?xsp={"rules":{"and":[{"field":"title","operator":"is","value":["$INFO[Window(home).Property(videoinfo_encoded_title)]"]%7d]},"type":"tvshows"}-->
<!--?xsp=%7b%22rules%22%3a%7b%22and%22%3a%5b%7b%22field%22%3a%22title%22%2c%22operator%22%3a%22doesnotcontain%22%2c%22value%22%3a%5b%22Pitt%22%5d%7d%5d%7d%2c%22type%22%3a%22tvshows%22%7d-->



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