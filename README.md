# Frostz
Random Side Project Because We Were Bored

The games load their Unity WebGL builds from the CDN URLs in their HTML pages, so an internet connection is required.
Game pages and cover images are stored in the `Games` folder.
The catalog loads the additional game list and covers from published CDNs and serves its game pages from a raw HTML mirror, so an internet connection is required to browse those games.

The homepage web search opens in FrostZ's tabbed browser view. Tabs can be opened, switched, and closed; browser navigation uses the configured Scramjet transport when available.

`Single.file.html` is a downloadable, self-contained copy of the FrostZ app shell. `FrostZ.svg` contains a compressed archive of the repository's source files, opens the app from those embedded files, and offers the archive for download. Generated `FrostZ.svg` and `Single.file.html` files, Git metadata, temporary files, Python caches, and installed `node_modules` are excluded from the archive. The SVG must remain under 20 MB. Remote game builds, catalog data, and streaming providers still require an internet connection.

Whenever you update a repository source file, regenerate the standalone files:

```powershell
python "Generate SVG.py"
```

Commit the regenerated `Single.file.html` and `FrostZ.svg` with the FrostZ changes so the downloadable files stay in sync.
