import streamlit as st

st.write('Welcome to app2!')
st.write('app2 secret is...' + st.secrets['app2']['the_secret'])