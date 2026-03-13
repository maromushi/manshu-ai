import itertools
import math

# =========================
# NORMALIZE
# =========================

def normalize(values):

    mn = min(values)
    mx = max(values)

    if mx - mn < 1e-6:
        return [0.5] * len(values)

    return [(v - mn) / (mx - mn) for v in values]


# =========================
# INPUT (例)
# =========================

Boat = [1,2,3,4,5,6]

WinRate = [0,0,0,0,0,0]
PlaceRate = [0,0,0,0,0,0]
AvgST = [0,0,0,0,0,0]

Motor2 = [0,0,0,0,0,0]
Boat2 = [0,0,0,0,0,0]

ExTime = [0,0,0,0,0,0]
ExST = [0,0,0,0,0,0]

TurnTime = [0,0,0,0,0,0]
LapTime = [0,0,0,0,0,0]
StraightTime = [0,0,0,0,0,0]

Class = ["B1","B1","B1","B1","B1","B1"]


# =========================
# SKILL
# =========================

WinRateScore = normalize(WinRate)
PlaceRateScore = normalize(PlaceRate)

SkillRaw = [
0.55 * WinRateScore[i] +
0.45 * PlaceRateScore[i]
for i in range(6)
]

Skill = normalize(SkillRaw)


# =========================
# ENGINE
# =========================

MotorScore = normalize(Motor2)
BoatScore = normalize(Boat2)

EngineRaw = [
0.65 * MotorScore[i] +
0.35 * BoatScore[i]
for i in range(6)
]

Engine = normalize(EngineRaw)


# =========================
# EXHIBITION
# =========================

AvgExTime = sum(ExTime) / 6

TimeDiff = [AvgExTime - x for x in ExTime]
TimeScore = normalize(TimeDiff)

ExSTScore = normalize([0.30 - x for x in ExST])

Exhibit = [
0.80 * TimeScore[i] +
0.20 * ExSTScore[i]
for i in range(6)
]


# =========================
# FOOT
# =========================

AvgTurn = sum(TurnTime) / 6
AvgLap = sum(LapTime) / 6
AvgStraight = sum(StraightTime) / 6

TurnDiff = [AvgTurn - x for x in TurnTime]
LapDiff = [AvgLap - x for x in LapTime]
StraightDiff = [AvgStraight - x for x in StraightTime]

TurnScore = normalize(TurnDiff)
LapScore = normalize(LapDiff)
StraightScore = normalize(StraightDiff)

RawFoot = [
0.40 * TurnScore[i] +
0.25 * LapScore[i] +
0.25 * StraightScore[i] +
0.10 * Exhibit[i]
for i in range(6)
]

Foot = normalize(RawFoot)


# =========================
# START
# =========================

BaseStart = [
max(0,min(1,(0.20 - AvgST[i]) / 0.10))
for i in range(6)
]

ExhibitStart = [
max(0,min(1,(0.20 - ExST[i]) / 0.10))
for i in range(6)
]

Start = [
0.65 * BaseStart[i] +
0.35 * ExhibitStart[i]
for i in range(6)
]


# =========================
# TURN
# =========================

TurnRaw = [
0.30 * Skill[i] +
0.55 * Foot[i] +
0.15 * Engine[i]
for i in range(6)
]

Turn = normalize(TurnRaw)


# =========================
# VELOCITY
# =========================

VelocityRaw = [
0.50 * Foot[i] +
0.35 * Engine[i] +
0.15 * Start[i]
for i in range(6)
]

Velocity = normalize(VelocityRaw)


# =========================
# INSIDE SURVIVAL
# =========================

InsideSurvival_i = [
0.40 * Skill[i] +
0.30 * Engine[i] +
0.20 * Start[i] +
0.10 * Foot[i]
for i in range(6)
]

# =========================
# LANE BONUS
# =========================

LaneBonus = [0.08,0.07,0.06,0.09,0.12,0.14]

# =========================
# CPI (Start削除版)
# =========================

CPI = [
0.33 * Skill[i] +
0.25 * Engine[i] +
0.27 * Foot[i] +
0.10 * Turn[i] +
0.05 * Velocity[i]
for i in range(6)
]


