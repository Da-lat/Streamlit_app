import streamlit as st

home_page = st.Page("Page_0.py", title="Home", icon=":material/house:")
yt_page = st.Page("Page_1.py", title="Youtube Analysis", icon=":material/add_circle:")
pdf_page = st.Page("Page_2.py", title="PDF Analysis", icon=":material/delete:")
url_page = st.Page("Page_3.py", title="URL Analysis", icon=":material/insert_link:")
csv_page = st.Page("Page_4.py", title="CSV Analysis", icon=":material/import_contacts:")
text_page = st.Page("Page_5.py", title="Text Analysis", icon=":material/insert_drive_file:")
video_game_covers = st.Page("Page_6.py", title="Video Game Covers", icon=":material/thumb_up:")
# timezones = st.Page("Page_7.py", title="Timezone Converter", icon=":material/schedule:")
news = st.Page("Page_8.py", title="Worldwide News", icon=":material/email:")
random_champ = st.Page("Page_9.py", title="Random Champion", icon=":material/sports_esports:")
coach_analysis = st.Page("Page_10.py", title="Coach Analysis", icon=":material/sports_kabaddi:")
flex_combo_stats = st.Page("Page_11.py", title="Flex Combo Stats", icon=":material/groups:")

pg = st.navigation([home_page,yt_page, pdf_page, url_page, csv_page, text_page, video_game_covers, news, random_champ, coach_analysis, flex_combo_stats])

pg.run()
