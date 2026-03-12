import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re

st.title("万舟AI")
st.write("レース画像をアップしてください")

uploaded_file = st.file_uploader("画像アップロード", type=["png","jpg","jpeg"])


# ==========================
# OCRエンジン
# ==========================

def ocr_image(image):

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)

    gray = cv2.GaussianBlur(gray,(5,5),0)

    gray = cv2.equalizeHist(gray)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    config="--psm 6 -c tessedit_char_whitelist=0123456789./-"

    text1 = pytesseract.image_to_string(
        thresh,
        lang="eng",
        config=config
    )

    inv=cv2.bitwise_not(thresh)

    text2 = pytesseract.image_to_string(
        inv,
        lang="eng",
        config=config
    )

    if len(text2)>len(text1):
        return text2
    else:
        return text1


# ==========================
# 展示部分切り出し
# ==========================

def split_image_sections(image):

    img=np.array(image)

    h,w=img.shape[:2]

    y1=int(h*0.65)

    return img[y1:h,:]


# ==========================
# 列分割
# ==========================

def split_columns(image):

    img=np.array(image)

    h,w=img.shape[:2]

    col_width=int(w/4)

    cols=[]

    for i in range(5):

        x1=i*col_width
        x2=(i+1)*col_width

        crop=img[:,x1:x2]

        cols.append(crop)

    return cols


# ==========================
# 行分割（6艇）
# ==========================

def split_rows(image):

    img=np.array(image)

    h,w=img.shape[:2]

    rows=[]

    row_h=int(h/6)

    for i in range(6):

        y1=i*row_h
        y2=(i+1)*row_h

        crop=img[y1:y2,:]

        rows.append(crop)

    return rows


# ==========================
# OCR結果修正
# ==========================

def fix_numbers(numbers):

    fixed=[]

    for n in numbers:

        try:

            s=str(n)

            # 連結修正
            parts=re.findall(r"\d+\.\d+",s)

            if len(parts)>=2:

                for p in parts:
                    fixed.append(float(p))

                continue

            v=float(n)

            if v>200:
                continue

            fixed.append(round(v,2))

        except:
            pass

    return fixed


# ==========================
# 数字抽出
# ==========================

def extract_numbers(text):

    return re.findall(r"\d+\.\d+|\d+",text)


# ==========================
# メイン
# ==========================

if uploaded_file:

    image=Image.open(uploaded_file)

    st.image(image,use_column_width=True)

    table=split_image_sections(image)

    st.subheader("展示切り出し")

    st.image(table,use_column_width=True)

    columns=split_columns(table)

    texts=[]

    for col in columns:

        rows=split_rows(col)

        for r in rows:

            txt=ocr_image(r)

            texts.append(txt)

    all_text="\n".join(texts)

    st.subheader("OCR全文")

    st.text(all_text)

    numbers=extract_numbers(all_text)

    numbers=fix_numbers(numbers)

    st.subheader("抽出数字")

    st.write(numbers)
