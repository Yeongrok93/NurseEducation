from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import copy

from openai import OpenAI

from engine.scenario_loader import load_scenario
from engine.game_state import GameState
from engine.evaluator import SBAREvaluator
from engine.physician_agent import PhysicianAgent

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "icu-sim-secret-key")
CORS(app)

# 시나리오는 한 번만 로드 (읽기 전용 원본)
_scenario_template = load_scenario("spo2_drop")

evaluator = SBAREvaluator(client)
doctor = PhysicianAgent(client)

# 세션별 게임 상태 저장소
games: dict[str, GameState] = {}


def get_game() -> GameState:
    """현재 세션의 GameState를 반환. 없으면 새로 생성."""
    sid = session.get("sid")
    if sid and sid in games:
        return games[sid]
    return _new_game()


def _new_game() -> GameState:
    """세션에 새 게임을 생성하고 저장."""
    import uuid
    sid = str(uuid.uuid4())
    session["sid"] = sid
    # 원본 시나리오를 deepcopy해서 격리
    game = GameState(copy.deepcopy(_scenario_template))
    games[sid] = game
    return game


@app.route("/")
def home():
    game = _new_game()   # 홈 진입 시 항상 새 게임
    return render_template("index.html", scenario=game.scenario.title)


@app.route("/get_monitor")
def get_monitor():
    game = get_game()
    return jsonify({
        "spo2": game.scenario.monitor["spo2"],
        "hr":   game.scenario.monitor["hr"],
        "bp":   game.scenario.monitor["bp"],
        "rr":   game.scenario.monitor["rr"],
        "turn": game.turn,
    })


@app.route("/get_vent")
def get_vent():
    return jsonify(get_game().scenario.ventilator)


@app.route("/get_chart")
def get_chart():
    return jsonify(get_game().scenario.chart)


@app.route("/get_labs")
def get_labs():
    return jsonify(get_game().scenario.labs)


@app.route("/get_patient")
def get_patient():
    return jsonify(get_game().scenario.patient)


@app.route("/interact", methods=["POST"])
def interact():
    game = get_game()

    if game.game_over:
        return jsonify({"error": "Game already ended"}), 400

    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    game.next_turn()

    game.history.append({"role": "user", "content": message})

    try:
        analysis = evaluator.evaluate(game.scenario, message)
    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {str(e)}"}), 500

    # GPT가 반환한 total_score를 신뢰 (Python 재계산 제거)
    score = analysis.get("total_score", 0)
    game.add_score(score)

    result = game.check_end()

    if result:
        game.game_over = True
        physician_response = "알겠습니다. 바로 확인하겠습니다."
    else:
        try:
            physician_response = doctor.respond(game.scenario, game.history)
        except Exception as e:
            physician_response = "죄송합니다. 잠시 후 다시 시도해주세요."

    game.history.append({"role": "assistant", "content": physician_response})

    return jsonify({
        "analysis":           analysis,
        "score":              score,
        "total_score":        game.score,
        "physician_response": physician_response,
        "turn":               game.turn,
        "result":             result,
    })


if __name__ == "__main__":
    app.run(debug=True)