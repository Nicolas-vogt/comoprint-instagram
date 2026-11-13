"""
Variante sans compte développeur Meta : la connexion à Instagram est gérée par Behold.

Exécuté chaque jour par GitHub Actions :
1. lit le flux JSON Behold (une seule requête par jour, donc environ 30 vues par mois,
   très en dessous des 1 200 vues mensuelles de l'offre gratuite) ;
2. télécharge et redimensionne les 6 images ;
3. écrit docs/feed.json, au même format que la version API Instagram.

Les visiteurs du site ne contactent jamais Behold : ils lisent le fichier publié sur GitHub Pages.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

from fetch_instagram import COUNT, IMG_DIR, OUT, clean_caption, download_square


def pick_image(post):
    sizes = post.get("sizes") or {}
    for key in ("medium", "large", "full", "small"):
        url = (sizes.get(key) or {}).get("mediaUrl")
        if url:
            return url
    return post.get("thumbnailUrl") or post.get("mediaUrl")


def main():
    feed_url = os.environ.get("BEHOLD_FEED_URL", "").strip()
    if not feed_url:
        sys.exit("Secret BEHOLD_FEED_URL manquant.")

    req = urllib.request.Request(feed_url, headers={"User-Agent": "comoprint-instagram-feed"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        sys.exit(f"Erreur Behold {err.code} : flux précédent conservé.")

    posts = data.get("posts") or []
    if not posts:
        sys.exit("Aucune publication renvoyée par Behold : flux précédent conservé.")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    items, keep = [], set()
    for p in posts[:COUNT]:
        src = pick_image(p)
        if not src:
            continue
        name = f"{p['id']}.webp"
        dest = IMG_DIR / name
        if not dest.exists():
            download_square(src, dest)
        keep.add(name)
        items.append({
            "id": p["id"],
            "type": p.get("mediaType"),
            "permalink": p.get("permalink"),
            "image": f"img/{name}",
            "caption": clean_caption(p.get("prunedCaption") or p.get("caption")),
            "timestamp": p.get("timestamp"),
        })

    for f in IMG_DIR.glob("*.webp"):
        if f.name not in keep:
            f.unlink()

    username = data.get("username")
    feed = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "username": username,
        "profile_url": f"https://www.instagram.com/{username}/" if username else "https://www.instagram.com/",
        "items": items,
    }
    (OUT / "feed.json").write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / ".nojekyll").touch()
    print(f"{len(items)} publications écrites dans docs/feed.json (source : Behold)")


if __name__ == "__main__":
    main()
