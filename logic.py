# ===============================
# UTIL
# ===============================
def normalize_sum(arr):
    s = sum(arr) + 1e-6
    return [x/s for x in arr]

# ===============================
# CORE
# ===============================
def run_ai(data, venue):
    f = calc_features(data)
    state = detect_state(f)
    P_no = sim_no_attack(f)
    P_weak = sim_weak(f)
    P_at = sim_attack(f)
    P = merge(P_no, P_weak, P_at, state)
    return P
    
# =====================================
# ① FEATURES（能力だけ）
# =====================================
def calc_features(data):

    # 必要最低限だけ（まずは軽く）
    Skill = data["WinRate"]
    Engine = data["Motor2"]
    Start = data["Start"]
    Foot = data["Foot"]

    # 正規化だけ
    Skill = normalize_sum(Skill)
    Engine = normalize_sum(Engine)
    Start = normalize_sum(Start)
    Foot = normalize_sum(Foot)

    CPI = [
        0.25*Skill[i] +
        0.25*Engine[i] +
        0.25*Start[i] +
        0.25*Foot[i]
        for i in range(6)
    ]

    return {
        "Skill": Skill,
        "Engine": Engine,
        "Start": Start,
        "Foot": Foot,
        "CPI": CPI
    }
    
# =====================================
# ② スタート計算
# =====================================
def calc_start(data):

    AvgST = data["AvgST"]
    ExST  = data["ExST"]
    Class = data["Class"]
    ExF   = data["ExhibitionF"]

    # ===============================
    # ① F補正（先に1回だけ）
    # ===============================
    BadST = [0]*6
    AdjExST = ExST.copy()

    for i in range(6):

        is_f = ExF[i] == 1
        is_abnormal = ExST[i] <= 0.02

        if is_f:

            BadST[i] = 1

            base = 0.20
            if Class[i] == "A1":
                base = 0.16
            elif Class[i] == "A2":
                base = 0.18

            AdjExST[i] = 0.7 * base + 0.3 * max(ExST[i], 0.05)

        elif is_abnormal:

            BadST[i] = 1

            if Class[i] == "A1":
                AdjExST[i] = max(0.11, ExST[i] * 0.5 + 0.07)
            elif Class[i] == "A2":
                AdjExST[i] = max(0.115, ExST[i] * 0.5 + 0.075)
            else:
                AdjExST[i] = max(0.13, ExST[i] * 0.5 + 0.09)

    # ===============================
    # ② Start算出
    # ===============================
    Start = []

    for i in range(6):

        st = AvgST[i]
        ex = AdjExST[i]

        # 展示補正
        if ex <= 0:
            ex = 0.18

        if ex < 0.10:
            ex = ex * 0.85 + 0.015
        elif ex < 0.20:
            ex = ex * 0.90 + 0.01

        # trust
        diff = abs(ex - st)

        t = 1.0
        if diff > 0.12:
            t *= 0.7
        if diff > 0.20:
            t *= 0.5

        # 合成
        val = (1 - t)*(0.30 - st) + t*(0.30 - ex)

        Start.append(val)

    return normalize_sum(Start)
    
def detect_state(f):

    Start = f["Start"]
    Turn  = f["Turn"]
    Foot  = f["Foot"]

    # ===============================
    # ① 基本差分
    # ===============================
    StartSpread = max(Start) - min(Start)

    # ===============================
    # ② 攻め候補（シンプル版）
    # ===============================
    attackers = []

    for i in range(1,6):

        reach = Start[i] >= Start[i-1] - 0.01

        pressure = (
            Start[i] > Start[i-1]
            or Turn[i] > Turn[i-1] + 0.02
            or Foot[i] > Foot[i-1] + 0.03
        )

        if reach and pressure:
            attackers.append(i)

    # ===============================
    # ③ 攻め成功判定
    # ===============================
    AttackSuccess = 0

    if attackers:

        atk = attackers[0]

        st_win = Start[atk] > Start[atk-1] + 0.02
        turn_win = Turn[atk] > Turn[atk-1] + 0.03

        if st_win or turn_win:
            AttackSuccess = 1

    # ===============================
    # ④ DAS（攻め強度）
    # ===============================
    DAS = (
        max(0, Start[2] - Start[1]) +
        max(0, Start[3] - Start[2]) +
        max(0, Start[4] - Start[3])
    )

    DAS += StartSpread * 0.5

    # ===============================
    # ⑤ スタート崩壊
    # ===============================
    StartCollapse = 1 if (
        Start[0] < max(Start[1:4]) - 0.03
    ) else 0

    # ===============================
    # ⑥ 弱攻め
    # ===============================
    AttackWeak = 0

    if attackers and AttackSuccess == 0:

        atk = attackers[0]

        near = (
            Start[atk] >= Start[atk-1] - 0.01
            or Turn[atk] >= Turn[atk-1] - 0.01
        )

        if near:
            AttackWeak = 1

    # ===============================
    # ⑦ 無風判定
    # ===============================
    NoAttackFlag = 1

    if (
        AttackSuccess == 1
        or DAS > 0.08
        or StartSpread > 0.06
        or StartCollapse == 1
    ):
        NoAttackFlag = 0

    # ===============================
    # ⑧ RaceMode
    # ===============================
    if AttackSuccess:
        RaceMode = "attack_success"

    elif DAS > 0.08:
        if AttackWeak:
            RaceMode = "attack_weak"
        else:
            RaceMode = "attack"

    elif StartCollapse:
        RaceMode = "collapse"

    else:
        RaceMode = "no_attack"

    # ===============================
    # 返却
    # ===============================
    return {
        "attackers": attackers,
        "AttackSuccess": AttackSuccess,
        "AttackWeak": AttackWeak,
        "DAS": DAS,
        "StartCollapse": StartCollapse,
        "NoAttackFlag": NoAttackFlag,
        "RaceMode": RaceMode
    }
    
# =====================================
# 世界①（1逃げ）
# =====================================
    
def sim_no_attack(f):

    CPI = f["CPI"]

    P1 = normalize_sum([
        1.2*CPI[0],  # イン強化
        CPI[1],
        CPI[2],
        CPI[3],
        0.7*CPI[4],
        0.5*CPI[5],
    ])

    return P1
    
# =====================================
# 世界②（攻め）
# =====================================

def sim_attack(f):

    Start = f["Start"]
    CPI = f["CPI"]

    P1 = normalize_sum([
        0.7*CPI[0],
        1.2*CPI[1] if Start[1] > Start[0] else CPI[1],
        1.2*CPI[2] if Start[2] > Start[1] else CPI[2],
        CPI[3],
        CPI[4],
        CPI[5],
    ])

    return P1
    
# =====================================
# 世界②（弱攻め
# =====================================
def sim_weak(f):

    CPI = f["CPI"]

    P1 = normalize_sum([
        0.9*CPI[0],
        1.05*CPI[1],
        1.05*CPI[2],
        CPI[3],
        CPI[4],
        CPI[5],
    ])

    return P1
    
# =====================================
# 合成
# =====================================
    
def merge(P_no, P_weak, P_at, state):

    w_no = state["NoAttackProb"]
    w_at = 1 - w_no
    w_weak = 0.3

    P = [0]*6

    for i in range(6):
        P[i] = (
            w_no * P_no[i] +
            w_at * P_at[i] +
            w_weak * P_weak[i]
        )

    return normalize_sum(P)