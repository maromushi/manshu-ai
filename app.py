import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

st.title("万舟AI")
st.write("レース画像をアップしてください")

uploaded_file = st.file_uploader("画像アップロード", type=["png","jpg","jpeg"])


# =====================
# OCR
# =====================

def ocr_image(img):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)

    gray = cv2.GaussianBlur(gray,(3,3),0)

    _,th = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)

    config="--psm 6 -c tessedit_char_whitelist=0123456789."

    txt = pytesseract.image_to_string(
        th,
        lang="eng",
        config=config
    )

    return txt


# =====================
# 展示表検出
# =====================

def detect_table(image):

    img = np.array(image)

    h,w = img.shape[:2]

    # 下25%を展示表とする
    y1 = int(h * 0.75)

    table = img[y1:h, :]

    return table


# =====================
# 列検出
# =====================

def split_columns(img):

    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    proj=np.sum(gray,axis=0)

    cols=[]

    width=img.shape[1]

    step=width//4

    for i in range(4):

        x1=i*step
        x2=(i+1)*step

        cols.append(img[:,x1:x2])

    return cols


# =====================
# 行検出
# =====================

def split_rows(img):

    h=img.shape[0]

    step=h//6

    rows=[]

    for i in range(6):

        y1=i*step
        y2=(i+1)*step

        rows.append(img[y1:y2,:])

    return rows


# =====================
# 数字抽出
# =====================

def extract_numbers(text):

    nums=re.findall(r"\d+\.\d+|\d+",text)

    fixed=[]

    for n in nums:

        try:

            v=float(n)

            if v>200:
                continue

            fixed.append(round(v,2))

        except:
            pass

    return fixed


# =====================
# MAIN
# =====================

if uploaded_file:

    image = Image.open(uploaded_file)

    img=np.array(image)

    st.image(img,use_column_width=True)

    table = detect_table(img)

    st.subheader("展示表")

    st.image(table,use_column_width=True)

    columns = split_columns(table)

    texts=[]

    for col in columns:

        rows = split_rows(col)

        for r in rows:

            txt=ocr_image(r)

            texts.append(txt)

    all_text="\n".join(texts)

    st.subheader("OCR全文")

    st.text(all_text)

    numbers=extract_numbers(all_text)

    st.subheader("抽出数字")

    st.write(numbers)
    st.write(numbers)
