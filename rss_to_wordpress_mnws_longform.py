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
    try:
        with open("rss_feeds.txt", "r", encoding="utf-8") as f:
            extra = [line.strip() for line in f if line.strip()]
        return list(set(DEFAULT_FEEDS + extra))
    except FileNotFoundError:
        return DEFAULT_FEEDS

seen_articles = set()

def fetch_and_process(max_articles_per_day=100):
    count = 0
    feeds = load_feeds()

    for url in feeds:
        if count >= max_articles_per_day:
            break
        feed = feedparser.parse(url)

        for entry in feed.entries:
            if count >= max_articles_per_day:
                break
            if not hasattr(entry, 'published_parsed'):
                continue
            pub_date = datetime(*entry.published_parsed[:6]).date()
            if pub_date != TARGET_DATE:
                continue
            if entry.link in seen_articles:
                continue

            seen_articles.add(entry.link)
            title_raw = entry.title
            summary = BeautifulSoup(entry.summary, "html.parser").get_text()
            image_url = extract_image_url(entry)

            content_raw = f"{title_raw}\n\n{summary}"
            translated_title = translate_text(title_raw, as_title=True)
            translated_content = translate_text(content_raw, as_title=False)

            html_content = build_html(translated_title, translated_content)
            post_to_wordpress(translated_title, html_content, image_url)
            count += 1

def extract_image_url(entry):
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    elif 'media_thumbnail' in entry:
        return entry.media_thumbnail[0]['url']
    return None

def translate_text(text, as_title=False):
    try:
        instruction = (
            "Vertaal deze titel helder en bondig naar journalistiek Nederlands zoals op MNWS.be. Geen bronvermelding."
            if as_title else
            "Vertaal en herschrijf dit artikel naar professioneel Nederlands met minimaal 5 uitgebreide paragrafen. "
            "Voeg achtergrondinformatie, context en relevante details toe. Gebruik een journalistieke stijl zoals MNWS.be. "
            "Geen bronvermelding. Eindig met: 'Bron: MNWS.be'."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[FOUT] Vertaling mislukt:", e)
        return "Vertaling mislukt."

def build_html(title, body):
    today = datetime.now().strftime("%d-%m-%Y")
    paragraphs = body.split("\n")
    clean_paragraphs = [p for p in paragraphs if "Bron: MNWS.be" not in p]
    formatted_paragraphs = ''.join(f"<p>{escape(p.strip())}</p>" for p in clean_paragraphs if p.strip())

    return f'''
    <div class="mnws-artikel" style="font-family: Arial, sans-serif; padding: 20px;">
      <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
        <span style="font-weight: bold; font-size: 14px; color: #999;">Nieuws • {today}</span>
      </div>
      <h2 style="font-size: 22px; font-weight: 700; margin-top: 10px;">{escape(title.strip())}</h2>
      <div style="margin-top: 15px; font-size: 17px; line-height: 1.7;">
        {formatted_paragraphs}
        <p style="margin-top: 30px; font-style: italic; color: #777;">Bron: MNWS.be</p>
      </div>
    </div>
    '''

def slugify(text):
    return "-".join(text.lower().strip().replace("’", "").replace("'", "").split())[:100]

def post_to_wordpress(title, content, image_url):
    existing = requests.get(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts?search={title}",
        auth=(WORDPRESS_USER, WORDPRESS_APP_PASS)
    )
    if existing.status_code == 200 and existing.json():
        print("[DUBBEL] Artikel bestaat al:", title)
        return

    slug = slugify(title)

    post_data = {
        "title": title.strip(),
        "content": content,
        "status": "draft",
        "slug": slug,
        "meta": {
            "_tie_full_width": "yes",
            "_tie_post_layout": "layout-2",
            "_hide_author_box": "yes",
            "_tie_sidebar_pos": "none"
        }
    }

    if image_url:
        media_id = upload_featured_image(image_url)
        if media_id:
            post_data["featured_media"] = media_id
        else:
            print("[WAARSCHUWING] Geen afbeelding geüpload.")

    response = requests.post(
        f"{WORDPRESS_URL}/wp-json/wp/v2/posts",
        json=post_data,
        auth=(WORDPRESS_USER, WORDPRESS_APP_PASS)
    )
    if response.status_code == 201:
        print("[OK] Gepost:", title)
    else:
        print("[FOUT] Post mislukt:", response.status_code, response.text)

def upload_featured_image(image_url):
    try:
        response = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print("[FOUT] Afbeelding ophalen mislukt:", image_url)
            return None
        image_data = response.content
        filename = image_url.split("/")[-1]
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'image/jpeg'
        }
        media_endpoint = f"{WORDPRESS_URL}/wp-json/wp/v2/media"
        wp_response = requests.post(
            media_endpoint,
            headers=headers,
            data=image_data,
            auth=(WORDPRESS_USER, WORDPRESS_APP_PASS)
        )
        if wp_response.status_code == 201:
            return wp_response.json().get("id")
        else:
            print("[FOUT] Upload mislukt:", wp_response.status_code)
    except Exception as e:
        print("[FOUT] Afbeelding upload error:", e)
    return None

if __name__ == "__main__":
    fetch_and_process()