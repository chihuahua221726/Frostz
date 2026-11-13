#!/usr/bin/env python3
"""Regenerate Single.file.html from FrostZ's canonical source files."""

import base64
import gzip
import html
import io
import json
import mimetypes
import re
import stat
import tarfile
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_MAX_BYTES = 20_000_000
GENERATED_FILES = {
    "FrostZ.svg",
    "FrostZ.svg.tmp",
    "Single.file.html",
    "Single.file.html.tmp",
}


class LocalGameCards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if (
            tag == "button"
            and "game-card" in attributes.get("class", "").split()
            and attributes.get("data-src")
        ):
            game_path = attributes["data-src"]
            if not game_path.startswith(("http:", "https:", "data:")):
                self.paths.append(game_path)


def data_uri(path):
    file_path = ROOT / path
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(file_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def encode_text(value):
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def build_repository_archive():
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for path in sorted(ROOT.rglob("*")):
            relative_path = path.relative_to(ROOT)
            if (
                any(
                    part in {".git", "__pycache__", "node_modules"}
                    for part in relative_path.parts
                )
                or relative_path.as_posix() in GENERATED_FILES
                or path.name.endswith((".pyc", ".tmp"))
                or not path.is_file()
            ):
                continue

            data = path.read_bytes()
            info = tarfile.TarInfo(relative_path.as_posix())
            info.size = len(data)
            info.mode = stat.S_IMODE(path.stat().st_mode)
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))

    return gzip.compress(archive.getvalue(), compresslevel=9, mtime=0)


