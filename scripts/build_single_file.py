#!/usr/bin/env python3
"""Regenerate Single.file.html from FrostZ's canonical source files."""

import base64
import json
import mimetypes
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        game_pages[game_path] = base64.b64encode(source.read_bytes()).decode("ascii")

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


if __name__ == "__main__":
    build()
