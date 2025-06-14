import streamlit as st
from datetime import datetime
import os

st.set_page_config(page_title="MNWS Artikelverwerker", layout="centered")
st.image("logo.png", width=200)
st.title("📆 MNWS Artikelverwerker")
st.markdown("Kies een datum en vul optioneel extra RSS-feeds in.")

selected_date = st.date_input("📅 Selecteer een datum", datetime.today())
extra_feeds_input = st.text_area("➕ Voeg extra RSS-feeds toe (1 per lijn)", height=100)

DEFAULT_FEEDS = [
    "https://www.hespress.com/feed",
    "https://www.moroccoworldnews.com/feed/",
    "https://www.bladna.nl/rss",
    "https://www.oujdacity.net/feed",
    "https://en.hespress.com/feed",
    "https://fr.hespress.com/feed"
]

with st.expander("📋 Standaard RSS-feeds"):
    for feed in DEFAULT_FEEDS:
        st.code(feed, language="url")

if st.button("🚀 Start verwerking"):
    extra_feeds = extra_feeds_input.strip().splitlines() if extra_feeds_input else []
    all_feeds = DEFAULT_FEEDS + extra_feeds
    feed_string = ";;".join(all_feeds)
    date_str = selected_date.strftime("%Y-%m-%d")
    st.info(f"Artikels van {date_str} worden verwerkt...")
    os.system(f'python rss_to_wordpress_mnws_longform.py "{date_str}" "{feed_string}"')
    st.success("✅ Voltooid!")