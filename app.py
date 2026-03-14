import itertools
import copy


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
# INPUT
# =====================================

Boat=[1,2,3,4,5,6]

WinRate=[0,0,0,0,0,0]
PlaceRate=[0,0,0,0,0,0]

AvgST=[0,0,0,0,0,0]

Motor2=[0,0,0,0,0,0]
Boat2=[0,0,0,0,0,0]

ExTime=[0,0,0,0,0,0]
ExST=[0,0,0,0,0,0]

TurnTime=[0,0,0,0,0,0]
LapTime=[0,0,0,0,0,0]
StraightTime=[0,0,0,0,0,0]

Class=["A1","A2","B1","B1","B2","A1"]
Fcount=[0,0,0,0,0,0]
ExhibitionF=[0,0,0,0,0,0]

ExEntry=[1,2,3,4,5,6]


# =====================================
# SANITIZE INPUT
# =====================================

WinRate=clamp(to_float_list(fix_length(WinRate)),0,10)
PlaceRate=clamp(to_float_list(fix_length(PlaceRate)),0,100)

AvgST=clamp(to_float_list(fix_length(AvgST)),0,0.40)

Motor2=clamp(to_float_list(fix_length(Motor2)),0,100)
Boat2=clamp(to_float_list(fix_length(Boat2)),0,100)

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
    0.40*TurnScore[i]+
    0.25*LapScore[i]+
    0.25*StraightScore[i]+
    0.10*Exhibit[i]
    for i in range(6)
    ]

    Foot=normalize(RawFoot)

    # ===============================
    # START
    # ===============================

    BaseStart=[max(0,min(1,(0.20-ST[i])/0.10)) for i in range(6)]
    ExhibitStart=[max(0,min(0.80,(0.20-EST[i])/0.10)) for i in range(6)]

    StartRaw=[0.75*BaseStart[i]+0.25*ExhibitStart[i] for i in range(6)]

    Start=normalize(StartRaw)

    # ===============================
    # TURN
    # ===============================

    TurnRaw=[0.30*Skill[i]+0.55*Foot[i]+0.15*Engine[i] for i in range(6)]
    Turn=normalize(TurnRaw)

    # ===============================
    # VELOCITY
    # ===============================

    VelocityRaw=[0.50*Foot[i]+0.35*Engine[i]+0.15*Start[i] for i in range(6)]
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
    0.33*Skill[i]+
    0.25*Engine[i]+
    0.27*Foot[i]+
    0.10*Turn[i]+
    0.05*Velocity[i]
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

    TwoLaneAttackFlag=1 if (Start[1]<=Start[0]+0.05 and CPI[1]>=0.55) else 0

    ThreeLaneAttackFlag=1 if (
    Start[2]<=0.18 and
    CPI[2]>=0.55 and
    Start[2]<=Start[1]+0.03
    ) else 0

    FourLaneAttackFlag=1 if (
    Start[3]<=Start[1] and
    Start[3]<=Start[2] and
    Start[3]<=0.15 and
    CPI[3]>=0.55
    ) else 0

    # ===============================
    # ATTACK SCORE
    # ===============================

    TwoLaneAttackScore = (
    0.22 * TwoLaneAttackFlag +
    0.28 * max(0, Start[1] - Start[0]) +
    0.22 * max(0, CPI[1] - CPI[0]) +
    0.15 * max(0, Engine[1] - Engine[0]) +
    0.13 * max(0, Turn[1] - Turn[0])
    )

    ThreeLaneAttackScore = (
    0.22 * ThreeLaneAttackFlag +
    0.28 * max(0, Start[2] - Start[1]) +
    0.22 * max(0, CPI[2] - CPI[0]) +
    0.15 * max(0, Engine[2] - Engine[0]) +
    0.13 * max(0, Turn[2] - Turn[0])
    )

    FourLaneAttackScore = (
    0.22 * FourLaneAttackFlag +
    0.28 * max(0, Start[3] - Start[2]) +
    0.22 * max(0, CPI[3] - CPI[0]) +
    0.15 * max(0, Engine[3] - Engine[0]) +
    0.13 * max(0, Turn[3] - Turn[0])
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

    0.50*DynamicInsideFactor,
    0.17+(0.50*(1-DynamicInsideFactor)*0.40),
    0.15+(0.50*(1-DynamicInsideFactor)*0.30),
    0.11+(0.50*(1-DynamicInsideFactor)*0.20),
    0.05+(0.50*(1-DynamicInsideFactor)*0.07),
    0.02+(0.50*(1-DynamicInsideFactor)*0.03)

    ]


    # ===============================
    # ATTACK BOOST
    # ===============================

    AttackBoost1 = max(
    0.70,
    1 - 0.4 * max(
    TwoLaneAttackScore,
    ThreeLaneAttackScore,
    FourLaneAttackScore
    )
    )

    AttackBoost2 = 1 + 0.5 * TwoLaneAttackScore
    AttackBoost3 = 1 + 0.6 * ThreeLaneAttackScore
    AttackBoost4 = 1 + 0.5 * FourLaneAttackScore
    AttackBoost5 = 1 + 0.9 * DoubleAttackScore
    AttackBoost6 = 1 + 0.7 * DoubleAttackScore


    AttackBoost=[
    AttackBoost1,
    AttackBoost2,
    AttackBoost3,
    AttackBoost4,
    AttackBoost5,
    AttackBoost6
    ]


    LaneCPI=[]

    for i in range(6):

        value=(
        CPI[i]*
        LaneWin[i]*
        AttackBoost[i]*
        StartBoost[i]
        )

        if i>=3:
            value=value*(1+0.4*DoubleAttackScore)

        LaneCPI.append(value)


    TotalLaneCPI=sum(LaneCPI)

    if TotalLaneCPI<=0:
        TotalLaneCPI=1e-6


    P1=[x/TotalLaneCPI for x in LaneCPI]


    LaneBonus=[0.08,0.07,0.08,0.09,0.12,0.14]


    SecondScore=[
    0.35*Turn[i]+
    0.35*Foot[i]+
    0.20*Velocity[i]+
    0.10*LaneBonus[i]
    for i in range(6)
    ]


    ThirdScore=[
    0.35*Velocity[i]+
    0.30*Foot[i]+
    0.20*Engine[i]+
    0.10*LaneBonus[i]+
    0.05*InsideSurvival[i]
    for i in range(6)
    ]


    SecondTotal=sum(SecondScore)
    ThirdTotal=sum(ThirdScore)


    SecondProb=[x/SecondTotal for x in SecondScore]
    ThirdProb=[x/ThirdTotal for x in ThirdScore]


    results=[]


    for a,b,c in itertools.permutations(range(6),3):

        den2=1-SecondProb[a]
        den3=1-ThirdProb[a]-ThirdProb[b]

        if den2<=0:
            den2=1e-6

        if den3<=0:
            den3=1e-6

        p=P1[a]*(SecondProb[b]/den2)*(ThirdProb[c]/den3)

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


print("Coverage:",Coverage)

for i,r in enumerate(Final,1):

    print(i,r)