# =========================
# START SPREAD
# =========================

StartSpread = max(Start) - min(Start)


# =========================
# CHAOS SCORE
# =========================

PerformanceSpread = max(CPI) - min(CPI)

OuterPower = (
0.5 * max(CPI[3:6]) +
0.3 * sorted(CPI[3:6])[-2] +
0.2 * (sum(CPI[3:6]) / 3)
)

InsideWeak = 1 - InsideSurvival_i[0]

ChaosScore = (
0.20 * OuterPower +
0.25 * InsideWeak +
0.25 * StartSpread +
0.16 * PerformanceSpread
)

ChaosScore = max(0,min(1,ChaosScore))


# =========================
# STAGE17（第一）
# =========================

AvgStart = sum(Start)/6

StartBoost = [
1 + (0.5 + 0.5 * ChaosScore) * (Start[i] - AvgStart)
for i in range(6)
]

DynamicInsideFactor = 1

if StartSpread >= 0.12:
    DynamicInsideFactor = 0.70
elif StartSpread >= 0.08:
    DynamicInsideFactor = 0.82


LaneWin = [
0.50 * DynamicInsideFactor,
0.17 + (0.50*(1-DynamicInsideFactor)*0.40),
0.15 + (0.50*(1-DynamicInsideFactor)*0.30),
0.11 + (0.50*(1-DynamicInsideFactor)*0.20),
0.05 + (0.50*(1-DynamicInsideFactor)*0.07),
0.02 + (0.50*(1-DynamicInsideFactor)*0.03)
]


LaneCPI = [
CPI[i] * LaneWin[i] * StartBoost[i]
for i in range(6)
]

TotalLaneCPI = sum(LaneCPI)

P1 = [x / TotalLaneCPI for x in LaneCPI]


# =========================
# SECOND / THIRD SCORE
# =========================

SecondScore = [
0.35 * Turn[i] +
0.35 * Foot[i] +
0.20 * Velocity[i]  +
0.10 * LaneBonus[i] 
for i in range(6)
]

ThirdScore = [
0.35 * Velocity[i] +
0.30 * Foot[i] +
0.20 * Engine[i] +
0.10 * LaneBonus[i] +
0.05 * InsideSurvival_i[i]
for i in range(6)
]


TotalSecond = sum(SecondScore)
TotalThird = sum(ThirdScore)


# =========================
# TRIFECTA
# =========================

results = []

for A,B,C in itertools.permutations(range(6),3):

    p = (
    P1[A] *
    (SecondScore[B] / (TotalSecond - SecondScore[A])) *
    (ThirdScore[C] / (TotalThird - ThirdScore[A] - ThirdScore[B]))
    )

    results.append((A+1,B+1,C+1,p))


results.sort(key=lambda x:x[3], reverse=True)


Coverage = 0
Final = []

for r in results:

    Coverage += r[3]
    Final.append(r)

    if Coverage >= 0.90:
        break

    if len(Final) >= 20:
        break


print("Coverage:",Coverage)

for i,r in enumerate(Final,1):

    print(i,r[0],r[1],r[2],r[3])

# ==========================================
# STAGE17 TRIFECTA PROBABILITY MODEL
# ==========================================

# --------------------------
# StartBoost
# --------------------------

AvgStart = sum(Start) / 6

StartBoost = []

for i in range(6):

    value = 1 + (0.35 + 0.45 * ChaosScore) * (Start[i] - AvgStart)

    value = max(0.75, value)

    StartBoost.append(value)

# --------------------------
# Dynamic Inside Factor
# --------------------------

DynamicInsideFactor = 1.0

if StartSpread >= 0.80:

    DynamicInsideFactor = 0.70

elif StartSpread >= 0.60:

    DynamicInsideFactor = 0.82


if STCrashIndex >= 0.45:

    DynamicInsideFactor = DynamicInsideFactor - 0.08


DynamicInsideFactor = max(0.60, DynamicInsideFactor)

# --------------------------
# Lane Win Probability
# --------------------------

LaneWin = []

LaneWin.append(0.50 * DynamicInsideFactor)

