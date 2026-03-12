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

    # 拡大
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # ノイズ除去
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    # コントラスト強化
    gray = cv2.equalizeHist(gray)

    # 二値化
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    config="--psm 6 -c tessedit_char_whitelist=0123456789./AB"

    text = pytesseract.image_to_string(
        thresh,
        lang="eng",
        config=config
    )

    return text


# ----------------------------
# 数字抽出
# ----------------------------
def extract_numbers(text):

    numbers = re.findall(r"\d+\.\d+|\d+", text)

    return numbers


# ----------------------------
# OCRゴミ修正
# ----------------------------
def fix_ocr_numbers(numbers):

    fixed = []

    for n in numbers:

        try:

            v = float(n)

            # OCR連結ミス修正
            if v > 1000:
                v = v % 100

            if v > 100:
                v = v % 100

            # 不正値除外
            if v < 0:
                continue

            if v > 200:
                continue

            fixed.append(round(v,2))

        except:
            pass

    return fixed


# ----------------------------
# 艇データ候補抽出
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
# 展示部分を取得
# ----------------------------
def split_image_sections(image):

    img = np.array(image)

    h, w = img.shape[:2]

    # 画像下を展示情報と仮定
    y1 = int(h * 0.65)
    y2 = int(h * 0.100)

    table = img[y1:y2, :]

    return table


# ----------------------------
# 列分割
# ----------------------------
def split_columns(image):

    img = np.array(image)

    h, w = img.shape[:2]

    cols = []

    step = w // 5

    for i in range(5):

        x1 = i * step
        x2 = (i+1) * step

        crop = img[:, x1:x2]

        cols.append(crop)

    return cols


# ----------------------------
# メイン処理
# ----------------------------
if uploaded_file:

    image = Image.open(uploaded_file)

    st.image(image, caption="アップロード画像", use_column_width=True)

    with st.spinner("OCR解析中..."):

        table = split_image_sections(image)

        st.image(table, caption="展示表切り出し")

        columns = split_columns(table)

        texts = []

        for col in columns:

            txt = ocr_image(col)

            texts.append(txt)

    all_text = "\n".join(texts)

    st.subheader("OCR全文")
    st.text(all_text)


    numbers = extract_numbers(all_text)

    numbers = fix_ocr_numbers(numbers)

    st.subheader("抽出数字")
    st.write(numbers)


    boats = parse_boat_data(all_text)

    st.subheader("艇データ候補")
    st.write(boats)
