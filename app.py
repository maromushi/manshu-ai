import streamlit as st
import ast
from logic import run_ai

st.title("ボートAI")

# ===============================
# 入力（#付きOK）
# ===============================
raw_text = st.text_area("ここに貼る（#付きOK）", "")

# ===============================
# パース（#対応版）
# ===============================
def parse_input(text):
    data = {}

    for line in text.split("\n"):

        line = line.strip()

        # ★ #削除（ここが本質）
        if line.startswith("#"):
            line = line[1:].strip()

        if "=" not in line:
            continue

        key, val = line.split("=", 1)

        try:
            data[key.strip()] = ast.literal_eval(val)
        except:
            pass

    return data

# ===============================
# 実行
# ===============================
if st.button("計算"):

    data = parse_input(raw_text)

    # 必須キー補完（最低限）
    data.setdefault("Motor2", [0]*6)
    data.setdefault("Boat2", [0]*6)
    data.setdefault("Foot", [0]*6)
    data.setdefault("Start", [0]*6)

    # ===============================
    # AI実行
    # ===============================
    result, state = run_ai(data, None)

    # ===============================
    # 順位
    # ===============================
    ranking = sorted(
        range(6),
        key=lambda i: result[i],
        reverse=True
    )

    # ===============================
    # 表示
    # ===============================
    st.subheader("結果")
    for i in range(6):
        st.write(f"{i+1}号艇: {round(result[i],3)}")

    st.subheader("順位")
    st.write([x+1 for x in ranking])

    # ===============================
    # 本線（3連単1点）
    # ===============================
    head, second, third = ranking[:3]

    st.subheader("本線")
    st.write(f"{head+1}-{second+1}-{third+1}")

    # ===============================
    # コピー用（#付き維持）
    # ===============================
    lines = []

    lines.append("# ===== INPUT =====")
    for line in raw_text.split("\n"):
        if line.strip():
            lines.append("# " + line.lstrip("# ").strip())

    lines.append("\n# ===== STATE =====")
    for k, v in state.items():
        lines.append(f"# {k}={v}")

    lines.append("\n# ===== RANK =====")
    lines.append(f"# 順位={[x+1 for x in ranking]}")

    lines.append("\n# ===== BET =====")
    lines.append(f"# 本線={head+1}-{second+1}-{third+1}")

    lines.append("\n# ===== OUTPUT =====")
    for i in range(6):
        lines.append(f"# {i+1}号艇: {round(result[i],3)}")

    full_text = "\n".join(lines)

    st.subheader("コピー用")
    st.code(full_text)