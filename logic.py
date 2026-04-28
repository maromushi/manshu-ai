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
    
# =====================================
# ② STATE（展開だけ）
# =====================================
    
def detect_state(f):

    Start = f["Start"]
    Turn  = f["Turn"]
    Foot  = f["Foot"]
    Engine= f["Engine"]
    ExST  = f["ExST"]
    Class = f["Class"]
    ExEntry = f["ExEntry"]

    # ① 並び
    StartCollapse = 0
        
        if Start[0] < max(Start[1:4]) - 0.03:
            StartCollapse = 1
            
        # --- 並び順作成（0-index）---
        entry_order = [x-1 for x in ExEntry]
        
        # 逆引き（どの艇が何番目か）
        pos = [0]*6
        for i, boat in enumerate(entry_order):
            pos[boat] = i
        
        # --- Class係数 ---
        ClassCoef = []
        for c in Class:
            if c == "A1":
                ClassCoef.append(1.15)
            elif c == "A2":
                ClassCoef.append(1.05)
            elif c == "B1":
                ClassCoef.append(0.95)
            else:
                ClassCoef.append(0.85)
        
        # --- Fペナルティ ---
        FPenalty = []
        for f in Fcount:
            if f >= 2:
                FPenalty.append(0.75)
            elif f == 1:
                FPenalty.append(0.88)
            else:
                FPenalty.append(1.0)

    # ② 基本差分（Spread系）
    
    # ③ 壁（Wall / Break）
    #===============================
    # ★ 外統一判定（追加）
    # ===============================
    outer_ok = [False]*6
        
    for i in range(1,6):
        is_fast = Start[i] > Start[i-1] + 0.01
        
        outer_ok[i] = (
            is_fast
            and (
                DAS < 0.12
                or AttackSuccess == 1
                or AttackWeak == 1
            )
        )
        
        
    # --- 壁強度（進入順ベース）---
    Wall = [0]*6
        
    for i in range(6):
        p = pos[i]
        
        if p == 0:
            Wall[i] = 0
        else:
            w = 0
            for k in range(p):
                j = entry_order[k]
        
                base = (0.6*Start[j] + 0.4*Foot[j])
                base *= ClassCoef[j]
                base *= FPenalty[j]
        
                w += base
        
            Wall[i] = w / p
        
        
    # --- 壁制約 ---
    for i in range(6):
        if pos[i] >= 3:
            penalty = 1 - (0.35 * Wall[i])
        
            Turn[i] *= penalty
            Lap[i]  *= penalty
        
            Start[i] -= 0.015 * Wall[i]
        
        
    # --- 外上限 ---
    for i in range(6):
        if pos[i] >= 4:
            Foot[i] = min(Foot[i], 0.55)
        
    # ===============================
    # ★ 壁崩れ検知
    # ===============================
    # --- 壁崩れ ---
    WallBreak = [0]*6
        
    for i in range(6):
        p = pos[i]
        
        if p == 0:
            continue
        
        score = 0
        
        for k in range(p):
            j = entry_order[k]
        
            st_diff = Start[i] - Start[j]
            f_factor = 1 - FPenalty[j]
            foot_diff = Foot[i] - Foot[j]
        
            score += 0.5*st_diff + 0.3*f_factor + 0.2*foot_diff
        
        WallBreak[i] = max(0, score)
        
        
    # --- 壁緩和 ---
    for i in range(6):
        if pos[i] >= 3:
            relax = 1 + 0.5 * WallBreak[i]
        
            Turn[i] *= relax
            Lap[i]  *= relax
                
    # ④ 攻め候補（AttackIndex → attackers）
    
    
    # ⑤ 成否判定（Success / Weak / Fail）
    # ⑥ DAS
    # ⑦ 崩壊・ズレ・無風フラグ
    # ⑧ RaceMode

    return state
    
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