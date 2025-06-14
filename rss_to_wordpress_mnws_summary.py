
import os
import feedparser
import openai
import requests
from bs4 import BeautifulSoup
from html import escape
from datetime import datetime, date
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

WORDPRESS_URL = os.getenv("WORDPRESS_URL")
WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASS = os.getenv("WORDPRESS_APP_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_DATE = os.getenv("TARGET_DATE")

if TARGET_DATE:
    try:
        TARGET_DATE = datetime.strptime(TARGET_DATE, "%Y-%m-%d").date()
    except:
        TARGET_DATE = date.today()
else:
    TARGET_DATE = date.today()

openai.api_key = OPENAI_API_KEY

DEFAULT_FEEDS = [
    "https://www.hespress.com/feed",
    "https://www.moroccoworldnews.com/feed/",
    "https://www.bladna.nl/rss",
    "https://www.oujdacity.net/feed",
    "https://en.hespress.com/feed",
    "https://fr.hespress.com/feed"
]

def load_feeds():
    if os.path.exists("rss_feeds.txt"):
        with open("rss_feeds.txt", "r", encoding="utf-8") as f:
            feeds = [line.strip() for line in f if line.strip()]
            return feeds if feeds else DEFAULT_FEEDS
    return DEFAULT_FEEDS

    if os.path.exists("rss_feeds.txt"):
        with open("rss_feeds.txt", "r", encoding="utf-8") as f:
            feeds = [line.strip() for line in f if line.strip()]
            return feeds if feeds else DEFAULT_FEEDS
    return DEFAULT_FEEDS

def translate_text(text, as_title=False):
    instruction = (
        "Vertaal deze titel kort en duidelijk naar professioneel Nederlands, zonder bronvermelding." if as_title else
        "Vat dit artikel samen in maximaal 2 alinea's in professioneel Nederlands, in journalistieke stijl zoals MNWS.be. Geen bronvermelding. Eindig met: 'Bron: MNWS.be'."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": text}
            ],
            timeout=30
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[FOUT bij vertalen]", e)
        return text

def extract_image(entry):
    if "media_content" in entry:
        for media in entry.media_content:
            if "url" in media:
                return media["url"]
    if "summary" in entry:
        soup = BeautifulSoup(entry.summary, "html.parser")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    return None

def download_and_upload_image(image_url):
    try:
        image_data = requests.get(image_url, timeout=10).content
        filename = os.path.basename(image_url.split("?")[0])
        media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        response = requests.post(
            media_endpoint,
            headers=headers,
            data=image_data,
            auth=(WORDPRESS_USER, WORDPRESS_APP_PASS)
        )
        if response.status_code == 201:
            return response.json()["id"]
    except Exception as e:
        print("[WAARSCHUWING] Geen afbeelding geüpload:", e)
    return None

def post_to_wordpress(title, content, image_url=None):
    featured_media_id = download_and_upload_image(image_url) if image_url else None
    endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    slug = "-".join(title.lower().split())[:80]
    data = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": "draft",
        "template": "template-layout2.php",
        "meta": {
            "_hide_author_box": "yes",
            "post_layout": "2",
            "sidebar_option": "no-sidebar"
        }
    }
    if featured_media_id:
        data["featured_media"] = featured_media_id

    response = requests.post(endpoint, json=data, auth=(WORDPRESS_USER, WORDPRESS_APP_PASS))
    if response.status_code == 201:
        print("[OK] Gepost:", title)
    else:
        print("[FOUT]", response.status_code, response.text)

def fetch_and_process():
    feeds = load_feeds()
    today = datetime.now().date()
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if "published_parsed" in entry:
                published_date = datetime(*entry.published_parsed[:3]).date()
                if published_date != today:
                    continue
            title = entry.title.strip()
            summary = BeautifulSoup(entry.summary, "html.parser").get_text()
            translated_title = translate_text(title, as_title=True)
            translated_summary = translate_text(summary)
            html_content = f"<div><i class='icon-news'></i><p>{escape(translated_summary)}</p></div>"
            image_url = extract_image(entry)
            post_to_wordpress(translated_title, html_content, image_url)

if __name__ == "__main__":
    fetch_and_process()