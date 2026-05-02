import streamlit as st
import ast
from logic import run_ai

st.title(“ボートAI（最終版）”)

===============================

入力（貼り付け）

===============================

st.subheader(“データ貼り付け”)

raw_text = st.text_area(“ここにそのまま貼る”, “”)

===============================

パース

===============================

def parse_input(text):
data = {}
for line in text.strip().split(”\n”):
if “=” not in line:
continue
key, val = line.split(”=”, 1)
try:
data[key.strip()] = ast.literal_eval(val)
except:
pass
return data

===============================

実行

===============================

if st.button(“計算”):