"""
Collecte des dernières publications Instagram de Comoprint.

Exécuté chaque jour par GitHub Actions :
1. rafraîchit le jeton d'accès Instagram (valable 60 jours, prolongé à chaque passage) ;
2. récupère les N dernières publications ;
3. télécharge et redimensionne les images (les URL Instagram expirent) ;
4. écrit docs/feed.json, servi par GitHub Pages et lu par le carrousel du site.

En cas d'erreur, le script s'arrête avec un code non nul : le flux publié la veille
reste en ligne et GitHub envoie un email d'échec au propriétaire du dépôt.
"""

import io
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from PIL import Image

API = "https://graph.instagram.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"
IMG_DIR = OUT / "img"
COUNT = int(os.environ.get("IG_COUNT", "6"))
IMG_SIZE = 640  # côté du carré en pixels
CAPTION_MAX = 140
NEW_TOKEN_FILE = ROOT / ".new_token"  # lu par le workflow, jamais commité


def api_get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        # Ne jamais afficher le jeton dans les journaux
        raise RuntimeError(f"Erreur API Instagram {err.code} sur /{path} : {body}") from None


def refresh_token(token):
    """Prolonge le jeton de 60 jours. Échec non bloquant (jeton de moins de 24 h, etc.)."""
    try:
        data = api_get("refresh_access_token", {
            "grant_type": "ig_refresh_token",
            "access_token": token,
        })
    except RuntimeError as err:
        print(f"::warning::Rafraîchissement du jeton non effectué : {err}")
        return token
    new = data.get("access_token", token)
    days = int(data.get("expires_in", 0)) // 86400
    print(f"Jeton rafraîchi, valable encore {days} jours.")
    if new != token:
        NEW_TOKEN_FILE.write_text(new, encoding="utf-8")
        print("Nouveau jeton émis : le secret GitHub sera mis à jour.")
    return new


def download_square(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize(
        (IMG_SIZE, IMG_SIZE), Image.LANCZOS
    )
    img.save(dest, "WEBP", quality=80, method=6)


def clean_caption(text):
    text = " ".join((text or "").split())
    if len(text) > CAPTION_MAX:
        text = text[: CAPTION_MAX - 1].rsplit(" ", 1)[0] + "…"
    return text


def main():
    token = os.environ.get("IG_TOKEN", "").strip()
    if not token:
        sys.exit("Secret IG_TOKEN manquant.")

    token = refresh_token(token)

    profile = api_get("me", {"fields": "username", "access_token": token})
    media = api_get("me/media", {
        "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
        "limit": COUNT,
        "access_token": token,
    }).get("data", [])

    if not media:
        sys.exit("Aucune publication renvoyée par Instagram : flux précédent conservé.")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    items, keep = [], set()
    for m in media[:COUNT]:
        src = m.get("thumbnail_url") if m.get("media_type") == "VIDEO" else m.get("media_url")
        if not src:
            continue
        name = f"{m['id']}.webp"
        dest = IMG_DIR / name
        if not dest.exists():
            download_square(src, dest)
        keep.add(name)
        items.append({
            "id": m["id"],
            "type": m.get("media_type"),
            "permalink": m.get("permalink"),
            "image": f"img/{name}",
            "caption": clean_caption(m.get("caption")),
            "timestamp": m.get("timestamp"),
        })

    # Suppression des images des publications sorties du flux
    for f in IMG_DIR.glob("*.webp"):
        if f.name not in keep:
            f.unlink()

    feed = {
        # Date mise à jour à chaque passage : garantit un commit quotidien,
        # donc une activité du dépôt qui empêche GitHub de suspendre la tâche.
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "username": profile.get("username"),
        "profile_url": f"https://www.instagram.com/{profile.get('username')}/",
        "items": items,
    }
    (OUT / "feed.json").write_text(
        json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / ".nojekyll").touch()
    print(f"{len(items)} publications écrites dans docs/feed.json")


if __name__ == "__main__":
    main()
