import streamlit as st

st.set_page_config(
    page_title="CHRL Apps",
    page_icon="👋",
)

st.write("# Welcome to the CHRL App Page")

st.sidebar.success("Select an app above.")

st.markdown(
    """
    Welcome to 
    ### App1
    - This does App1 things
    ### App2
    - This does App2 things
  
"""
)
