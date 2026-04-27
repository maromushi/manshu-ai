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
# ② STATE（展開だけ）
# =====================================
def detect_state(f):

    Start = f["Start"]
    CPI = f["CPI"]

    DAS = max(Start) - min(Start)

    AttackSuccess = 1 if (
        Start[1] > Start[0] + 0.02
        or Start[2] > Start[1] + 0.02
    ) else 0

    AttackWeak = 1 if (
        DAS > 0.04 and AttackSuccess == 0
    ) else 0

    NoAttackProb = max(0, min(1, 1 - DAS/0.1))

    return {
        "DAS": DAS,
        "AttackSuccess": AttackSuccess,
        "AttackWeak": AttackWeak,
        "NoAttackProb": NoAttackProb
    }
    
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