import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np

st.title("万舟AI")

st.write("レース画像をアップしてください")

uploaded_file = st.file_uploader("画像アップロード", type=["png","jpg","jpeg"])

def ocr_image(image):
    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

    text = pytesseract.image_to_string(thresh, lang="jpn")

    return text


if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="アップロード画像", use_column_width=True)

    with st.spinner("OCR解析中..."):

        text = ocr_image(image)

    st.subheader("抽出テキスト")

    st.text(text)
