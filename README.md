# Frostz
Random Side Project Because We Were Bored

The games load their Unity WebGL builds from the CDN URLs in their HTML pages, so an internet connection is required.
Game pages and cover images are stored in the `Games` folder.
The catalog loads the additional game list and covers from published CDNs and serves its game pages from a raw HTML mirror, so an internet connection is required to browse those games.

`Single.file.html` is a downloadable, self-contained copy of the FrostZ app shell. It embeds the homepage styles, images, looping background video, local game pages, and Movies page in one HTML file. The game builds, remote game catalog, movie catalog, and streaming providers still require an internet connection.
