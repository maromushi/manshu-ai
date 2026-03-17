import streamlit as st

st.title("万舟AI")

data = st.text_area("抽出データを貼り付け")

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
    # NORMALIZE
    # =====================================

    def normalize(values):

        mn=min(values)
        mx=max(values)

        if mx-mn<1e-6:
            return [0.5]*len(values)

        return [(v-mn)/(mx-mn) for v in values]

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

    WinRate=clamp(to_float_list(fix_length(WinRate)),0,10)
    # 勝率0補正
    avg_win = sum(WinRate)/6
    WinRate=[x if x>0 else avg_win*0.9 for x in WinRate]

    PlaceRate=clamp(to_float_list(fix_length(PlaceRate)),0,100)

    AvgST=clamp(to_float_list(fix_length(AvgST)),0,0.40)

    Motor2=clamp(to_float_list(fix_length(Motor2)),0,100)
    Boat2=clamp(to_float_list(fix_length(Boat2)),0,100)

    # モーター0補正
    avg_motor=sum(Motor2)/6
    if avg_motor==0:
        avg_motor=50    
    Motor2=[x if x>0 else avg_motor for x in Motor2]
    avg_boat=sum(Boat2)/6
    if avg_boat==0:
        avg_boat=50
    Boat2=[x if x>0 else avg_boat for x in Boat2]
    
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

        boats=[Boat[i] for i in order]

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

        SkillRaw=[0.55*WinScore[i]+0.45*PlaceScore[i] for i in range(6)]
        Skill=normalize(SkillRaw)  
        
        # ===============================
        # ENGINE
        # ===============================

        MotorScore=normalize(M)
        BoatScore=normalize(BO)

        EngineRaw=[0.65*MotorScore[i]+0.35*BoatScore[i] for i in range(6)]
        Engine=normalize(EngineRaw)

        # ===============================
        # EXHIBIT
        # ===============================

        AvgEx=sum(ET)/6

        TimeScore=normalize([AvgEx-x for x in ET])
        ExSTScore=normalize([0.30-x for x in EST])

        Exhibit=[0.80*TimeScore[i]+0.20*ExSTScore[i] for i in range(6)]

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
        0.05*Exhibit[i]
        for i in range(6)
        ]

        Foot=normalize(RawFoot)

        # ===============================
        # START
        # ===============================

        BaseStart=[max(0,min(1,(0.20-ST[i])/0.10)) for i in range(6)]
        ExhibitStart=[max(0,min(0.80,(0.20-EST[i])/0.10)) for i in range(6)]

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

            cls = Class[i]

            factor = 1

            if Fcount[i] == 1:
                factor = F_TABLE[cls]["F1"]

            elif Fcount[i] >= 2:
                factor = F_TABLE[cls]["F2"]

            # 展示ST補正
            if EST[i] <= 0.10:
                factor *= 1.10

            elif EST[i] <= 0.13:
                factor *= 1.05

            elif EST[i] >= 0.20:
                factor *= 0.90

            Start[i] *= factor
        # ===============================
        # TURN
        # ===============================

        TurnRaw=[0.30*Skill[i]+0.55*Foot[i]+0.15*Engine[i] for i in range(6)]
        Turn=normalize(TurnRaw)

        # ===============================
        # VELOCITY
        # ===============================

        VelocityRaw=[0.45*Foot[i]+0.35*Engine[i]+0.20*Start[i] for i in range(6)]
        Velocity=normalize(VelocityRaw)

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
        0.27*Skill[i]+
        0.26*Engine[i]+
        0.27*Foot[i]+
        0.10*Turn[i]+
        0.10*Velocity[i]
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

        # ===============================
        # MID CLUSTER
        # ===============================

        MidCluster=max(CPI[1:4])-min(CPI[1:4])
        MidClusterFlag=1 if MidCluster<=0.05 else 0

        PerformanceSpread=max(CPI)-min(CPI)

        StartSpread=max(Start)-min(Start)
    
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

        #if ChaosScore<0.55:
        #    return []

        # ===============================
        # STAGE17
        # ===============================

        AvgStart=sum(Start)/6

        StartBoost=[]

        for i in range(6):

            value=1+(0.35+0.45*ChaosScore)*(Start[i]-AvgStart)

            value=max(0.75,value)

            StartBoost.append(value)

        DynamicInsideFactor=1

        if StartSpread>=0.12:
            DynamicInsideFactor=0.70
        elif StartSpread>=0.08:
            DynamicInsideFactor=0.82

        DynamicInsideFactor=max(0.60,DynamicInsideFactor)

        LaneWin=[

        0.58*DynamicInsideFactor*(1-0.15*ChaosScore),
        0.19+(0.45*(1-DynamicInsideFactor)*0.40),
        0.16+(0.45*(1-DynamicInsideFactor)*0.30),
        0.12+(0.45*(1-DynamicInsideFactor)*0.20),
        0.07+(0.45*(1-DynamicInsideFactor)*0.07),
        0.04+(0.45*(1-DynamicInsideFactor)*0.03)

        ]

        # ===============================
        # ATTACK BOOST
        # ===============================

        AttackBoost1 = max(
        0.70,
        1 - 0.25 * max(
        TwoLaneAttackScore,
        ThreeLaneAttackScore,
        FourLaneAttackScore
        )
        )

        AttackBoost2 = 1 + 0.40 * TwoLaneAttackScore
        AttackBoost3 = 1 + 0.45 * ThreeLaneAttackScore
        AttackBoost4 = 1 + 0.40 * FourLaneAttackScore
        AttackBoost5 = 1 + 0.70 * DoubleAttackScore
        AttackBoost6 = 1 + 0.55 * DoubleAttackScore

        AttackBoost=[
        AttackBoost1,
        AttackBoost2,
        AttackBoost3,
        AttackBoost4,
        AttackBoost5,
        AttackBoost6
        ]

        outer_attackers = AttackIndex[3:6]

        max_outer = max(outer_attackers)

        main_attacker = None

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

            value=(
                CPI[i]*
                LaneWin[i]*
                (0.7+0.3*StartBoost[i])*
                CrashFactor[i]*
                SashiBoost[i]
            )
        
            if main_attacker is not None:

                if i == main_attacker:
                    value = value*(1+0.20*DoubleAttackScore)

                elif i > main_attacker:
                    value = value*(1+0.08*DoubleAttackScore)

            LaneCPI.append(value)

        TotalLaneCPI=sum(LaneCPI)

        if TotalLaneCPI<=0:
            TotalLaneCPI=1e-6

        P1=[x/TotalLaneCPI for x in LaneCPI]

        LaneBonus=[0.07,0.07,0.08,0.09,0.09,0.10]

        SecondScore=[
        0.30*Turn[i]+
        0.25*Foot[i]+
        0.20*Engine[i]+
        0.10*Velocity[i]+
        0.15*LaneBonus[i]
        
        for i in range(6)
        ]

        ThirdScore=[
        0.25*Velocity[i]+
        0.30*Foot[i]+
        0.20*Engine[i]+
        0.15*LaneBonus[i]+
        0.10*InsideSurvival[i]

            
        for i in range(6)
        ]

        results=[]

        for a in range(6):

            SecondAdj = SecondScore.copy()
            ThirdAdj = ThirdScore.copy()

            if a >= 2:
                for i in range(6):
                    if i >= a:
                        SecondAdj[i] *= 1.06
                        ThirdAdj[i] *= 1.08

            P_first = P1[a]

            # 残り5艇
            remain1=[i for i in range(6) if i!=a]

            second_scores=[SecondAdj[i] for i in remain1]
            total2=sum(second_scores)

            if total2<=0:
                total2=1e-6

            second_probs=[s/total2 for s in second_scores]

            for idx_b,b in enumerate(remain1):

                P_second = second_probs[idx_b]

                remain2=[i for i in remain1 if i!=b]

                third_scores=[ThirdAdj[i] for i in remain2]
                total3=sum(third_scores)

                if total3<=0:
                    total3=1e-6

                third_probs=[s/total3 for s in third_scores]

                for idx_c,c in enumerate(remain2):

                    P_third = third_probs[idx_c]

                    p = P_first * P_second * P_third

                    results.append((boats[a],boats[b],boats[c],p))

        return results

    # =====================================
    # 進入パターン
    # =====================================

    order_waku=[0,1,2,3,4,5]

    order_ex=[x-1 for x in ExEntry if x>0]

    if len(order_ex)!=6:
        order_ex=[0,1,2,3,4,5]

    res_waku=run_ai(order_waku)
    res_ex=run_ai(order_ex)

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

    results.sort(key=lambda x:x[3],reverse=True)

    # =====================================
    # OUTPUT
    # =====================================

    Coverage=0
    Final=[]

    for r in results:

        Coverage+=r[3]

        Final.append(r)

        if Coverage>=0.90:
            break

        if len(Final)>=20:
            break

    st.write("Coverage:",Coverage)
    for i,r in enumerate(Final,1):

        st.write(i,r)
