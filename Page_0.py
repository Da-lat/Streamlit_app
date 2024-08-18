import streamlit as st

# Labelling
st.sidebar.markdown("# Swiss Army Summaries 🛸")
st.sidebar.markdown("Feel free to navigate through the different pages, choose your input and let the magic happen!")
st.title("Home 🛸")
st.write("***")
st.write("## Welome to the Swiss Army Knife of summarising media options! Select an option for your input below to get started.")
st.write("")

col1, col2, col3, col4, col5 = st.columns(5)

# Navigation links
with col1:
    st.image("https://images.unsplash.com/photo-1611162616475-46b635cb6868?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("Page_1.py", label="Youtube", icon="🎈")
with col2:
    st.image("https://images.unsplash.com/photo-1553484771-371a605b060b?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("Page_2.py", label="PDF", icon="📄")
with col3:
    st.image("https://images.unsplash.com/photo-1617854818583-09e7f077a156?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("Page_3.py", label="URL", icon="💻")
with col4:
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("Page_4.py", label="CSV", icon="📈")
with col5:
    st.image("https://images.unsplash.com/photo-1517180102446-f3ece451e9d8?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("Page_5.py", label="Text", icon="🔤")

st.write("***")
st.write("### Contact me if you have any questions or issues, you can find me here!")
st.write("***")
# Social links

col6, col7, col8, col9, col10 = st.columns(5)

with col6:
    st.image("https://images.unsplash.com/photo-1611944212129-29977ae1398c?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("https://www.linkedin.com/in/brandon-davies-cs/", label="LinkedIn", icon="1️⃣")
with col7:
    st.image("https://live.staticflickr.com/5622/22160892602_e5474a698d_w.jpg")
    st.page_link("https://github.com/Da-lat/", label="Github", icon="2️⃣")
with col8:
    st.image("https://images.unsplash.com/photo-1596526131083-e8c633c948d2?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D")
    st.page_link("https://www.linkedin.com/newsletters/7170962682852859904/", label="My Newsletter", icon="3️⃣")
with col9:
    st.image("https://images.unsplash.com/photo-1666875753105-c63a6f3bdc86?q=80&w=2073&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", use_column_width="auto")
    st.page_link("https://public.tableau.com/app/profile/brandon.davies/vizzes", label="Tableau", icon="4️⃣")
with col10:
    st.image("https://media.licdn.com/dms/image/D560BAQGChCB_hK7nQw/company-logo_200_200/0/1719257926517/elegance_group_nz_logo?e=2147483647&v=beta&t=PIoQsPcECJd4wAHkUugj4NygaUp1J-ooy-9dYJ_AKgM")
    st.page_link("https://elegancegroup.co.nz/", label="Elegance Group", icon="5️⃣")

# Donate
st.write("***")
st.write("Everything is free to use here forever, if you are enjoying using this app, please consider making a donation. It would be greatly appreciated and will support upkeep fees.")
st.markdown(
        """
    <a href='https://ko-fi.com/Y8Y312122A' target='_blank'><img height='36' style='border:0px;height:36px;' 
    src='https://storage.ko-fi.com/cdn/kofi2.png?v=3' border='0' 
    alt='Buy Me a Coffee at ko-fi.com' /></a>
    """,
         unsafe_allow_html=True,
)