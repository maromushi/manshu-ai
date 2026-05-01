import streamlit as st

from logic import run_ai

if st.button("計算"):

    result = run_ai(local_vars, venue)

    st.write(result)