def build_interactive_svg(_page):
    compressed_archive = build_repository_archive()
    encoded_archive = base64.b64encode(compressed_archive).decode("ascii")
    mime_types = {}
    with tarfile.open(
        fileobj=io.BytesIO(gzip.decompress(compressed_archive)), mode="r:"
    ) as tar:
        for member in tar:
            if member.isfile():
                extension = Path(member.name).suffix.lower()
                mime_types[extension] = (
                    mimetypes.guess_type(member.name)[0] or "application/octet-stream"
                )
    encoded_mime_types = json.dumps(mime_types, separators=(",", ":"))

    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml" width="100%" height="100%" viewBox="0 0 1280 800" preserveAspectRatio="none" role="application" aria-labelledby="frostz-svg-title frostz-svg-description">
  <title id="frostz-svg-title">FrostZ</title>
  <desc id="frostz-svg-description">FrostZ repository archive and standalone app, embedded in a compressed SVG.</desc>
  <metadata id="frostz-compressed-repository">__FROSTZ_COMPRESSED_REPOSITORY__</metadata>
  <metadata id="frostz-mime-types">__FROSTZ_MIME_TYPES__</metadata>
  <foreignObject x="0" y="0" width="1280" height="800">
    <xhtml:div xmlns="http://www.w3.org/1999/xhtml" id="frostz-loader">
      <xhtml:div id="frostz-toolbar"><xhtml:strong>FrostZ</xhtml:strong><xhtml:span id="frostz-status">Unpacking the complete FrostZ repository…</xhtml:span><xhtml:a id="frostz-download" download="FrostZ-repository.tar.gz">Download source archive</xhtml:a></xhtml:div>
      <xhtml:iframe id="frostz-app-frame" title="FrostZ interactive site" allow="fullscreen; autoplay; gamepad; clipboard-read; clipboard-write"></xhtml:iframe>
    </xhtml:div>
  </foreignObject>
  <style><![CDATA[
    #frostz-loader { display:flex; flex-direction:column; width:100%; height:100%; background:#061827; color:#eaf8ff; font:14px/1.4 Arial,sans-serif; }
    #frostz-toolbar { display:flex; flex:0 0 42px; align-items:center; gap:14px; padding:0 14px; background:#0b2233; }
    #frostz-toolbar strong { font-size:16px; }
    #frostz-status { flex:1; color:#b6d2e0; }
    #frostz-download { padding:6px 10px; border:1px solid #53c8f2; border-radius:7px; color:#eaf8ff; text-decoration:none; }
    #frostz-download:hover,#frostz-download:focus-visible { background:#12334a; outline:2px solid #82ddff; }
    #frostz-app-frame { width:100%; min-height:0; flex:1; border:0; background:#061827; }
  ]]></style>
  <script><![CDATA[
    (async () => {
      const status = document.getElementById("frostz-status");
      const encoded = document.getElementById("frostz-compressed-repository").textContent.trim();
      const mimeTypes = JSON.parse(document.getElementById("frostz-mime-types").textContent);
      const binary = atob(encoded);
      const compressed = Uint8Array.from(binary, (character) => character.charCodeAt(0));
      const decompressed = await new Response(
        new Blob([compressed]).stream().pipeThrough(new DecompressionStream("gzip"))
      ).arrayBuffer();
      const archive = new Uint8Array(decompressed);
      const decoder = new TextDecoder();
      const files = new Map();
      const readString = (start, length) => {
        const value = decoder.decode(archive.subarray(start, start + length));
        const nullIndex = value.indexOf(String.fromCharCode(0));
        return nullIndex < 0 ? value : value.slice(0, nullIndex);
      };
      for (let offset = 0; offset + 512 <= archive.length;) {
        if (archive.subarray(offset, offset + 512).every((byte) => byte === 0)) break;
        const name = readString(offset, 100);
        const prefix = readString(offset + 345, 155);
        const path = prefix ? prefix + "/" + name : name;
        const size = Number.parseInt(readString(offset + 124, 12).trim(), 8) || 0;
        const dataStart = offset + 512;
        if (readString(offset + 156, 1) === "0" || readString(offset + 156, 1) === "") {
          files.set(path, archive.slice(dataStart, dataStart + size));
        }
        offset = dataStart + Math.ceil(size / 512) * 512;
      }
      if (!files.has("index.html")) throw new Error("The repository archive has no index.html.");

      const urls = new Map();
      const textExtensions = new Set([".css", ".htm", ".html", ".js", ".mjs", ".svg"]);
      for (const [path, bytes] of files) {
        if (!textExtensions.has(path.slice(path.lastIndexOf(".")).toLowerCase())) {
          const extension = path.slice(path.lastIndexOf(".")).toLowerCase();
          urls.set(path, URL.createObjectURL(new Blob([bytes], {
            type: mimeTypes[extension] || "application/octet-stream",
          })));
        }
      }

      function localUrl(reference, sourcePath) {
        const value = reference.trim();
        if (!value || /^(?:[a-z][a-z0-9+.-]*:|\\/\\/|#)/i.test(value)) return null;
        const split = value.search(/[?#]/);
        const pathname = split < 0 ? value : value.slice(0, split);
        const suffix = split < 0 ? "" : value.slice(split);
        let resolved;
        try {
          const base = new URL("https://frostz.invalid/" + sourcePath);
          resolved = decodeURIComponent(new URL(pathname, value.startsWith("/")
            ? "https://frostz.invalid/"
            : base).pathname).replace(/^\\//, "");
        } catch {
          return null;
        }
        const blobUrl = urls.get(resolved);
        return blobUrl ? blobUrl + suffix : null;
      }

      function rewriteText(source, path) {
        let text = source;
        text = text.replace(
          /\\b(src|href|poster|data-src|action|formaction|xlink:href)\\s*=\\s*(["'])(.*?)\\2/gi,
          (match, attribute, quote, reference) => {
            const replacement = localUrl(reference, path);
            return replacement ? attribute + "=" + quote + replacement + quote : match;
          },
        );
        text = text.replace(
          /url\\(\\s*(["']?)(.*?)\\1\\s*\\)/gi,
          (match, quote, reference) => {
            const replacement = localUrl(reference, path);
            return replacement ? "url(" + quote + replacement + quote + ")" : match;
          },
        );
        if (/\\.(?:html?|js|mjs)$/i.test(path)) {
          text = text.replace(
            /(["'`])([^"'`\\s]+)\\1/g,
            (match, quote, reference) => {
              const replacement = localUrl(reference, path);
              return replacement ? quote + replacement + quote : match;
            },
          );
        }
        return text;
      }

      for (const [path, bytes] of files) {
        const extension = path.slice(path.lastIndexOf(".")).toLowerCase();
        if (!textExtensions.has(extension)) continue;
        const text = rewriteText(decoder.decode(bytes), path);
        urls.set(path, URL.createObjectURL(new Blob([text], {
          type: mimeTypes[extension] || "text/plain;charset=utf-8",
        })));
      }

      const download = document.getElementById("frostz-download");
      download.href = URL.createObjectURL(new Blob([compressed], { type: "application/gzip" }));
      status.textContent = files.size + " repository files ready.";
      document.getElementById("frostz-app-frame").src = urls.get("index.html");
    })().catch((error) => {
      document.getElementById("frostz-status").textContent = "Could not load FrostZ: " + error.message;
      console.error("Could not unpack the FrostZ repository.", error);
    });
  ]]></script>
</svg>
""".replace("__FROSTZ_COMPRESSED_REPOSITORY__", encoded_archive).replace(
        "__FROSTZ_MIME_TYPES__", encoded_mime_types
    )
    svg_bytes = svg.encode("utf-8")
    if len(svg_bytes) >= SVG_MAX_BYTES:
        raise ValueError(
            f"FrostZ.svg would be {len(svg_bytes):,} bytes; "
            f"the maximum is {SVG_MAX_BYTES - 1:,} bytes."
        )

    output = ROOT / "FrostZ.svg"
    temporary_output = output.with_suffix(output.suffix + ".tmp")
    temporary_output.write_bytes(svg_bytes)
    temporary_output.replace(output)
    print(
        f"Built {output.name}: {output.stat().st_size:,} bytes "
        f"({output.stat().st_size / 1_000_000:.2f} MB)."
    )


def build():
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    title_stylesheet = (ROOT / "Effects" / "frostz-title.css").read_text(
        encoding="utf-8"
    )
    page, stylesheet_count = re.subn(
        r'<link rel="stylesheet" href="Effects/frostz-title\.css[^"]*" />',
        lambda _: f"<style>\n{title_stylesheet}\n</style>",
        page,
        count=1,
    )
    if stylesheet_count != 1:
        raise ValueError("Could not find the FrostZ title stylesheet link in index.html")
    theme_stylesheet = (ROOT / "Effects" / "frostz-themes.css").read_text(
        encoding="utf-8"
    )
    page, theme_stylesheet_count = re.subn(
        r'<link rel="stylesheet" href="Effects/frostz-themes\.css" />',
        lambda _: f"<style>\n{theme_stylesheet}\n</style>",
        page,
        count=1,
    )
    if theme_stylesheet_count != 1:
        raise ValueError("Could not find the FrostZ theme stylesheet link in index.html")

    asset_directory = ROOT / "Games" / "assets"
    for asset in sorted(asset_directory.iterdir()):
        if asset.is_file():
            relative_path = asset.relative_to(ROOT).as_posix()
            page = page.replace(relative_path, data_uri(relative_path))

    cards = LocalGameCards()
    cards.feed(page)
    game_paths = sorted(set(cards.paths))
    if not game_paths:
        raise ValueError("No local game cards with data-src paths were found")

    game_pages = {}
    for game_path in game_paths:
        source = ROOT / game_path
        if not source.is_file():
            raise FileNotFoundError(f"Local game page does not exist: {game_path}")
        game_page = source.read_text(encoding="utf-8")
        game_page = game_page.replace(
            "../Games/assets/oneko-thanksgiving.png",
            data_uri("Games/assets/oneko-thanksgiving.png"),
        )
        game_pages[game_path] = base64.b64encode(game_page.encode("utf-8")).decode(
            "ascii"
        )

    movie_path = ROOT / "Games" / "Apps" / "Movie.html"
    movie = movie_path.read_text(encoding="utf-8")
    movie, movie_stylesheet_count = re.subn(
        r'<link rel="stylesheet" href="\.\./\.\./Effects/frostz-themes\.css" />',
        lambda _: f"<style>\n{theme_stylesheet}\n</style>",
        movie,
        count=1,
    )
    if movie_stylesheet_count != 1:
        raise ValueError("Could not find the theme stylesheet link in the Movies page")
    movie = movie.replace("../assets/home-icon.png", data_uri("Games/assets/home-icon.png"))
    movie = movie.replace("../../index.html", "#frostz-home")
    movie_script = """<script>
      document.querySelectorAll(".nf-home-button").forEach((button) => {
        button.addEventListener("click", (event) => {
          event.preventDefault();
          parent.postMessage({ type: "frostz-bundle-home" }, "*");
        });
      });
    </script>
  </body>"""
    if "</body>" not in movie:
        raise ValueError("Could not find the closing body tag in the Movies page")
    movie = movie.replace("</body>", movie_script, 1)

    json_pages = json.dumps(game_pages, separators=(",", ":"), ensure_ascii=True)
    json_pages = json_pages.replace("<", "\\u003c")
    bundled_json = (
        '<script id="frostz-bundled-pages" type="application/json">'
        + json_pages
        + "</script>"
    )
    page, body_count = page.replace("  <body>", "  <body>\n    " + bundled_json, 1), page.count(
        "  <body>"
    )
    if body_count != 1:
        raise ValueError("Could not find a unique body start tag in index.html")

    player_markup = """      <iframe id="game-frame" title="Game" allow="fullscreen"></iframe>
      <iframe id="browser-frame" title="Browser tab" allow="fullscreen; autoplay; clipboard-read; clipboard-write" hidden></iframe>
    </section>"""
    movie_markup = """      <iframe id="game-frame" title="Game" allow="fullscreen"></iframe>
      <iframe id="browser-frame" title="Browser tab" allow="fullscreen; autoplay; clipboard-read; clipboard-write" hidden></iframe>
    </section>
    <section id="bundle-movie-view" class="bundle-movie-view" hidden aria-label="Movies">
      <header class="bundle-movie-toolbar">
        <button id="bundle-movie-back" type="button">Back to FrostZ</button>
        <strong>FrostZ Movies</strong>
      </header>
      <iframe id="bundle-movie-frame" title="FrostZ Movies" allow="fullscreen; autoplay; picture-in-picture"></iframe>
    </section>"""
    if page.count(player_markup) != 1:
        raise ValueError("Could not find the game player insertion point in index.html")
    page = page.replace(player_markup, movie_markup, 1)

    style_anchor = """      .screen[hidden] {
        display: none;
      }"""
    movie_styles = """      .bundle-movie-view[hidden] { display: none; }
      .bundle-movie-view { position: fixed; z-index: 60; inset: 0; display: flex; flex-direction: column; background: #061827; }
      .bundle-movie-toolbar { min-height: 48px; display: flex; align-items: center; gap: 16px; padding: 6px 12px; background: #0b2233; color: #eaf8ff; }
      .bundle-movie-toolbar button { min-height: 34px; padding: 6px 12px; border: 1px solid #66c9ef; border-radius: 8px; background: #12334a; color: inherit; font: inherit; cursor: pointer; }
      .bundle-movie-toolbar button:hover, .bundle-movie-toolbar button:focus-visible { background: #1d5b79; outline: 2px solid #bceeff; outline-offset: 2px; }
      #bundle-movie-frame { width: 100%; flex: 1; border: 0; }

"""
    if page.count(style_anchor) != 1:
        raise ValueError("Could not find the screen visibility style insertion point")
    page = page.replace(style_anchor, movie_styles + style_anchor, 1)

    script_anchor = '      const frostzTitle = document.getElementById("frostz-title");'
    movie_logic = f"""      const bundledPages = JSON.parse(document.getElementById("frostz-bundled-pages").textContent);
      function decodeBundledPage(encoded) {{
        const bytes = Uint8Array.from(atob(encoded), (char) => char.charCodeAt(0));
        return new TextDecoder().decode(bytes);
      }}
      const bundleMovieView = document.getElementById("bundle-movie-view");
      const bundleMovieFrame = document.getElementById("bundle-movie-frame");
      function closeBundleMovie() {{
        bundleMovieView.hidden = true;
        bundleMovieFrame.srcdoc = "";
      }}
      document.querySelectorAll('a[href="Games/Apps/Movie.html"]').forEach((movieLink) => movieLink.addEventListener("click", (event) => {{
        event.preventDefault();
        bundleMovieFrame.srcdoc = decodeBundledPage({json.dumps(encode_text(movie))});
        bundleMovieView.hidden = false;
      }}));
      document.getElementById("bundle-movie-back").addEventListener("click", closeBundleMovie);
      window.addEventListener("message", (event) => {{
        if (event.data && event.data.type === "frostz-bundle-home") closeBundleMovie();
      }});

"""
    if page.count(script_anchor) != 1:
        raise ValueError("Could not find the homepage script insertion point")
    page = page.replace(script_anchor, movie_logic + script_anchor, 1)

    game_load = "        frame.src = card.dataset.src;"
    embedded_game_load = """        const bundledPage = bundledPages[card.dataset.src];
        if (bundledPage) {
          frame.srcdoc = decodeBundledPage(bundledPage);
        } else {
          frame.src = card.dataset.src;
        }"""
    if page.count(game_load) != 1:
        raise ValueError("Could not find the game loading insertion point")
    page = page.replace(game_load, embedded_game_load, 1)

    output = ROOT / "Single.file.html"
    temporary_output = output.with_suffix(output.suffix + ".tmp")
    temporary_output.write_text(page, encoding="utf-8", newline="\n")
    temporary_output.replace(output)
    print(
        f"Built {output.name}: {output.stat().st_size:,} bytes, "
        f"{len(game_paths)} local game pages, one Movies page."
    )
    build_interactive_svg(page)


if __name__ == "__main__":
    build()
