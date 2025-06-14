import streamlit as st
from datetime import datetime
import os

st.set_page_config(page_title="MNWS Artikelverwerker", layout="centered")
st.image("logo.png", width=200)
st.title("📰 MNWS Artikelverwerker")

# Stap 1: Kies RSS feeds
feed_options = {
    "🇲🇦 Hespress NL/AR/FR": [
        "https://www.hespress.com/feed",
        "https://en.hespress.com/feed",
        "https://fr.hespress.com/feed"
    ],
    "🌍 Morocco World News": [
        "https://www.moroccoworldnews.com/feed/"
    ],
    "🧭 Bladna.nl": [
        "https://www.bladna.nl/rss"
    ],
    "📡 OujdaCity": [
        "https://www.oujdacity.net/feed"
    ],
    "📦 Alles combineren": [
        "https://www.hespress.com/feed",
        "https://en.hespress.com/feed",
        "https://fr.hespress.com/feed",
        "https://www.moroccoworldnews.com/feed/",
        "https://www.bladna.nl/rss",
        "https://www.oujdacity.net/feed"
    ]
}
st.subheader("1️⃣ Kies een RSS-bron")
selected_source = st.selectbox("RSS feed selectie", list(feed_options.keys()))

# Stap 2: Kies datum
st.subheader("2️⃣ Kies een publicatiedatum")
selected_date = st.date_input("Selecteer een datum", datetime.today())

# Stap 3: Extra feeds manueel
st.subheader("3️⃣ Extra RSS-feeds (optioneel)")
extra_feeds_input = st.text_area("Voeg hier handmatig RSS-links toe (1 per regel)", height=100)

# Stap 4: Opties
st.subheader("4️⃣ Verwerkingsopties")
with_afbeelding = st.checkbox("📸 Voeg uitgelichte afbeelding toe", value=True)
lange_artikels = st.radio("📝 Artikeltype", ["Lange artikels (volledig herschreven)", "Korte samenvatting"], index=0)

# Verwerken
if st.button("🚀 Start verwerking"):
    extra_feeds = extra_feeds_input.strip().splitlines() if extra_feeds_input else []
    all_feeds = feed_options[selected_source] + extra_feeds
    feed_string = ";;".join(all_feeds)
    date_str = selected_date.strftime("%Y-%m-%d")
    artikelvorm = "long" if lange_artikels.startswith("Lange") else "short"
    image_flag = "yes" if with_afbeelding else "no"
    os.system(f'python rss_to_wordpress_mnws_longform.py "{date_str}" "{feed_string}" "{image_flag}" "{artikelvorm}"')
    st.success("✅ Verwerking afgerond.")