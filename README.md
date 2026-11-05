# Frostz
Random Side Project Because We Were Bored

The games load their Unity WebGL builds from the CDN URLs in their HTML pages, so an internet connection is required.
Game pages and cover images are stored in the `Games` folder.
The catalog loads the additional game list and covers from published CDNs and serves its game pages from a raw HTML mirror, so an internet connection is required to browse those games.

The homepage web search opens in FrostZ's tabbed browser view. Tabs can be opened, switched, and closed; browser navigation uses the configured Scramjet transport when available.

`Single.file.html` is a downloadable, self-contained copy of the FrostZ app shell. `FrostZ.svg` is an interactive SVG wrapper around the same generated app. Both embed the homepage styles, images, looping background video, local game pages, and Movies page. The game builds, remote game catalog, movie catalog, and streaming providers still require an internet connection.

Whenever you update `index.html`, `Effects/frostz-title.css`, `Effects/frostz-themes.css`, `Games/Apps/Movie.html`, a local game page, or a file under `Games/assets`, regenerate both generated files before finishing the change:

```powershell
python scripts\build_single_file.py
```

Commit the regenerated `Single.file.html` and `FrostZ.svg` with the FrostZ changes so the downloadable files stay in sync.
