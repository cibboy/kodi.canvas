Wishlist:
- TV show theme: play once (or in a loop with some pause between plays)
- Try to capture more events where Kodi is idiotic and tries to navigate the media library not from setting and move to home
- Preload next episode in player, so play next screen shows it immediately
- Hide play icon in play next when not highlighted
- BUG: play something with clearlogo (open OSD to be sure), then play something from file manager: previous clearlogo is used in OSD (might be the one from home, though)
- BUG: play something from file manager, use back, video continues in background because there's no onload trapping to move to "play next" (which stops if < 90%)
- Total review of onhover of media elements:
	- Real debouce
	- Maintain old clearlogo, fanart, blur and text color until load of new element completes or timeout (1s? 1.5s? timeout = fallbacks, except for fanart), whichever comes first (but if timeout is first, then load completes, new info MUST appear after fallback); must work also across window changes, so these info must be stored in skin vars or vars (careful on navigating to episode list, as th focus might be on the wrong element initially... ugh, it's a mess!)

TODO:
- Version bump to 2.0.0
- continue watching should consider items watched but also with time left
- variable accent color needs some work, especially for legibility of text in tags
- could use some VERY light tint (of accent color) over blur bg
- goto episode in custom medianav should not re-run when coming back from player (or, better, should run only if coming from home, so use window property set/reset on home?)
- Quando si va in medianav episodi, anche se la lista è nascosta finché non ha finito la selezione dell'episodio corretto, i dettagli dell'episodio sbagliato potrebbero essere caricarti e visualizzati, soprattutto su Shield che è più lento.

BUGS:
- medianav for movies not working
- previous/next season from episode nav not working when there are no more episodes (it shows the indicator, and the action moves to a ?random? season)
- no limit on title for play next (on long titles it can overlap image)

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