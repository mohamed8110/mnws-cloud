
import streamlit as st
import subprocess
from datetime import datetime, date
import os

st.set_page_config(page_title="MNWS Artikel Dashboard", layout="centered")

st.title("📰 MNWS Artikelverwerker")

st.markdown("Kies hieronder de gewenste verwerkingswijze:")

st.header("⚙️ Verwerkingsopties")
option = st.radio("Wat wil je doen?", ["📚 Lange Artikels", "📝 Samenvattingen"])

st.header("📡 Kies een RSS-bron (of verwerk alles)")
try:
    with open("rss_feeds.txt", "r", encoding="utf-8") as f:
        extra_feeds = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    extra_feeds = []

default_feeds = [
    "https://www.hespress.com/feed",
    "https://www.moroccoworldnews.com/feed/",
    "https://www.bladna.nl/rss",
    "https://www.oujdacity.net/feed",
    "https://en.hespress.com/feed",
    "https://fr.hespress.com/feed"
]

all_feeds = list(set(default_feeds + extra_feeds))
selected_feed = st.selectbox("Kies optioneel een specifieke feed", ["Alle feeds"] + all_feeds)

st.header("📅 Kies datum")
selected_date = st.date_input("Selecteer de publicatiedatum van de artikels", value=date.today())

st.markdown("---")
if st.button("▶️ Start verwerking"):
    script = "rss_to_wordpress_mnws_longform.py" if option == "📚 Lange Artikels" else "rss_to_wordpress_mnws_summary.py"

    env = os.environ.copy()
    env["TARGET_DATE"] = selected_date.isoformat()

    if selected_feed != "Alle feeds":
        with open("rss_feeds.txt", "w", encoding="utf-8") as f:
            f.write(selected_feed + "\n")

    with st.spinner(f"Verwerken met script: {script}"):
        result = subprocess.run(["python", script], capture_output=True, text=True, env=env)
        st.code(result.stdout + result.stderr)

    st.success("Verwerking afgerond. Controleer je WordPress concepten.")

st.header("➕ RSS-feed toevoegen")
new_rss = st.text_input("Nieuwe RSS-feed URL")
if st.button("➕ Voeg feed toe"):
    with open("rss_feeds.txt", "a", encoding="utf-8") as f:
        f.write(new_rss + "\n")
    st.success("RSS-feed toegevoegd!")

st.caption(f"Laatste update: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
