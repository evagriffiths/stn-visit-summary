import streamlit as st

st.write('Welcome to app1!')
st.write('app1 secret is...' + st.secrets['app1']['the_secret'])