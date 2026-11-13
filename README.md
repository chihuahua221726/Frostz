# Frostz
Random Side Project Because We Were Bored

The games load their Unity WebGL builds from the CDN URLs in their HTML pages, so an internet connection is required.
Game pages and cover images are stored in the `Games` folder.
The catalog loads the additional game list and covers from published CDNs and serves its game pages from a raw HTML mirror, so an internet connection is required to browse those games.

The homepage web search opens in FrostZ's tabbed browser view. Tabs can be opened, switched, and closed; browser navigation uses the configured Scramjet transport when available.

`Single.file.html` is a downloadable, self-contained copy of the FrostZ app shell. `FrostZ.svg` is a compressed interactive SVG wrapper around the same generated app. The SVG inflates its embedded app in browsers that support `DecompressionStream`. Both embed the homepage styles, images, looping background video, local game pages, and Movies page. The game builds, remote game catalog, movie catalog, and streaming providers still require an internet connection.

Whenever you update `index.html`, `Effects/frostz-title.css`, `Effects/frostz-themes.css`, `Games/Apps/Movie.html`, a local game page, or a file under `Games/assets`, regenerate the standalone files:

```powershell
python "Generate SVG.py"
```

The generator embeds the homepage, local game pages, Movies page, and local game assets, then compresses the app into `FrostZ.svg`. It stops with an error rather than writing an SVG at or above 20 MB. Remote game builds, movie data, and streaming providers still need an internet connection.

Commit the regenerated `Single.file.html` and `FrostZ.svg` with the FrostZ changes so the downloadable files stay in sync.
