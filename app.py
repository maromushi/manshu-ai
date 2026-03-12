import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

st.title("万舟AI")

st.write("レース画像をアップしてください")

uploaded_file = st.file_uploader("画像アップロード", type=["png","jpg","jpeg"])


# ----------------------------
# OCR処理
# ----------------------------

def ocr_image(image):

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # OCR精度向上のため拡大
    scale = 2
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # ノイズ除去
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    # 二値化
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    config = "--psm 6"

    text = pytesseract.image_to_string(thresh, lang="jpn", config=config)

    return text


# ----------------------------
# 数字抽出
# ----------------------------

def extract_numbers(text):

    numbers = re.findall(r"\d+\.\d+|\d+", text)

    numbers = [float(n) for n in numbers]

    return numbers


# ----------------------------
# OCRテキストから艇データ候補抽出
# ----------------------------

def parse_boat_data(text):

    boats = []

    lines = text.split("\n")

    for line in lines:

        nums = re.findall(r"\d+\.\d+|\d+", line)

        if len(nums) >= 3:

            boats.append(nums)

    return boats


# ----------------------------
# セクション分割（テキスト）
# ----------------------------

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


# ----------------------------
# 画像を6分割
# ----------------------------

def split_image_sections(image):

    img = np.array(image)

    h, w = img.shape[:2]

    sections = {}

    sections["基本情報"] = img[int(h*0.00):int(h*0.20), :]
    sections["勝率"] = img[int(h*0.20):int(h*0.35), :]
    sections["今節成績"] = img[int(h*0.35):int(h*0.50), :]
    sections["直前情報"] = img[int(h*0.50):int(h*0.65), :]
    sections["展示情報"] = img[int(h*0.65):int(h*0.80), :]
    sections["オリジナル展示"] = img[int(h*0.80):int(h*1.00), :]

    return sections


# ----------------------------
# メイン処理
# ----------------------------

if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="アップロード画像", use_column_width=True)

    with st.spinner("OCR解析中..."):

        sections_img = split_image_sections(image)

        sections_text = {}

        for key, img in sections_img.items():

            txt = ocr_image(img)

            sections_text[key] = txt


    st.subheader("セクションOCR結果")

    st.write(sections_text)


    all_text = "\n".join(sections_text.values())


    st.subheader("OCR全文")

    st.text(all_text)


    numbers = extract_numbers(all_text)

    st.subheader("抽出数字")

    st.write(numbers)


    boats = parse_boat_data(all_text)

    st.subheader("艇データ候補")

    st.write(boats)


    sections = split_sections(all_text)

    st.subheader("セクション分割")

    st.write(sections)
