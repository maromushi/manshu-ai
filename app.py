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
# STAGE17
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
