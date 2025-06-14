import streamlit as st
from datetime import datetime
import os

st.set_page_config(page_title="MNWS RSS Dashboard", layout="centered")
st.title("📆 MNWS Artikelverwerker")
st.markdown("Kies een datum en druk op **Start** om artikelen te verwerken:")

selected_date = st.date_input("Selecteer een datum", datetime.today())

if st.button("🚀 Start verwerking"):
    st.info(f"Artikels van {selected_date} worden verwerkt...")
    date_str = selected_date.strftime("%Y-%m-%d")
    os.system(f'python rss_to_wordpress_mnws_longform.py "{date_str}"')
    st.success("✅ Voltooid!")