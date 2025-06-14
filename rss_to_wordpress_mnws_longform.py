import os
import feedparser
import openai
import requests
from bs4 import BeautifulSoup
from html import escape
from datetime import datetime
from urllib.parse import urljoin
import sys

openai.api_key = os.getenv("OPENAI_API_KEY")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
WORDPRESS_USER = os.getenv("WORDPRESS_USER")
WORDPRESS_APP_PASS = os.getenv("WORDPRESS_APP_PASS")

DEFAULT_FEEDS = [
    "https://www.hespress.com/feed",
    "https://www.moroccoworldnews.com/feed/",
    "https://www.bladna.nl/rss",
    "https://www.oujdacity.net/feed",
    "https://en.hespress.com/feed",
    "https://fr.hespress.com/feed"
]

def fetch_articles_from_feed(feed_url, selected_date):
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        try:
            entry_date = datetime(*entry.published_parsed[:6]).date()
        except Exception:
            continue
        if entry_date == selected_date:
            articles.append(entry)
    return articles

def translate_text(text, style="article"):
    if style == "title":
        prompt = "Vertaal deze titel naar helder en correct Nederlands, zonder aanhalingstekens of extra uitleg."
    else:
        prompt = (
            "Herschrijf dit nieuwsartikel in verzorgd en informatief Nederlands zoals op MNWS.be. "
            "Gebruik een vlotte journalistieke schrijfstijl, zonder verwijzing naar de bron."
        )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Vertaalfout:", e)
        return text

def extract_image(entry):
    soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
    img = soup.find("img")
    return img["src"] if img and "src" in img.attrs else None

def build_html(content):
    return f'''
    <div>
        <p><i class="fa fa-clock"></i> {datetime.now().strftime('%d-%m-%Y')}</p>
        <div>{content}</div>
        <p><i class="fa fa-globe"></i> Bron: MNWS.be</p>
    </div>
    '''

def upload_featured_image(image_url):
    try:
        img_data = requests.get(image_url).content
        media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        headers = {
            'Content-Disposition': 'attachment; filename=image.jpg'
        }
        response = requests.post(
            media_endpoint,
            headers=headers,
            data=img_data,
            auth=(WORDPRESS_USER, WORDPRESS_APP_PASS)
        )
        if response.status_code == 201:
            return response.json().get("id")
    except Exception as e:
        print("Afbeelding uploaden mislukt:", e)
    return None

def post_to_wordpress(title, content, image_id=None):
    endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/posts"
    data = {
        "title": title,
        "content": content,
        "status": "draft",
        "meta": {
            "jannah_post_layout": "layout-2",
            "jannah_single_page_layout": "fullwidth",
            "jannah_post_sidebar": "none"
        }
    }
    if image_id:
        data["featured_media"] = image_id

    response = requests.post(endpoint, json=data, auth=(WORDPRESS_USER, WORDPRESS_APP_PASS))
    if response.status_code == 201:
        print("✅ Gepost:", title)
    else:
        print("❌ Fout bij posten:", response.status_code, response.text)

def process_all(feeds, selected_date):
    for feed_url in feeds:
        entries = fetch_articles_from_feed(feed_url, selected_date)
        for entry in entries:
            original_title = entry.get("title", "")
            translated_title = translate_text(original_title, style="title")
            full_text = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text()
            translated_content = translate_text(full_text, style="article")
            html_content = build_html(translated_content)
            image_url = extract_image(entry)
            image_id = upload_featured_image(image_url) if image_url else None
            post_to_wordpress(translated_title, html_content, image_id)

if __name__ == "__main__":
    date_input = sys.argv[1] if len(sys.argv) > 1 else datetime.today().strftime("%Y-%m-%d")
    feed_string = sys.argv[2] if len(sys.argv) > 2 else ""
    selected_date = datetime.strptime(date_input, "%Y-%m-%d").date()
    feeds = feed_string.split(";;") if feed_string else DEFAULT_FEEDS
    process_all(feeds, selected_date)