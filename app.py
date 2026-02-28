from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------
# 환경 설정
# ------------------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

conversation_history = []
phase=1

# ------------------------
# 초기 상태값
# ------------------------

def reset_game():
    global patient_state, nurse_state, turn_count, game_over, conversation_history, phase

    patient_state = {
        "orientation": 50,
        "anxiety": 60,
        "aggression": 65
    }

    nurse_state = {
        "empathy": 50,
        "problem_solving": 50,
        "assessment": 50,
        "safety": 50,
        "communication": 50
    }

    turn_count = 0
    game_over = False
    conversation_history = []
    phase=1

reset_game()

MAX_TURN = 10

# ------------------------
# Phase 결정 (상태 기반)
# ------------------------

def update_phase():  # 🔥 추가
    global phase

    if patient_state["aggression"] >= 68:
        phase = 2
    elif patient_state["orientation"] >= 60 and patient_state["anxiety"] <= 50:
        phase = 3
    else:
        phase = 1

# ------------------------
# 힌트 생성 (규칙 기반)
# ------------------------

def generate_hint():  # 🔥 추가
    if phase == 1:
        return "환자는 지남력 저하 상태입니다. 적절한 중재를 제공하세요."
    elif phase == 2:
        return "환자가 과자극 상태입니다. 부드러운 문자으로 접근하세요."
    elif phase == 3:
        return "환자가 안정을 찾고 있습니다. 따뜻한 말로 환자에게 다가가세요."

# ------------------------
# 상태 범위 제한
# ------------------------

def clamp_state():
    for key in patient_state:
        patient_state[key] = max(0, min(100, patient_state[key]))

    for key in nurse_state:
        nurse_state[key] = max(0, min(100, nurse_state[key]))


# ------------------------
# LLM 분석
# ------------------------

def analyze_nurse_input(nurse_input):
    prompt = f"""
You are a clinical interaction analyzer.
Return ONLY valid JSON.

For each category assign integer score -5 to +5.

Categories:
- empathy
- reorientation
- cam_assessment
- sedative_request
- safety_intervention

Nurse statement:
"{nurse_input}"

Current patient state:
{patient_state}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=150
    )

    return json.loads(response.choices[0].message.content)

# ------------------------
# 환자 대사 생성
# ------------------------

def generate_patient_response():
    global conversation_history
    system_prompt = f"""
You are roleplaying as a 78-year-old hospitalized male patient with hyperactive delirium.

Rules:
- Speak naturally like an elderly Korean man.
- Do NOT explain your condition.
- Do NOT say you are confused or anxious.
- Only speak what the patient would say.
- One short sentence only (max 10 words).
- Always use correct Korean spacing.
- Never remove spacing between words.
- Use natural Korean grammar and spacing.
IMPORTANT: Always maintain proper spacing between Korean words.

Tone examples:
- "여기가 어디요?"
- "집에 가야 하는데..."
- "저 사람 누구요?"
- "나 건드리지 마!"

Current Phase: {phase}

Phase behavior guideline:
- Phase 1 → confused, questioning, restless.
- Phase 2 → irritable, defensive, reactive.
- Phase 3 → slightly calmer, more receptive.

Current state:
Orientation: {patient_state["orientation"]}
Anxiety: {patient_state["anxiety"]}
Aggression: {patient_state["aggression"]}

Respond with dialogue only.
"""
    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4,
        max_tokens=40
    )

    reply = response.choices[0].message.content.strip()
    reply = " ".join(reply.split())
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

# ------------------------
# 엔딩 생성 (LLM 기반)
# ------------------------

def generate_ending(result_type):
    prompt = f"""
You are a delirium patient.

Game result: {result_type}

If SUCCESS → patient feels calmer and oriented.
If FAIL → patient is agitated and confused.
If TIME_OVER → patient is still unstable.

Respond in ONE short Korean sentence.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=30
    )

    return response.choices[0].message.content

# ------------------------
# 게임 종료 판정
# ------------------------

def check_game_end():
    if (patient_state["aggression"] <= 40 and
        patient_state["orientation"] >= 65 and
        patient_state["anxiety"] <= 45):
        return "SUCCESS"

    if (patient_state["aggression"] >= 90 or
        patient_state["orientation"] <= 20):
        return "FAIL"

    if turn_count >= MAX_TURN:
        return "TIME_OVER"

    return None

# ------------------------
# 홈
# ------------------------

@app.route("/")
def home():
    reset_game()
    update_phase()               # 🔥 추가
    current_hint = generate_hint()  # 🔥 추가
    return render_template("index.html",
                            patient_state=patient_state,
                            nurse_state=nurse_state,
                            hint=current_hint,
                            opening_line="여기가 어디야… 집에 가야 하는데…")

# ------------------------
# 인터랙션
# ------------------------

@app.route("/interact", methods=["POST"])
def interact():
    global turn_count, game_over

    if game_over:
        return jsonify({"error": "Game Over"}), 400

    data = request.json
    nurse_input = data.get("nurse_input", "")

    try:
        turn_count += 1
        conversation_history.append({
    "role": "user",
    "content": nurse_input
})

        analysis = analyze_nurse_input(nurse_input)

        # 점수 반영
        nurse_state["empathy"] += analysis.get("empathy", 0)
        nurse_state["assessment"] += analysis.get("cam_assessment", 0)
        nurse_state["safety"] += analysis.get("safety_intervention", 0)
        nurse_state["problem_solving"] += (-analysis.get("sedative_request", 0))

        patient_state["orientation"] += analysis.get("reorientation", 0)
        patient_state["anxiety"] -= analysis.get("empathy", 0)
        patient_state["aggression"] -= analysis.get("safety_intervention", 0)

        # 이벤트 트리거
        if patient_state["aggression"] >= 75:
            if analysis.get("safety_intervention", 0) <= 0:
                patient_state["aggression"] += 5

        if patient_state["orientation"] >= 70:
            patient_state["anxiety"] -= 5

        if nurse_state["empathy"] >= 65:
            patient_state["anxiety"] -= 2

        clamp_state()
        update_phase()
        current_hint = generate_hint()

        result = check_game_end()

        if result:
            game_over = True
            patient_response = generate_ending(result)
        else:
            patient_response = generate_patient_response()

        return jsonify({
            "patient_state": patient_state,
            "nurse_state": nurse_state,
            "analysis": analysis,
            "patient_response": patient_response,
            "turn": turn_count,
            "game_result": result,
            "phase" : phase,
            "hint" : generate_hint()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------
# 실행
# ------------------------

if __name__ == "__main__":
    app.run(debug=True)