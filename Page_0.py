import streamlit as st

# Labelling
st.sidebar.markdown("# Home 🛸")
st.sidebar.markdown("Feel free to navigate through the different pages, choose your input and let the magic happen!")
st.title("Home 🛸")
st.write("Welome to the Swiss Army Knife of summarising media options!")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.page_link("Page_1.py", label="Youtube", icon="🎈")
with col2:
    st.page_link("Page_2.py", label="PDF", icon="📄")
with col3:
    st.page_link("Page_3.py", label="URL", icon="💻", disabled=True)
with col4:
    st.page_link("Page_4.py", label="CSV", icon="📈")
with col5:
    st.page_link("Page_5.py", label="Text", icon="🔤")