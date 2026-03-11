import streamlit as st

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Force show sidebar toggle
st.markdown("""
<style>
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: #166534 !important;
    position: fixed !important;
    left: 0 !important;
    top: 50% !important;
    width: 32px !important;
    height: 60px !important;
    z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Sidebar")
    st.write("Yeh dikh raha hai?")

st.title("Main")
st.write("Left side pe green button dikh raha hai?")
