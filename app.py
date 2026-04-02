import streamlit as st

st.title("万舟AI")

# ====================================
# NORMALIZE
# =====================================

def normalize(values):

    valid = [v for v in values if v is not None]

    if len(valid) == 0:
        return [0]*len(values)

    mn = min(valid)
    mx = max(valid)

    if mx-mn < 1e-6:
        return [0.5 if v is not None else 0 for v in values]

    return [
       ((v-mn)/(mx-mn)) if v is not None else 0
       for v in values
    ]

data = st.text_area("抽出データを貼り付け")

venue = st.selectbox(
    "会場",
    ["浜名湖","蒲郡","常滑","多摩川","びわこ","その他"],
    index=0
)

if st.button("計算"):

    if not data:
        st.write("データを貼ってください")
        st.stop()

    local_vars={}

    try:
        exec(data,{"__builtins__":{}},local_vars)
    except:
        st.write("抽出データの形式が正しくありません")
        st.stop()
        
    WinRate=local_vars.get("WinRate",[0]*6)
    PlaceRate=local_vars.get("PlaceRate",[0]*6)

    AvgST=local_vars.get("AvgST",[0]*6)

    Motor2=local_vars.get("Motor2",[0]*6)
    Boat2=local_vars.get("Boat2",[0]*6)

    ExTime=local_vars.get("ExTime",[0]*6)
    ExST=local_vars.get("ExST",[0]*6)

    TurnTime=local_vars.get("TurnTime",[0]*6)
    LapTime=local_vars.get("LapTime",[0]*6)
    StraightTime=local_vars.get("StraightTime",[0]*6)

    Class=local_vars.get("Class",["B1"]*6)
    Fcount=local_vars.get("Fcount",[0]*6)
    ExEntry=local_vars.get("ExEntry",[1,2,3,4,5,6])

    Boat=[1,2,3,4,5,6]

    # ↓ここから万舟AIコード

    import itertools
            

    # =====================================
    # FIX FUNCTIONS
    # =====================================

    def fix_length(arr, fill=0):

        arr=list(arr)

        if len(arr)<6:
            arr+=[fill]*(6-len(arr))

        return arr[:6]

    def to_float_list(arr):

        out=[]

        for x in arr:

            try:
                out.append(float(x))
            except:
                out.append(0.0)

        return out

    def to_int_list(arr):

        out=[]

        for x in arr:

            try:
                out.append(int(x))
            except:
                out.append(0)

        return out

    def clamp(arr, lo, hi):

        out=[]

        for x in arr:

            if x<lo or x>hi:
                out.append(0.0)
            else:
                out.append(x)

        return out

    def fix_class(arr):

        allowed=["A1","A2","B1","B2"]

        out=[]

        for x in arr:

            if x in allowed:
                out.append(x)
            else:
                out.append("B1")

        return fix_length(out,"B1")

    def fix_exentry(arr):

        try:
            arr=[int(x) for x in arr]
        except:
            return [1,2,3,4,5,6]

        if len(arr)!=6:
            return [1,2,3,4,5,6]

        if set(arr)!={1,2,3,4,5,6}:
            return [1,2,3,4,5,6]

        return arr

    # =====================================
    # SANITIZE INPUT
    # =====================================

    # ① 先に欠場判定
    Active = [1]*6

    for i in range(6):
        if WinRate[i]==0 and PlaceRate[i]==0:
            Active[i]=0

    # ② そのあと補正
    avg_win = sum([WinRate[i] for i in range(6) if Active[i]==1])/max(1,sum(Active))

    WinRate=[
        x if Active[i]==1 else 0
        for i,x in enumerate(WinRate)
    ]
    PlaceRate=clamp(to_float_list(fix_length(PlaceRate)),0,100)

    AvgST=clamp(to_float_list(fix_length(AvgST)),0,0.40)

    Motor2=clamp(to_float_list(fix_length(Motor2)),0,100)
    Boat2=clamp(to_float_list(fix_length(Boat2)),0,100)

    # モーター0補正
    avg_motor = sum([Motor2[i] for i in range(6) if Active[i]==1]) / max(1,sum(Active))
    Motor2 = [
        Motor2[i] if Active[i]==1 else 0.0
        for i in range(6)
    ]

    avg_boat = sum([Boat2[i] for i in range(6) if Active[i]==1]) / max(1,sum(Active))

    Boat2 = [
        Boat2[i] if Active[i]==1 else 0.0
        for i in range(6)
    ]
    
    ExTime=clamp(to_float_list(fix_length(ExTime)),6,8)
    ExST=clamp(to_float_list(fix_length(ExST)),0,0.40)

    TurnTime=to_float_list(fix_length(TurnTime))
    LapTime=to_float_list(fix_length(LapTime))
    StraightTime=to_float_list(fix_length(StraightTime))

    Class=fix_class(Class)

    Fcount=to_int_list(fix_length(Fcount))

    ExEntry=fix_exentry(ExEntry)

    ExhibitionF=[0,0,0,0,0,0]

    # =====================================
    # AI CORE
    # =====================================

    def run_ai(order):

        FC=[Fcount[i] for i in order]
        
        CLS=[Class[i] for i in order]
        
        boats = [
            Boat[i] if Active[i]==1 else -1
            for i in order
        ]

        WR=[WinRate[i] for i in order]
        PR=[PlaceRate[i] for i in order]

        ST=[AvgST[i] for i in order]

        M=[Motor2[i] for i in order]
        BO=[Boat2[i] for i in order]

        ET=[ExTime[i] for i in order]
        EST=[ExST[i] for i in order]

        TT=[TurnTime[i] for i in order]
        LT=[LapTime[i] for i in order]
        STT=[StraightTime[i] for i in order]

        # ===============================
        # SKILL
        # ===============================

        WinScore=normalize(WR)
        PlaceScore=normalize(PR)

        SkillRaw=[WinScore[i] for i in range(6)]
        Skill=SkillRaw 
        
        # ===============================
        # ENGINE
        # ===============================

        EngineRaw=[M[i]/100 for i in range(6)]

        Engine = []

        for i in range(6):

            if Active[i]==0:
                Engine.append(0)
                continue

            motor_ratio = M[i] / max(avg_motor,1e-6)

            factor = 0.90+ 0.10*motor_ratio

            Engine.append(EngineRaw[i] * factor)

        # ===============================
        # EXHIBIT
        # ===============================

        AvgEx=sum(ET)/6

        TimeScore=normalize([AvgEx-x for x in ET])
        ExSTScore=normalize([0.30-x for x in EST])

        ExhibitRaw=[0.80*TimeScore[i]+0.20*ExSTScore[i] for i in range(6)]

        Exhibit=[]

        for i in range(6):

            cls = CLS[i]

            if cls == "A1":
                factor = 1.00
            elif cls == "A2":
                factor = 0.92
            elif cls == "B1":
                factor = 0.80
            else:  
                factor = 0.65

            Exhibit.append(ExhibitRaw[i]*factor)

        # ===============================
        # FOOT
        # ===============================

        AvgTurn=sum(TT)/6
        AvgLap=sum(LT)/6
        AvgStraight=sum(STT)/6

        TurnScore=normalize([AvgTurn-x for x in TT])
        LapScore=normalize([AvgLap-x for x in LT])
        StraightScore=normalize([AvgStraight-x for x in STT])

        RawFoot=[
        0.42*TurnScore[i]+
        0.28*LapScore[i]+
        0.25*StraightScore[i]+
        0.08*Exhibit[i]
        for i in range(6)
        ]

        Foot=RawFoot

        for i in range(6):

            if Active[i]==0:
                continue

            motor_ratio = M[i] / max(avg_motor,1e-6)

            Foot[i] *= (0.90 + 0.10*motor_ratio)

        # 外は展示過信を少し下げる
        for i in range(6):
            if i >= 4:
                Foot[i] *= 0.95

        # ===============================
        # START
        # ===============================

        BaseStart = ([0.30 - x for x in ST])
        ExhibitStart = ([0.30 - x for x in EST])
        
        StartRaw=[0.75*BaseStart[i]+0.25*ExhibitStart[i] for i in range(6)]

        Start=StartRaw
        # F補正（階級 + 展示ST）

        F_TABLE = {
        "A1":{"F1":0.96,"F2":0.92},
        "A2":{"F1":0.94,"F2":0.88},
        "B1":{"F1":0.92,"F2":0.84},
        "B2":{"F1":0.88,"F2":0.78}
        }

        for i in range(6):

            cls = CLS[i]

            factor = 1

            if FC[i] == 1:
                factor = F_TABLE[cls]["F1"]

            elif FC[i] >= 2:
                factor = F_TABLE[cls]["F2"]

            # 展示ST補正
            if EST[i] <= 0.10:
                factor *= 1.10

            elif EST[i] <= 0.13:
                factor *= 1.05

            elif EST[i] >= 0.20:
                factor *= 0.90

            Start[i] *= factor
            
            # 遅いSTペナルティ（基本）

            penalty = 1.0
            
            if ST[i] > 0.20:
                Start[i] *= 0.90

            if ST[i] > 0.25:
                Start[i] *= 0.80

            # A1は軽減だけ（打ち消さない）
            if CLS[i] == "A1":
                penalty = max(penalty, 0.85)
            
            Start[i] *= penalty
    
        # ===============================
        # TURN
        # ===============================

        TurnRaw=[0.30*Skill[i]+0.55*Foot[i]+0.15*Engine[i] for i in range(6)]
        Turn=TurnRaw

        # ===============================
        # VELOCITY
        # ===============================

        VelocityRaw=[0.45*Foot[i]+0.35*Engine[i]+0.20*Start[i] for i in range(6)]
        Velocity=VelocityRaw

        for i in range(6):
            if i >= 4 and Engine[i] > 0.60:
                Velocity[i] *= 1.05

        # ===============================
        # INSIDE SURVIVAL
        # ===============================

        InsideSurvival=[
        0.40*Skill[i]+
        0.30*Engine[i]+
        0.20*Start[i]+
        0.10*Foot[i]
        for i in range(6)
        ]

        # ===============================
        # CPI
        # ===============================

        CPI=[
        0.20*Skill[i]+
        0.20*Engine[i]+
        0.22*Foot[i]+
        0.18*Turn[i]+
        0.20*Velocity[i]
        for i in range(6)
        ]

        AttackCPI=[
        0.35*Foot[i]+
        0.25*Turn[i]+
        0.20*Start[i]+
        0.20*Engine[i]
        for i in range(6)
        ]

        AttackIndex=[
        0.40*Start[i]+
        0.30*Foot[i]+
        0.20*Turn[i]+
        0.10*Engine[i]
        for i in range(6)
        ]

        OuterCluster = max(CPI[3:6]) - min(CPI[3:6])
        OuterClusterFlag = 1 if OuterCluster <= 0.06 else 0

        # ===== 6頭検知フラグ =====

        SixHeadFlag = 0

        if (
            CPI[5] >= max(CPI[3:6]) - 0.02
            and Start[5] >= Start[3] - 0.01
            and Engine[5] >= 0.58
            and (
                InsideSurvival[0] < 0.55
                or Start[0] < Start[1] - 0.03
            )
        ):
            SixHeadFlag = 1

        # ===============================
        # MID CLUSTER
        # ===============================

        MidCluster=max(CPI[1:4])-min(CPI[1:4])
        MidClusterFlag=1 if MidCluster<=0.05 else 0

        PerformanceSpread=max(CPI)-min(CPI)

        StartSpread=max(Start)-min(Start)

        InsideCollapse = 1 if (StartSpread > 0.10 and OuterClusterFlag == 1) else 0

        # ===============================
        # EXHIBIT LEADER
        # ===============================

        min_exst = min(EST)

        ExhibitLeader = [0]*6

        for i in range(6):
            if EST[i] == min_exst:
                ExhibitLeader[i] = 1

        # ===============================
        # SASHI CHANCE
        # ===============================

        SashiGap=[0]*6

        for i in range(1,6):
            SashiGap[i]=max(0,Start[i]-Start[i-1])
    
        # ===============================
        # ATTACK FLAG
        # ===============================

        TwoLaneAttackFlag = 1 if (
        Start[1] <= Start[0] + 0.05
        ) else 0

        ThreeLaneAttackFlag = 1 if (
        Start[2] <= Start[1] + 0.04
        ) else 0

        FourLaneAttackFlag = 1 if (
        Start[3] <= min(Start[1],Start[2]) + 0.02
        ) else 0

        # ===============================
        # ATTACK SCORE
        # ===============================

        TwoLaneAttackScore = (
        0.22 * TwoLaneAttackFlag +
        0.28 * max(0, Start[1] - Start[0]) +
        0.22 * max(0, AttackCPI[1] - AttackCPI[0]) +
        0.15 * max(0, Engine[1] - Engine[0]) +
        0.13 * max(0, Turn[1] - Turn[0])
        )

        ThreeLaneAttackScore = (
        0.22 * ThreeLaneAttackFlag +
        0.28 * max(0, Start[2] - Start[1]) +
        0.22 * max(0, AttackCPI[2] - AttackCPI[0]) +
        0.15 * max(0, Engine[2] - Engine[0]) +
        0.13 * max(0, Turn[2] - Turn[0])
        )

        FourLaneAttackScore = (
        0.22 * FourLaneAttackFlag +
        0.28 * max(0, Start[3] - Start[2]) +
        0.22 * max(0, AttackCPI[3] - AttackCPI[0]) +
        0.15 * max(0, Engine[3] - Engine[0]) +
        0.13 * max(0, Turn[3] - Turn[0])
        )

        OutsideFlow = (
        0.6*ThreeLaneAttackScore +
        0.8*FourLaneAttackScore
        )

        DoubleAttackScore = (
        (ThreeLaneAttackScore * FourLaneAttackScore)
        +
        0.5 * (TwoLaneAttackScore * ThreeLaneAttackScore)
        )

        # ===============================
        # 攻め主体判定（改良版）
        # ===============================

        Attack2 = 1 if (
            Start[1] > Start[0] + 0.02
            and AttackIndex[1] > AttackIndex[0]
            and (Foot[1] >= Foot[0] or Engine[1] >= Engine[0])
        ) else 0


        Attack3 = 1 if (
            Start[2] > Start[1] + 0.02
            and AttackIndex[2] > AttackIndex[1]
            and (Foot[2] >= Foot[1] or Engine[2] >= Engine[1])
            and (
                CLS[2] in ["A1","A2"]
                or (
                    ExST[2] <= 0.05
                    and Start[2] >= Start[1]   # ★これ追加（ブレーキ）
                )
            )
        ) else 0

        Attack3Power = (
            max(0, Start[2] - Start[1]) +
            max(0, AttackIndex[2] - AttackIndex[1])
        )

        InsideBreak = 1 if (
            Start[0] < Start[1] - 0.03
            and Attack3 == 1
        ) else 0
        
        # ===============================
        # CHAOS CORE
        # ===============================

        OuterPower=(
        0.5*max(CPI[3:6])+
        0.3*sorted(CPI[3:6])[-2]+
        0.2*(sum(CPI[3:6])/3)
        )

        InsideWeak=1-InsideSurvival[0]

        ChaosScore=(
        0.20*OuterPower+
        0.25*InsideWeak+
        0.25*StartSpread+
        0.16*PerformanceSpread+
        0.05*TwoLaneAttackFlag+
        0.08*ThreeLaneAttackFlag+
        0.05*FourLaneAttackFlag+
        0.06*MidClusterFlag
        )

        ChaosScore=max(0,min(1,ChaosScore))

        if ChaosScore < 0.45:
            chaos_weight = 0.7   # 安定レース
        elif ChaosScore < 0.65:
            chaos_weight = 1.0   # 通常
        else:
            chaos_weight = 1.3   # 荒れ
            
        # ===============================
        # AUTO MODE 判定
        # ===============================
        
        race_score = 0
        
        # イン弱い
        if Skill[0] < 0.45:
            race_score += 1
        
        # スタートばらつき
        if max(Start) - min(Start) > 0.08:
            race_score += 1
        
        # 外強い
        if max(CPI[3:6]) > CPI[0]:
            race_score += 1
        
        # 展開あり
        if DoubleAttackScore > 0.08:
            race_score += 1
        
        # 判定
        use_mode = "ana" if race_score >= 2 else "safe"

        
        # ===============================
        # STAGE17
        # ===============================

        AvgStart=sum(Start)/6

        StartBoost=[]

        for i in range(6):

            value=1+(0.25+0.35*ChaosScore)*(Start[i]-AvgStart)

            value=max(0.75,value)

            StartBoost.append(value)

        DynamicInsideFactor=1

        if StartSpread>=0.12:
            DynamicInsideFactor=0.70
        elif StartSpread>=0.08:
            DynamicInsideFactor=0.82

        DynamicInsideFactor=max(0.60,DynamicInsideFactor)

        # ===== イン過信抑制 =====

        if CPI[1] >= CPI[0] - 0.05 and Start[1] <= Start[0] + 0.04:
            DynamicInsideFactor *= 0.88

        LaneWin=[

        0.58*DynamicInsideFactor*(1-0.25*ChaosScore),
        0.19+(0.45*(1-DynamicInsideFactor)*0.40)*(1+0.20*ChaosScore),
        0.16+(0.45*(1-DynamicInsideFactor)*0.30)*(1+0.25*ChaosScore),
        0.14+(0.45*(1-DynamicInsideFactor)*0.20)*(1+0.30*ChaosScore),
        0.07+(0.45*(1-DynamicInsideFactor)*0.07)*(1+0.35*ChaosScore),
        0.04+(0.45*(1-DynamicInsideFactor)*0.03)*(1+0.40*ChaosScore)

        ]

        # ===== 2差し強化補正 =====

        if CPI[1] >= CPI[0] - 0.03 and Start[1] <= Start[0] + 0.03:

            LaneWin[1] += 0.07
            LaneWin[0] -= 0.07

        elif CPI[1] >= CPI[0] - 0.06 and Start[1] <= Start[0] + 0.05:

            LaneWin[1] += 0.04
            LaneWin[0] -= 0.04

        FirstScore=[
        0.35*Start[i]+
        0.25*Skill[i]+
        0.15*Engine[i]+
        0.15*Foot[i]+
        0.20*Turn[i]+
        0.15*LaneWin[i]
        for i in range(6)
        ]
        
        # ===============================
        # ★ 主役取りこぼし（最重要）
        # ===============================
        if (
            CLS[3] == "A1"
            and DoubleAttackScore > 0.05
            and Start[3] <= Start[2] + 0.01
        ):
            FirstScore[3] *= 0.90
            
        # ===============================
        # ★ イン事故復活（これ）
        # ===============================
        if (
            CLS[0] in ["B1","B2"]
            and DoubleAttackScore < 0.08
        ):
            FirstScore[0] *= 1.08
        
        # ===============================
        # ★ 6の強さ分類（追加）
        # ===============================
        Strong6 = (
            CLS[5] == "A1"
            and CPI[5] >= 0.52
            and Start[5] >= Start[3] - 0.02
        )
        
        Normal6 = (
            CPI[5] >= 0.45
            and Foot[5] >= 0.48
        )
        
        SemiStrong6 = (
            CLS[5] == "A2"
            and CPI[5] >= 0.55
            and Start[5] >= Start[3] - 0.01
            and DoubleAttackScore > 0.08
        )
        
        # ===============================
        # ★ 低性能カット（ここ）
        # ===============================
        for i in range(6):
        
            if Foot[i] < 0.45 and Engine[i] < 0.50:
                FirstScore[i] *= 0.80
        
            if Foot[i] < 0.40:
                FirstScore[i] *= 0.75

        # ===============================
        # ★ 攻め不発（最重要）
        # ===============================
        NoAttackFlag = 0

        if (
            StartSpread < 0.08
            and DoubleAttackScore < 0.06
        ):
            NoAttackFlag = 1
        
        if NoAttackFlag == 1:
        
            # イン残りはするが“信頼しすぎない”
            if InsideSurvival[0] >= 0.60:
                FirstScore[0] *= 1.10
            else:
                FirstScore[0] *= 1.03

            if Skill[0] < 0.50:
                FirstScore[0] *= 0.92

            # ★ ここ追加（これ）
            if Skill[0] < 0.55:
                FirstScore[0] *= 0.95
        
            FirstScore[1] *= 0.95
            FirstScore[2] *= 0.95
            FirstScore[3] *= 0.95
        
            FirstScore[4] *= 0.85
            FirstScore[5] *= 0.75
        
            # 2・3は“攻めない”
            FirstScore[1] *= 0.95
            FirstScore[2] *= 0.95
            FirstScore[3] *= 0.95
        
            # 外はさらに弱く
            FirstScore[4] *= 0.85


        # ===============================
        # ★ 弱イン分散（最重要）
        # ===============================
        if NoAttackFlag == 1 and Skill[0] < 0.55:
        
            # 1の支配を崩す
            FirstScore[0] *= 0.88
        
            # 3・4を主役に引き上げる
            FirstScore[2] *= 1.08
            FirstScore[3] *= 1.10

        # ★ 1の過集中防止
        if NoAttackFlag == 1 and Start[0] < max(Start[1:4]):
            FirstScore[0] *= 0.90

        # ===============================
        # ★ 攻め競合（共倒れ）
        # ===============================
        if (
            Turn[2] > 0.55
            and Turn[3] > 0.55
            and abs(Turn[2] - Turn[3]) < 0.04
            and DoubleAttackScore > 0.06
        ):
            # 共倒れ
            FirstScore[2] *= 0.90
            FirstScore[3] *= 0.85
        
            # 外浮上（重要）
            for i in range(4,6):
                FirstScore[i] *= 1.05
        
        # ===============================
        # ★ イン安定補正（これが本命）
        # ===============================
        
        if (
            Skill[0] >= 0.50
            and Start[0] >= 0.13
            and InsideSurvival[0] >= 0.55
        ):
            FirstScore[0] *= 1.25
            
        # ←ここに入れる👇
        
        # ★ 差し役なのにスタート遅い → 消す
        if Start[1] < Start[0] - 0.02:
            FirstScore[1] *= 0.85
            
        if Start[1] > Start[0] + 0.03:
            FirstScore[1] *= 0.90
            
        # ===============================
        # ★ 攻め条件（←ここ！！！）
        # ===============================
        if (
            Turn[2] == max(Turn)
            and Foot[2] >= Foot[1]
            and DoubleAttackScore > 0.06   # ←これ追加
        ):
            FirstScore[2] *= 1.25
            
        # ★ 3の展示攻め補強（追加）
        if (
            Start[2] >= Start[1] + 0.02
            and ExST[2] <= 0.05
        ):
            FirstScore[2] *= 1.15
        
        # ===============================
        # ★ イン残り補正（追加）
        # ===============================
        if Skill[0] >= 0.45 and Start[0] >= 0.13:
            FirstScore[0] *= 1.10
        
        if Start[0] >= 0.14:
            FirstScore[0] *= 1.05
            
        # ===============================
        # ★ 3のまくり差し強化（超重要）
        # ===============================
        if (
            Skill[2] >= 0.50
            and Foot[2] >= max(Foot[0], Foot[1])
            and Turn[2] >= max(Turn[0], Turn[1])
            and DoubleAttackScore > 0.06   # ←これ追加
        ):
            FirstScore[2] *= 1.20
            
        # ===============================
        # ★ 2のエンジン過信抑制（追加）
        # ===============================
        if Engine[1] > 0.60 and Turn[1] < Turn[2]:
            FirstScore[1] *= 0.88
        
        # ===============================
        # ★ 外A1複数 → 軸分散モード
        # ===============================
        
        outer_a1 = 0

        for i in range(4,6):  # 5・6コース
            if CLS[i] == "A1" and Engine[i] >= 0.55:
                outer_a1 += 1
        
        if outer_a1 >= 2:
        
            for i in range(4,6):
                if CLS[i] == "A1":
                    FirstScore[i] *= 1.15   # 外の頭を引き上げ
        
            # イン少し弱める
            FirstScore[0] *= 0.90
            FirstScore[1] *= 0.95

        # ===== イン最低保証 =====
        if Skill[0] >= 0.55 and Engine[0] >= 0.50:
            FirstScore[0] *= 1.08

        # ===== 2差し直撃補正（最重要） =====

        #if CPI[1] >= CPI[0] - 0.03 and Start[1] <= Start[0] + 0.02:

            #FirstScore[1] *= 1.12
            #FirstScore[0] *= 0.92

        elif CPI[1] >= CPI[0] - 0.06 and Start[1] <= Start[0] + 0.05:

            FirstScore[1] *= 1.03
            FirstScore[0] *= 0.95
            
        # ★ 2の頭制限（これが本命）
        if DoubleAttackScore > 0.06:
            FirstScore[1] *= 0.96
            
        # ===============================
        # ★ 2の頭精査（これが正解）
        # ===============================
        if FirstScore[1] >= max(FirstScore)*0.95:
        
            # 攻め展開なら2は頭じゃない
            if DoubleAttackScore > 0.06:
                FirstScore[1] *= 0.88
        
            # 4が強いなら2は頭じゃない
            if Turn[3] >= Turn[1] and Foot[3] >= Foot[1]:
                FirstScore[1] *= 0.90
            
            
        # ===============================
        # ★ イン残り補正（A1＋A2）
        # ===============================
        if CLS[0] == "A1":
            if Start[0] >= 0.13:
                FirstScore[0] *= 1.12
        
        elif CLS[0] == "A2":
            if Start[0] >= 0.14 and InsideSurvival[0] >= 0.52:
                FirstScore[0] *= 1.08
        
        elif CLS[0] == "B1":
            if (
                Start[0] >= 0.15
                and InsideSurvival[0] >= 0.55
                and DoubleAttackScore < 0.08
            ):
                FirstScore[0] *= 1.05
                
        # ===============================
        # ★ 会場補正（ここに入れる）
        # ===============================
        
        if venue == "多摩川":
            DynamicInsideFactor *= 1.08
            FirstScore[0] *= 1.10
        
        if venue == "びわこ":
            if StartSpread > 0.10:
                chaos_weight *= 0.9
        
        
        # ===============================
        # ★ 攻め役の勝ち切り制限（5）
        # ===============================
        if (
            ExST[4] <= 0.05
            and Start[4] >= Start[2] - 0.02
        ):
            if not (
                Foot[4] >= max(Foot[1:4])
                or Turn[4] >= max(Turn[1:4])
            ):
                FirstScore[4] *= 0.85

        # ===============================
        # ST遅い艇の頭抑制（追加）
        # ===============================
        AvgStart = sum(Start)/6

        for i in range(6):
            if Start[i] < AvgStart - 0.04:
                FirstScore[i] *= 0.82

        # 外の1着抑制（重要）
        for i in range(6):

            if i >= 4:
                
                if outer_a1 >= 2:
                    continue  # ←外A1強い時は絶対殺さない
        
                # ===== 6コース =====
                if i == 5:
            
                    if Strong6:
                        FirstScore[5] *= 1.18
            
                    elif SemiStrong6:
                        FirstScore[5] *= 1.08
                        
                    elif Normal6:
                        FirstScore[5] *= 0.95
            
                    else:
                        if Start[5] < Start[0]:
                            FirstScore[5] *= 0.70
                        else:
                            FirstScore[5] *= 0.85
            
                # ===== 5コース =====
                elif i == 4:
            
                    if CLS[4] == "A1":
                        FirstScore[4] *= 1.08
                    elif CLS[4] == "A2":
                        FirstScore[4] *= 1.02
                    else:
                        FirstScore[4] *= 0.80

        # 6頭の最終ブレーキ
        if Start[5] < Start[0] - 0.01:
            FirstScore[5] *= 0.70
        
        elif Start[5] <= Start[1] or Start[5] <= Start[0]:
            FirstScore[5] *= 0.80
            
        # ===============================
        # ★ 6の展開連動ブースト（ここ）
        # ===============================
        if (
            DoubleAttackScore > 0.10
            and Start[5] >= Start[3] - 0.005
            and CLS[5] == "A1"
        ):
            FirstScore[5] *= 1.08
        
        if use_mode == "safe":
            FirstScore[0] *= 1.08
                
            for i in range(6):

                # 弱いイン削る
                if i == 0 and Skill[i] < 0.45:
                    FirstScore[i] *= 0.75
                        
                # ===============================
                #  外の頭条件化（修正）
                # ===============================
                if i >= 4:
                    if AttackIndex[i] < max(AttackIndex):
                        FirstScore[i] *= 0.70
                        

        # ===== 6頭処理 =====

        # ★ 条件を強化（ここが本質）
        StrongSixHead = (
            CPI[5] >= 0.60
            and Start[5] >= Start[3]
            and DoubleAttackScore > 0.10
        )
        
        if SixHeadFlag == 1 and StrongSixHead:
        
            boost = 1.15 + 0.25 * (CPI[5] - 0.50)
        
            if Engine[5] >= 0.60:
                boost += 0.03
        
            FirstScore[5] *= boost
            FirstScore[0] *= 0.85
            FirstScore[1] *= 0.90
        
        else:
        
            # ===== 6抑制（強弱分岐） =====
            
            if Normal6:
                FirstScore[5] *= 0.95
        
            if CPI[5] < 0.50:
                FirstScore[5] *= 0.60
        
            elif Start[5] < Start[3]:
                FirstScore[5] *= 0.70
        
            else:
                FirstScore[5] *= 0.80
                
            # ===============================
            # ★ 6の頭制限（これ追加）
            # ===============================
            if i == 5:
                if not (
                    DoubleAttackScore > 0.10
                    and Start[5] >= Start[3]
                    and CPI[5] >= 0.55
                ):
                    FirstScore[5] *= 0.70
                    
            # ===============================
            # ★ 2号艇の主役補正（追加）
            # ===============================
            
            if (
                Turn[1] == min(Turn)   # 最速ターン
                and LapTime[1] == min(LapTime)  # 周回も最速
            ):
                # 2が一番強い場合
                FirstScore[1] *= 1.12
            
                # 逆に外の攻めすぎを抑える
                FirstScore[4] *= 0.92
                
            


        # ===============================
        # ★ 攻め不発補正
        # ===============================
        if NoAttackFlag == 1:
        
            # イン残り強化
            FirstScore[0] *= 1.15
        
            # 攻め側弱める
            FirstScore[2] *= 0.92
            FirstScore[3] *= 0.92

        # ★ 6の最終制御（絶対必要）
        if FirstScore[5] == max(FirstScore) and not (Strong6 or Normal6):
            FirstScore[5] *= 0.92
            
        # ===============================
        # ★ 弱インなら強制攻め
        # =============================
            
        # 弱イン補正
            
        if AvgST[0] > 0.20:
            FirstScore[0] *= 0.92
            
        # ===============================
        # ★ 攻め展開時の外強化
        # ===============================
        
        if NoAttackFlag == 0:

            if DoubleAttackScore > 0.09:
                FirstScore[2] *= 1.10
                FirstScore[3] *= 1.12
                FirstScore[0] *= 0.92
        
            elif DoubleAttackScore > 0.04:
                FirstScore[2] *= 1.05
                FirstScore[3] *= 1.06
                FirstScore[0] *= 0.98   # ←ここが本質
        
            else:
                FirstScore[0] *= 1.05
            
        # ===============================
        # ★ 2の過剰頭抑制（最重要）
        # ===============================
        if FirstScore[1] >= max(FirstScore)*0.95:
        
            # 攻め展開なら2は頭じゃない
            if DoubleAttackScore > 0.06:
                FirstScore[1] *= 0.88
        
            # 4が強い時も頭じゃない
            if Turn[3] >= Turn[1] and Foot[3] >= Foot[1]:
                FirstScore[1] *= 0.90
                
        # ===============================
        # ★ 中間展開のイン復活（最重要）
        # ===============================
        if (
            DoubleAttackScore > 0.04
            and DoubleAttackScore < 0.09
            and NoAttackFlag == 0
        ):
            FirstScore[0] *= 1.12

        # ===============================
        # ATTACK BOOST
        # ===============================

        OuterPowerCheck = max(AttackCPI[3:6])

        AttackBoost1 = max(
        0.70,
        1 - 0.25 * max(
        TwoLaneAttackScore,
        ThreeLaneAttackScore,
        FourLaneAttackScore
        )
        )

        AttackBoost2 = 1 + 0.20 * TwoLaneAttackScore
        AttackBoost3 = 1 + 0.30 * ThreeLaneAttackScore
        AttackBoost4 = 1 + 0.25 * FourLaneAttackScore
        AttackBoost5 = 1 + 0.35 * DoubleAttackScore
        AttackBoost6 = 1 + 0.25 * DoubleAttackScore

        AttackBoost=[
        AttackBoost1,
        AttackBoost2,
        AttackBoost3,
        AttackBoost4,
        AttackBoost5,
        AttackBoost6
        ]

        if OuterPowerCheck < 0.55:
            AttackBoost[3] *= 0.85
            AttackBoost[4] *= 0.80
            AttackBoost[5] *= 0.75

        outer_attackers = AttackIndex[3:6]

        max_outer = max(outer_attackers)

        main_attacker = None

        if OuterClusterFlag == 1:
            for j in range(3,6):
                AttackBoost[j] *= 1.10

        if max_outer > AttackIndex[2] + 0.03:
            main_attacker = outer_attackers.index(max_outer) + 3

        # ===============================
        # 展開モデル
        # ===============================

        CrashFactor=[1.0]*6
        SashiBoost=[1.0]*6

        if main_attacker is not None:

            attack_power = DoubleAttackScore

            # 前潰れ
            for j in range(main_attacker):
                CrashFactor[j] = 1 - 0.15*attack_power

            # 差し
            for j in range(main_attacker+1,6):
                SashiBoost[j] = 1 + 0.12*attack_power
          
        LaneCPI=[]

        for i in range(6):

            if Active[i] == 0:
                LaneCPI.append(0)
                continue

            value=(
                CPI[i]*
                LaneWin[i]*
                (0.8+0.2*StartBoost[i]*chaos_weight)*
                CrashFactor[i]*
                SashiBoost[i]*
                AttackBoost[i]
            )


            if i == 0 and InsideBreak == 1:
                value *= 0.70

            if i == 0 and CLS[0] in ["A1","A2"]:
                value *= 1.15

            # イン崩壊
            if InsideCollapse == 1:
                if i <= 2:
                    value *= 0.88

            # 外まとまり
            if OuterClusterFlag == 1:
                if i >= 4:
                    value *= 1.01
                    

            # ===============================
            # 2まくり（弱め）
            # ===============================
            if Attack2 == 1:

                if i == 0:
                    value *= 0.90

                if i == 1:
                    value *= 1.18

                if i == 2:
                    value *= 0.92

                if i >= 3:
                    value *= 1.05

            # ===============================
            # 3まくり（弱め）
            # ===============================
            if Attack3 == 1:

                if i == 0:
                    value *= 0.85

                if i == 1:
                    value *= 0.90

                if i == 2:

                    if CLS[2] in ["B1","B2"]:

                        if Attack3Power < 0.05:
                            value *= 0.90

                        elif Attack3Power < 0.10:
                            value *= 1.00

                        else:
                            value *= 1.10

                    else:
                        value *= 1.10

                if i >= 3:
                    value *= 1.06

            if Attack3 == 1 and CLS[2] in ["B1","B2"] and i >= 4:
                value *= 0.85

            if Attack3 == 1 and Attack3Power < 0.08:

                if i == 1:
                    value *= 1.20

                if i == 0:
                    value *= 1.05
            
            # 展開艇補正
            if ExhibitLeader[i] == 1 and i >= 3:
                value *= 1.08

            # 差し補正
            if i==1:
                value*=1+0.22*SashiGap[i]
            elif i==2:
                value*=1+0.15*SashiGap[i]
            elif i==3:
                value*=1+0.08*SashiGap[i]
            elif i==4:
                value*=1+0.04*SashiGap[i]
        
            if main_attacker is not None:

                if i == main_attacker:
                    value = value*(1+0.20*DoubleAttackScore)

                elif i > main_attacker:
                    value = value*(1+0.08*DoubleAttackScore)

                elif i == main_attacker - 1:
                    value *= (1+0.06*DoubleAttackScore)

            LaneCPI.append(value)
            
        # ★ デバッグここ
        debug_log = []

        debug_log.append(("FirstScore", [round(x,3) for x in FirstScore]))
        debug_log.append(("順位", sorted(range(6), key=lambda i: FirstScore[i], reverse=True)))
        debug_log.append(("CPI", [round(x,3) for x in CPI]))
        debug_log.append(("Start", [round(x,3) for x in Start]))

        TotalFirst = sum([FirstScore[i] for i in range(6) if Active[i]==1])

        if TotalFirst <= 0:
            TotalFirst = 1e-6
        
        P1 = [
        (FirstScore[i]/TotalFirst) if Active[i]==1 else 0
        for i in range(6)
        ]

        # ===============================
        # トップ集中ブースト
        # ===============================
        top = max(P1)

        for i in range(6):
            if P1[i] == top:        
                P1[i] *= 1.05

        # ===== 正規化 =====

        total_p1 = sum(P1)

        if total_p1 > 0:
            P1 = [p / total_p1 for p in P1]

        LaneBonus=[0.10,0.09,0.08,0.07,0.06,0.05]

        SecondScore=[
        0.33*Turn[i]+
        0.27*Foot[i]+
        0.20*Engine[i]+
        0.10*Velocity[i]+
        0.10*LaneBonus[i]
        for i in range(6)
        ]
        
        
        
        # ===============================
        # ★ 階級補正（最重要）
        # ===============================
        for i in range(6):
        
            if CLS[i] == "A1":
                SecondScore[i] *= 1.05
        
            elif CLS[i] == "A2":
                SecondScore[i] *= 1.03
        
            elif CLS[i] == "B2":
                SecondScore[i] *= 0.95
                

        
        # ===============================
        # ★ 中途半端展開（イン残り＋外1枚）
        # ===============================
        if (
            DoubleAttackScore > 0.04
            and DoubleAttackScore < 0.09
        ):
            SecondScore[1] *= 1.08
            SecondScore[3] *= 1.05
        
        
        # ===============================
        # ★ 外の“展開じゃない強さ”を拾う（これ）
        # ===============================
        for i in range(4,6):
        
            # 展開なくても強い外を拾う
            if (
                CLS[i] in ["A1","A2"]
                and Start[i] >= Start[3] - 0.02
                and (
                    Foot[i] >= 0.48
                    or CPI[i] >= 0.46
                )
            ):
                SecondScore[i] *= 1.15
        
        # ===============================
        # ★ 強制外シナリオ（ここ！！）
        # ===============================
        #if DoubleAttackScore > 0.07:
        
            #for i in range(4,6):
                #SecondScore[i] *= 1.25
        
        #for i in range(6):
        
            # 外のポテンシャル艇を救う
            #if i >= 4:
                #if Foot[i] >= 0.50 or CPI[i] >= 0.48:
                    #SecondScore[i] *= 1.20
                    
        
        # ===============================
        # ★ 外の勝者だけ残す（5・6共通）
        # ===============================
        outer_max = max(CPI[4], CPI[5])
        
        for i in range(4,6):
        
            if CPI[i] >= outer_max - 0.03:
        
                if DoubleAttackScore > 0.07:
                    SecondScore[i] *= (1 + 0.25 * DoubleAttackScore)
        
            else:
                SecondScore[i] *= 0.97
        
        
        # ===============================
        # ★ 展開6（性能じゃない6を拾う）
        # ===============================
        if (
            DoubleAttackScore > 0.10
            and Start[5] >= Start[3] - 0.01
            and CLS[5] in ["A1","A2"]
            and Foot[5] >= 0.50
        ):
            SecondScore[5] *= 1.12
        
        # ===============================
        # ★ 外残りフラグ（5・6用）
        # ===============================
        
        FlowOuter = (
            DoubleAttackScore > 0.08
            or OuterClusterFlag == 1
        )
        
        FiveFlowFlag = (
            FlowOuter
            and (
                Foot[4] >= 0.48
                or CPI[4] >= 0.46
            )
            and Start[4] >= Start[2] - 0.03
        )
        
        SixFlowFlag = (
            FlowOuter
            and (
                Foot[5] >= 0.50
                or CPI[5] >= 0.48
            )
            and Start[5] >= Start[3] - 0.03
        )    
        
        # ===============================
        # ★ 2着強化
        # ===============================
        
        if FiveFlowFlag:
            SecondScore[4] *= 1.20
        

        # ===============================
        # ★ 6の過剰2着抑制（追加）
        # ===============================
        
        if NoAttackFlag == 1:
            SecondScore[5] *= 0.85


        # ===== 2の差し残り強化 =====

        if (
            CPI[1] >= CPI[0] - 0.05
            and Fcount[1] == 0   # ←これ追加
        ):
            SecondScore[1] *= 1.10
            
        # ===============================
        # ★ F持ち最終補正（完全版）
        # ===============================
        for i in range(6):
        
            if Fcount[i] >= 1:

                if Fcount[i] == 1:
            
                    if CLS[i] == "A1":
                        factor = 0.97
                    elif CLS[i] == "A2":
                        factor = 0.95
                    elif CLS[i] == "B1":
                        factor = 0.93
                    else:
                        factor = 0.90
            
                elif Fcount[i] >= 2:
            
                    if CLS[i] == "A1":
                        factor = 0.92
                    elif CLS[i] == "A2":
                        factor = 0.88
                    elif CLS[i] == "B1":
                        factor = 0.85
                    else:
                        factor = 0.80
            
                # 差し役は少しだけ追加ペナ
                if i in [1,2]:
                    factor *= 0.97
            
                SecondScore[i] *= factor


        # ===== 6の2着残り強化 =====

        SixSecondFlag = 0

        if (
            CPI[5] >= 0.50
            and Foot[5] >= 0.55
            and (
                DoubleAttackScore > 0.06
                or OuterClusterFlag == 1
            )
        ):
            SixSecondFlag = 1

            # 1〜3を少し削る（前残り崩れ）
            SecondScore[0] *= 0.92
            SecondScore[1] *= 0.95
            SecondScore[2] *= 0.97

        else:

            # 弱い6はしっかり消す
            if Foot[5] < 0.45:
                SecondScore[5] *= 0.90
            else:
                SecondScore[5] *= 1.00
                

        ThirdScore=[
        0.28*Velocity[i]+
        0.28*Foot[i]+
        0.20*Engine[i]+
        0.14*LaneBonus[i]+
        0.10*InsideSurvival[i]
        for i in range(6)
        ]
    
        # ===============================
        # ★ インの2着・3着粘り復活
        # ===============================
        
        if (
            CLS[0] in ["A1","A2"]
            and Start[0] >= 0.13
        ):
            SecondScore[0] *= 1.12
            ThirdScore[0] *= 1.08
        
        # ===============================
        # ★ 展開艇の3着流入（最重要）
        # ===============================
        for i in range(6):
        
            if (
                ExST[i] <= 0.05
                and DoubleAttackScore > 0.04
            ):
                ThirdScore[i] *= 1.20
        
        # ===============================
        # ★ 3と4が完全に競ってる時だけ
        # ===============================
        if (
            DoubleAttackScore > 0.04
            and DoubleAttackScore < 0.09
            and abs(CPI[2] - CPI[3]) < 0.03
        ):
            ThirdScore[2] *= 0.95
        
        # ===============================
        # ★ 5の3着軽拾い（ここ）
        # ===============================
        for i in range(6):
            if i == 4 and CPI[4] >= 0.42:
                ThirdScore[4] *= 1.05
        
        # ===============================
        # ★ 1の過剰残り抑制（ここ）
        # ===============================
        if (
            DoubleAttackScore > 0.08
            and Start[0] < Start[2] - 0.02
        ):
            ThirdScore[0] *= 0.90
        
        # ===============================
        # ★ 2の残り復活（ここに入れる）
        # ===============================
        if (
            Start[1] >= Start[0] - 0.02
            and CPI[1] >= 0.45
        ):
            SecondScore[1] *= 1.12
            ThirdScore[1] *= 1.08

        
        # ===============================
        # ★ 強制外シナリオ（ここ！！）
        # ===============================
        if DoubleAttackScore > 0.07:
        
            for i in range(4,6):
                ThirdScore[i] *= 1.30
        
        
        # ===============================
        # ★ 外の最低保証
        # ===============================
        for i in range(4,6):
            if CPI[i] >= 0.46:
                ThirdScore[i] *= 1.15
                
        # ★ 外の単発強者（追加）
        if (
            Engine[4] >= 0.55
            and Start[4] >= Start[2] - 0.03
        ):
            ThirdScore[4] *= 1.15
        
        # ===============================
        # ★ 外の勝者だけ残す（5・6）
        # ===============================
        outer_max = max(CPI[4], CPI[5])
        
        for i in range(4,6):
        
            if CPI[i] >= outer_max - 0.03:
        
                if DoubleAttackScore > 0.07:
                    ThirdScore[i] *= (1 + 0.30 * DoubleAttackScore)
        
            else:
                ThirdScore[i] *= 0.88
                
        # ===============================
        # ★ 外単独強者救済（これが本命）
        # ===============================
        for i in range(4,6):
        
            if (
                Start[i] >= Start[3] - 0.02
                and Foot[i] >= 0.48
            ):
                SecondScore[i] *= 1.10
        
        
        # ===============================
        # ★ 展開6（性能じゃない6）
        # ===============================
        if (
            DoubleAttackScore > 0.08
            and Start[5] >= Start[3] - 0.02
            and CLS[5] in ["A1","A2"]
        ):
            ThirdScore[5] *= 1.25
        
        # ===============================
        # ★ 3着強化
        # ===============================
        
        if FiveFlowFlag:
            ThirdScore[4] *= 1.15
        
        if SixFlowFlag:
            ThirdScore[5] *= 1.20

        # ===== 3号艇の自然流入 =====

        if 0.43 <= CPI[2] <= 0.62:
            ThirdScore[2] *= 1.12

        # ===============================
        # ★ 弱外でも展開なら残す（最重要）
        # ===============================
        for i in range(4,6):
        
            if (
                DoubleAttackScore > 0.06
                and Start[i] >= Start[2] - 0.03
            ):
                ThirdScore[i] *= 1.10

        results=[]
            
        # ===============================
        # ★ 非頭艇の残り補正（最重要）
        # ===============================
            
        for a in range(6):

            if Active[a] == 0:
                continue
        
            P_first = P1[a]
        
            SecondAdj = SecondScore.copy()
            ThirdAdj = ThirdScore.copy()
            
            # ===============================
            # ★ 6の2着侵食ストップ（本命修正）
            # ===============================
            
            # 6が「展開で2着に来れる状態」か？
            valid_six_second = (
                DoubleAttackScore > 0.08
                and Start[5] >= Start[3] - 0.02
                and Foot[5] >= 0.50
            )
            
            # それ以外は2着をしっかり削る
            if not valid_six_second:
                SecondAdj[5] *= 0.65   # ←ここがキモ（強め）
            
            # ===============================
            # ★ 6の2着・3着まとめて制御
            # ===============================
            
            # --- 2着用 ---
            strong_flow6 = (
                DoubleAttackScore > 0.10
                and Start[5] >= Start[3] - 0.02
            )
            
            light_flow6 = (
                DoubleAttackScore > 0.06
                and Start[5] >= Start[2] - 0.03
            )
            
            six_power = (
                Foot[5] >= 0.50
                or CPI[5] >= 0.48
            )
            
            if not ((strong_flow6 or light_flow6) and six_power):
                SecondAdj[5] *= 0.85
            
            
            # --- 3着用 ---
            flow6 = (
                DoubleAttackScore > 0.08
                and Start[5] >= Start[3] - 0.02
            )
            
            six_ok = (
                Foot[5] >= 0.48
                or CPI[5] >= 0.48
            )
            
            if not (flow6 and six_ok):
                ThirdAdj[5] *= 0.85
            
            # ===============================
            # ★ 5を2着に引き上げる（核心）
            # ===============================
            if (
                i == 4
                and DoubleAttackScore > 0.05
                and Start[4] >= Start[2] - 0.03
            ):
                SecondAdj[4] *= 1.25
                
            if i >= 4:
                if Foot[i] >= 0.50 or CPI[i] >= 0.48:
                    ThirdAdj[i] *= 1.10
            
            # ===============================
            # ★ 3着候補の繰り上げ（最重要）
            # ===============================
        
            # ★ここに入れる
            for i in range(6):
        
                if i != a:

                    # ★ 外の序列補正（最重要）
                    if i > a:
                    
                        if Start[i] >= Start[a] - 0.02:
                    
                            attack_center = max(range(2,6), key=lambda x: AttackIndex[x])
            
                        
            # ===============================
            # ★ 展開ライン連動（最重要）
            # ===============================
            if (
                DoubleAttackScore > 0.06
                and NoAttackFlag == 0
            ):
            
                attack_center = max(range(2,6), key=lambda x: AttackIndex[x])
            
                for j in range(6):
            
                    if j > attack_center:
                        ThirdAdj[j] *= 1.15
            
                    if j == attack_center + 1:
                        ThirdAdj[j] *= 1.20
            
            # ===============================
            # ★ 弱頭でも残り計算させる（最重要）
            # ===============================
            if (
                P1[a] < 0.15
                and DoubleAttackScore > 0.08
            ):
                P_first *= 1.10
            
            # ===============================
            # ★ 頭弱い艇の残り救済（最重要）
            # ===============================
            outer_power = max(CPI[4:6])

            if (
                outer_power > CPI[a] + 0.02
                and DoubleAttackScore > 0.06
            ):
                ThirdAdj[5] *= 1.30
            
                SecondAdj[4] *= 1.10
                ThirdAdj[4] *= 1.15
            
            if NoAttackFlag == 1:
                
                # イン残り
                SecondAdj[0] *= 1.10
                ThirdAdj[0] *= 1.08
            
                # 3の残り（ちゃんと効かせる）
                SecondAdj[2] *= 1.10
                ThirdAdj[2] *= 1.10
            
                # 攻め役だけ少し削る（軽く）
                SecondAdj[3] *= 0.95        

            # ===============================
            # ★ 共倒れ時の着順補正
            # ===============================
            if (
                Turn[2] > 0.55
                and Turn[3] > 0.55
                and abs(Turn[2] - Turn[3]) < 0.04
            ):
            
                # 3・4の残りを削る
                SecondAdj[2] *= 0.90
                SecondAdj[3] *= 0.90
            
                ThirdAdj[2] *= 0.90
                ThirdAdj[3] *= 0.90
            
                # 外と内に流す
                SecondAdj[5] *= 1.02
                ThirdAdj[5] *= 1.05
            
                SecondAdj[0] *= 1.05
                ThirdAdj[0] *= 1.05

            
            # ===============================
            # ★ 3頭時の2過剰抑制
            # ===============================
            if a == 2:  # 3号艇が1着
                if Turn[2] > Turn[1]:
                    SecondAdj[1] *= 0.92
            
            # 残り5艇（ここ追加）
            remain1 = [i for i in range(6) if i != a and Active[i] == 1]
    
            for i in range(6):

                dist = i - a
            
                if dist < 0:
                    SecondAdj[i] *= (1 - 0.04*DoubleAttackScore)                  
                    ThirdAdj[i] *= (1 - 0.06*DoubleAttackScore)
            
                elif dist == 1:
                    SecondAdj[i] *= 1.12
                    ThirdAdj[i] *= 1.08
            
                elif dist >= 2:
                    SecondAdj[i] *= 1.03
                    ThirdAdj[i] *= 1.00

                if i >= 4:

                    if i == 5:
                        if not (Strong6 or Normal6):

                            # ★ 展開6は殺さない
                            if not (
                                DoubleAttackScore > 0.08
                                and Start[i] >= Start[3] - 0.02
                            ):
                                if not (
                                    i == 5
                                    and DoubleAttackScore > 0.08
                                    and Start[i] >= Start[3] - 0.02
                                ):
                                    if Foot[i] < 0.50:
                                        ThirdAdj[i] *= 0.95
                    else:
                        if Foot[i] < 0.55:
                            SecondAdj[i] *= 0.90
                            
                    # ===== 外の残り再設計 =====
                    if i >= 4:
                    
                        if (
                            Start[i] >= Start[2] - 0.03
                            and (
                                Foot[i] >= 0.48
                                or CPI[i] >= 0.46
                            )
                        ):
                            SecondAdj[i] *= 1.12
                            ThirdAdj[i] *= 1.08
            
                # ===============================
                # 内残り（条件付きに変更）
                # ===============================
                if i <= 2 and InsideSurvival[i] > 0.55:
                    ThirdAdj[i] *= 1.03
            
                # インのしぶとさ（少し弱め）
                if i == 0:
                    ThirdAdj[i] *= 1.02
            
                # ===============================
                # 3着バランス補正（シンプル版）
                # ===============================

                # 基本位置
                if i == 2:   # 3号艇
                    ThirdAdj[i] *= 1.10
                elif i == 3: # 4号艇
                    ThirdAdj[i] *= 1.08
                elif i == 4:
                
                    if DoubleAttackScore > 0.06:
                        ThirdAdj[i] *= 1.05
                    else:
                        ThirdAdj[i] *= 0.98
                        
                elif i == 5: # 6号艇

                    if Foot[i] < 0.50:
                        ThirdAdj[i] *= 0.90   # 弱いときだけ削る
                
                    else:
                        ThirdAdj[i] *= 1.00   # 基本はあまり削らない

                # 展開ある時だけ6を少し戻す
                if i == 5 and DoubleAttackScore > 0.08:
                    ThirdAdj[i] *= 1.10

                # 弱すぎる艇だけ削る
                if Skill[i] < 0.30:
                    ThirdAdj[i] *= 0.90  
                    
            # ===============================
            # ★ 4頭時の6流入（ここに入れる）
            # ===============================
            
                
                
            if (
                a == 3
                and Strong6
            ):
                SecondAdj[5] *= 1.10
                    

            second_scores = [
                SecondAdj[i] if Active[i]==1 else 0
                for i in remain1
            ]
            total2=sum(second_scores)

            if total2<=0:
                total2=1e-6

            second_probs=[s/total2 for s in second_scores]

            for idx_b,b in enumerate(remain1):
                if Active[b] == 0:
                    continue

                P_second = second_probs[idx_b]

                remain2=[i for i in remain1 if i!=b and Active[i]==1]

                third_scores = [
                ThirdAdj[i] if Active[i]==1 else 0
                for i in remain2
                ]
                total3=sum(third_scores)

                if total3<=0:
                    total3=1e-6

                third_probs=[s/total3 for s in third_scores]

                for idx_c,c in enumerate(remain2):

                    if Active[c] == 0:
                        continue

                    P_third = third_probs[idx_c]

                    p = P_first * P_second * P_third
                    
                    if boats[a] != -1 and boats[b] != -1 and boats[c] != -1:
                        results.append((boats[a],boats[b],boats[c],p))

        return results, ChaosScore, P1, DoubleAttackScore, InsideSurvival, debug_log
    # =====================================
    # 進入パターン
    # =====================================

    order_waku=[0,1,2,3,4,5]

    order_ex=[x-1 for x in ExEntry if x>0]

    if len(order_ex)!=6:
        order_ex=[0,1,2,3,4,5]

    res_waku, chaos1, P1_waku, DAS1, IS1, debug_log = run_ai(order_waku)
    res_ex, chaos2, P1_ex, DAS2, IS2, debug_log = run_ai(order_ex)

    ChaosScore = 0.3 * chaos1 + 0.7 * chaos2
    P1 = P1_ex
    DoubleAttackScore = DAS2
    InsideSurvival = IS2
    # =====================================
    # 合成
    # =====================================

    final={}

    for a,b,c,p in res_waku:

        key=(a,b,c)

        final[key]=final.get(key,0)+0.3*p

    for a,b,c,p in res_ex:

        key=(a,b,c)

        final[key]=final.get(key,0)+0.7*p

    results=[(k[0],k[1],k[2],v) for k,v in final.items()]
    
    # ===============================
    # ★ シャープ化 & 正規化 & カット
    # ===============================
    
    # ① シャープ化
    power = 1.30 + 0.30 * ChaosScore
    
    results = [
        (a,b,c, p**power)
        for (a,b,c,p) in results
    ]
    
    # ② 正規化
    total = sum(r[3] for r in results)
    
    if total > 0:
        results = [
            (a,b,c, p/total)
            for (a,b,c,p) in results
        ]
    
    filtered = []

    for r in results:
    
        p = r[3]
    
        # 中穴ゾーン保護
        if 0.01 <= p <= 0.03:
            filtered.append(r)
    
        # 通常カット条件
        elif p >= 0.004:
            filtered.append(r)
    
    results = filtered

    results.sort(key=lambda x:x[3],reverse=True)

    # ===============================
    # 予想信頼度
    # ===============================

    if len(results) >= 2:
        TopGap = results[0][3] - results[1][3]
    else:
        TopGap = 0


    # =====================================
    # OUTPUT
    # =====================================

    Coverage = 0
    Final = []
    
    target = 0.78 + 0.12 * ChaosScore
    
    # ★ 追加（超重要）
    max_bets = int(8 + 8 * ChaosScore)   # 8〜16点に制御
    
    for r in results:
    
        Coverage += r[3]
        Final.append(r)
    
        # カバレッジ条件
        if Coverage >= target:
            break
    
        # ★ 点数制限（最重要）
        if len(Final) >= max_bets:
            break

    unique = {}

    for a,b,c,p in Final:
        key = (a,b,c)
        if key not in unique or unique[key] < p:
            unique[key] = p
    
    Final = [(k[0],k[1],k[2],v) for k,v in unique.items()]

    # ===============================
    # ★ここに追加（これだけ）
    # ===============================
    
    # 例：2コース凹みっぽい時だけ
    dent_flag = False
    
    # 簡易判定（まずこれでOK）
    if AvgST[1] > 0.18 or ExST[1] > 0.18:
        if DoubleAttackScore > 0.06:
            dent_flag = True
    
    # 追加
    if dent_flag:
        Final.append((4,6,2,0.001))  # 確率は適当でOK（表示用）

                    
    # ===============================
    # ★ マーク付け（修正版）
    # ===============================
    
    sorted_final = sorted(Final, key=lambda x: x[3], reverse=True)
    top_p = sorted_final[0][3]
    top_set = set([tuple(x[:3]) for x in sorted_final[:5]])
    
    marked = []
    
    for (a,b,c,p) in Final:
    
        
        head_p = P1[a-1]

        if (a,b,c) in top_set:
    
            if a-1 == top_head and p >= top_p * 0.9:
                mark = "◎"
    
            elif p >= top_p * 0.75:
                mark = "○"
    
            elif DoubleAttackScore > 0.06 and a >= 3:
                mark = "▲"
    
            else:
                mark = "▲"
    
        else:
            mark = "△"
    
        marked.append((mark,a,b,c,p))
                
    # △の中でも弱いの消す
    filtered_marked = []
        
    for mark,a,b,c,p in marked:
        
        if mark == "△" and (p < 0.025 or P1[a-1] < 0.12):
            continue
        
        filtered_marked.append((mark,a,b,c,p))
        
    marked = filtered_marked
    
    # ===============================
    # 表示
    # ===============================
            
    for m in marked:
        mark,a,b,c,p = m
        st.write(f"{mark} {a}-{b}-{c} ({round(p,4)})")

    # ===============================
    # ★ コピペ用出目
    # ===============================
    
    copy_text = "\n".join([
        f"{r[0]}-{r[1]}-{r[2]} ({round(r[3],4)})"
        for r in Final
    ])
    
    st.text_area("コピペ用", copy_text, height=200)
    
    st.write("▼デバッグ")
    
    for name, val in debug_log:
        st.write(name, val)    
          

  
