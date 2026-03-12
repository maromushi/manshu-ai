import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re


st.title("万舟AI")

st.write("レース画像をアップしてください")

uploaded_file = st.file_uploader("画像アップロード", type=["png","jpg","jpeg"])


def ocr_image(image):

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]

    text = pytesseract.image_to_string(thresh, lang="jpn")

    return text



def extract_numbers(text):

    numbers = re.findall(r"\d+\.\d+|\d+", text)

    numbers = [float(n) for n in numbers]

    return numbers



def parse_boat_data(text):

    boats = []

    lines = text.split("\n")

    for line in lines:

        nums = re.findall(r"\d+\.\d+|\d+", line)

        if len(nums) >= 3:

            boats.append(nums)

    return boats

def split_sections(text):

    sections = {}

    keys = [
        "基本情報",
        "勝率",
        "今節成績",
        "直前情報",
        "展示情報",
        "オリジナル展示"
    ]

    current = None

    for line in text.split("\n"):

        for k in keys:
            if k in line:
                current = k
                sections[current] = []
                break

        if current:
            sections[current].append(line)

    return sections

if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="アップロード画像", use_column_width=True)


    with st.spinner("OCR解析中..."):

        text = ocr_image(image)


    st.subheader("抽出テキスト")

    st.text(text)


    numbers = extract_numbers(text)

    st.subheader("抽出数字")

    st.write(numbers)


    boats = parse_boat_data(text)

    st.subheader("艇データ候補")

    st.write(boats)


    sections = split_sections(text)

    st.subheader("セクション分割")

    st.write(sections)
