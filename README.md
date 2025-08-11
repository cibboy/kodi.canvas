TOFIX:
- aggiunto genre audio in plugin (potenzialmente una lista, quindi bisognerà fare delle prove con ulteriore scraping e aggiornamento tag mp3, che è stata aggiunta alla details info line 2)
- home side menu non ha gli angoli arrotondati sul overlay perchè c'è scalediffuse su aspectratio
- bottombar mostra la studio icon prima che finisca il loading, e background stessa cosa con fanart:
  - forse risolvibile facendosi passare l'info come parametro e spostare la variabile sulla home, così è condizionale al loading

TODO:
- spostare più in basso l'inizio delle wall
- manca il caricamento della lista pictures
- estrarre la brightness dall'immagine di blur e salvare l'info in una proprietà del listitem (e nel nome dell'immagine) in modo da poter invertire il colore testo dei details e nomi strip home
  fatto solo per details (mancano label delle strip - sotto gli elementi e titolo della strip), ma non completo:
  - continue watching potrebbe non funzionare correttamente
  - quelli bright mettono testo nero, ma non dovrebbero farlo finchè il menù ha focus (perchè c'è il diffuse che scurisce molto)
  - contrast sbagliato:
    x Captain Phillips (thumb: 5ab3a880)
    x Captain America: The First Avenger (thumb: 6b136b33)
    x 27 Dresses (thumb: 44254806)
    - Memento
    - Morning Glory
    - The Lake House (thumb: 97a36aeb)
- Sorting include "The", da capire se si vuole togliere come in Plex
- creare possibilità di sbiancare la cache in temp
  - prima posizionare blur in temp/canvas.blur, clearlogo in temp/canvas.clearlogo e mp3 in temp/canvas.sound (da fare più avanti, quando si può testare il primo loading)
- capire se investire il tempo per farsi da 0 le impostazioni come Android TV usando JSON-RPC (vedi AndroidTVSettings.md)

- skin settings (skinsettings) > sub of interface?
x interface (interfacesettings)
x media library (mediasettings)
x player (playersettings)
x system (systemsettings)
x services (servicesettings)
- pvr, profiles, file manager
- addons (addonbrowser!)
- information (systeminfo)
- event log (eventlog)
- settings level, where?



not in spotify:
- Always Getting Over You, Angela Ammons, American Pie 2
- Right Here, Right Now, Fatboy Slim, You've Come a Long Way, Baby
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

<!--?xsp={"rules":{"and":[{"field":"title","operator":"is","value":["$INFO[Window.Property(videoinfo_encoded_title)]"]%7d]},"type":"tvshows"}-->
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