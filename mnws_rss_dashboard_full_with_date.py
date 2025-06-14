
import streamlit as st
import subprocess
from datetime import datetime, date
import os
import pandas as pd

# ✅ Belangrijk: eerste Streamlit-commando
st.set_page_config(page_title="MNWS Artikel Dashboard", layout="centered")

# Statistiekfunctie
def log_post_count(nieuwe_posts):
    today = datetime.now().date().isoformat()
    log_path = "mnws_post_stats.csv"
    if os.path.exists(log_path):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{today},{nieuwe_posts}\n")
    else:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("datum,aantal_artikels\n")
            f.write(f"{today},{nieuwe_posts}\n")

def toon_statistieken():
    st.sidebar.title("📊 Statistieken")
    log_path = "mnws_post_stats.csv"
    if os.path.exists(log_path):
        df = pd.read_csv(log_path)
        totaal = df["aantal_artikels"].sum()
        vandaag = df[df["datum"] == datetime.now().date().isoformat()]["aantal_artikels"].sum()
        st.sidebar.metric("Vandaag gepost", vandaag)
        st.sidebar.metric("Totaal gepost", totaal)
    else:
        st.sidebar.info("Nog geen statistieken beschikbaar.")

toon_statistieken()

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

        gepost_count = result.stdout.count("[OK] Gepost:")
        log_post_count(gepost_count)

    st.success("Verwerking afgerond. Controleer je WordPress concepten.")

st.header("➕ RSS-feed toevoegen")
new_rss = st.text_input("Nieuwe RSS-feed URL")
if st.button("➕ Voeg feed toe"):
    with open("rss_feeds.txt", "a", encoding="utf-8") as f:
        f.write(new_rss + "\n")
    st.success("RSS-feed toegevoegd!")

st.caption(f"Laatste update: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