LaneWin.append(
    0.17 + (0.50 * (1 - DynamicInsideFactor) * 0.40)
)

LaneWin.append(
    0.15 + (0.50 * (1 - DynamicInsideFactor) * 0.30)
)

LaneWin.append(
    0.11 + (0.50 * (1 - DynamicInsideFactor) * 0.20)
)

LaneWin.append(
    0.05 + (0.50 * (1 - DynamicInsideFactor) * 0.07)
)

LaneWin.append(
    0.02 + (0.50 * (1 - DynamicInsideFactor) * 0.03)
)


# --------------------------
# Attack Boost
# --------------------------

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


DoubleAttackScore = (
    (ThreeLaneAttackScore * FourLaneAttackScore)
    +
    0.5 * (TwoLaneAttackScore * ThreeLaneAttackScore)
)


AttackBoost5 = 1 + 0.9 * DoubleAttackScore
AttackBoost6 = 1 + 0.7 * DoubleAttackScore


AttackBoost = [
    AttackBoost1,
    AttackBoost2,
    AttackBoost3,
    AttackBoost4,
    AttackBoost5,
    AttackBoost6
]


# --------------------------
# Lane Bonus
# --------------------------

LaneBonus = [0.05,0.06,0.05,0.10,0.15,0.18]


# --------------------------
# Second Score
# --------------------------

SecondScore = []

for i in range(6):

    value = (
        0.40 * Turn[i]
        +
        0.35 * Foot[i]
        +
        0.25 * Velocity[i]
    )

    SecondScore.append(value)


# --------------------------
# Third Score
# --------------------------

ThirdScore = []

for i in range(6):

    value = (
        0.35 * Velocity[i]
        +
        0.30 * Foot[i]
        +
        0.20 * Engine[i]
        +
        0.10 * LaneBonus[i]
        +
        0.05 * InsideSurvival[i]
    )

    ThirdScore.append(value)


# --------------------------
# LaneCPI
# --------------------------

LaneCPI = []

for i in range(6):

    value = (
        CPI[i]
        *
        LaneWin[i]
        *
        AttackBoost[i]
        *
        StartBoost[i]
    )

    if i >= 3:

        value = value * (1 + 0.4 * DoubleAttackScore)

    LaneCPI.append(value)


TotalLaneCPI = sum(LaneCPI)

if TotalLaneCPI == 0:

    TotalLaneCPI = 0.000001


# --------------------------
# P1 probability
# --------------------------

P1 = []

for i in range(6):

    P1.append(LaneCPI[i] / TotalLaneCPI)


TotalSecondScore = sum(SecondScore)
TotalThirdScore = sum(ThirdScore)


# --------------------------
# STAGE17.5 TRIFECTA GENERATION
# --------------------------

results = []

for A in range(6):

    for B in range(6):

        for C in range(6):

            if A != B and B != C and A != C:
                p = (
                    P1[A]
                    *
                    (
                        SecondScore[B]
                        /
                        (TotalSecondScore - SecondScore[A])
                    )
                    *
                    (
                        ThirdScore[C]
                        /
                        (
                            TotalThirdScore
                            -
                            ThirdScore[A]
                            -
                            ThirdScore[B]
                        )
                    )
                )

# --------------------------
# STAGE17.6 SORT
# --------------------------

results.sort(
    key=lambda x: x[3],
    reverse=True
)


# --------------------------
# STAGE17.7 COVERAGE
# --------------------------

Coverage = 0.0
BetCount = 0

FinalBets = []

for combo in results:

    Coverage = Coverage + combo[3]

    FinalBets.append(combo)

    BetCount = BetCount + 1

    if Coverage >= 0.90:

        break

    if BetCount >= 20:

        break


# --------------------------
# FINAL OUTPUT
# --------------------------

print("Coverage Achieved :", Coverage)

print("Total Bets :", BetCount)

print()

print("Rank | Combination | Probability")

print("--------------------------------")

for i,combo in enumerate(FinalBets):

    rank = i + 1

    A = combo[0]
    B = combo[1]
    C = combo[2]
    P = combo[3]

    print(
        rank,
        "|",
        f"{A}-{B}-{C}",
        "|",
        P
    )
