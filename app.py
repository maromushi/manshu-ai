import streamlit as st

st.title("万舟AI")

st.write("画像をアップしてください")

uploaded_file = st.file_uploader("レース画像", type=["png","jpg","jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="アップロード画像", use_column_width=True)
    st.write("画像を受け取りました")
