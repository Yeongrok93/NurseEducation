from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic
import copy
import logging
import os
import re

from engine.evaluator import SBAREvaluator
from engine.game_state import GameState
from engine.log_repository import SupabaseLogRepository
from engine.physician_agent import PhysicianAgent
from engine.scenario_loader import load_scenario

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
log_repo = SupabaseLogRepository(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY"),
)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "icu-sim-secret-key")
CORS(app)

SCENARIO_NAME = "spo2_drop"
_scenario_template = load_scenario(SCENARIO_NAME)

SBAR_SCORE_KEYS = [
    "identify_self",
    "patient_name",
    "situation",
    "context",
    "recent_findings",
    "facts_only",
    "assessment",
    "recommendation",
    "contact_information",
]

evaluator = SBAREvaluator(client)
doctor = PhysicianAgent(client)
games: dict[str, GameState] = {}


def build_cumulative_report(history: list[dict]) -> str:
    nurse_messages = [item["content"] for item in history if item.get("role") == "user" and item.get("content")]
    return "\n".join(nurse_messages).strip()


def normalize_analysis(raw_analysis: dict) -> dict:
    analysis = dict(raw_analysis or {})
    recalculated_score = 0
    for key in SBAR_SCORE_KEYS:
        value = 1 if int(analysis.get(key, 0) or 0) == 1 else 0
        analysis[key] = value
        recalculated_score += value

    analysis.pop("patient_identifier", None)
    analysis["total_score"] = recalculated_score
    analysis["incorrect_items"] = analysis.get("incorrect_items") or []
    analysis["missing_items"] = analysis.get("missing_items") or []
    analysis["verified_facts"] = analysis.get("verified_facts") or []
    analysis["next_focus"] = analysis.get("next_focus") or []
    return analysis


def apply_message_guardrails(report_text: str, analysis: dict) -> dict:
    normalized = re.sub(r"\s+", "", report_text.lower())
    short_nonclinical_patterns = {
        "안녕하세요",
        "안녕",
        "네",
        "예",
        "응",
        "넵",
        "감사합니다",
        "감사",
        "죄송합니다",
        "알겠습니다",
        "확인했습니다",
    }

    if normalized in short_nonclinical_patterns or len(normalized) <= 4:
        for key in SBAR_SCORE_KEYS:
            analysis[key] = 0
        analysis["total_score"] = 0
        analysis["overall_status"] = "insufficient"
        analysis["verified_facts"] = []
        analysis["incorrect_items"] = []
        analysis["missing_items"] = [
            "자기소개",
            "환자 이름",
            "현재 문제",
            "배경 정보",
            "활력징후 또는 검사 결과",
        ]
        analysis["next_focus"] = ["자기소개", "환자 이름", "현재 상태 보고"]
        analysis["feedback"] = "인사나 짧은 응답만으로는 SBAR 보고로 평가되지 않습니다."

    return analysis


def get_game() -> GameState:
    sid = session.get("sid")
    if not sid:
        return _new_game()

    if log_repo.enabled:
        state = log_repo.load_state(sid)
        if state is None:
            return _new_game()
        game = GameState.from_state(copy.deepcopy(_scenario_template), state, sid)
        return game

    if sid in games:
        return games[sid]
    return _new_game()


def save_game(game: GameState) -> None:
    sid = session.get("sid")
    if log_repo.enabled:
        log_repo.save_state(sid, game.to_state())
    else:
        games[sid] = game


def _new_game() -> GameState:
    import uuid

    previous_sid = session.get("sid")
    if previous_sid:
        games.pop(previous_sid, None)

    sid = str(uuid.uuid4())
    session["sid"] = sid

    game = GameState(copy.deepcopy(_scenario_template))
    game.db_session_id = log_repo.create_game_session(sid, game)
    save_game(game)
    return game


@app.route("/")
def home():
    game = _new_game()
    return render_template("index.html", scenario=game.scenario.title)


@app.route("/get_monitor")
def get_monitor():
    game = get_game()
    return jsonify({
        "spo2": game.scenario.monitor["spo2"],
        "hr": game.scenario.monitor["hr"],
        "bp": game.scenario.monitor["bp"],
        "rr": game.scenario.monitor["rr"],
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


@app.route("/keepalive")
def keepalive():
    """Called daily by Vercel Cron so the Supabase project doesn't pause from inactivity."""
    cron_secret = os.getenv("CRON_SECRET")
    if cron_secret and request.headers.get("Authorization") != f"Bearer {cron_secret}":
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"ok": log_repo.ping()})


@app.route("/interact", methods=["POST"])
def interact():
    game = get_game()

    if game.game_over:
        return jsonify({"error": "Game already ended"}), 400

    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    game.next_turn()
    game.history.append({"role": "user", "content": message})
    cumulative_report = build_cumulative_report(game.history)

    try:
        analysis = normalize_analysis(evaluator.evaluate(game.scenario, cumulative_report))
        analysis = apply_message_guardrails(cumulative_report, analysis)
    except Exception as exc:
        return jsonify({"error": f"Evaluation failed: {str(exc)}"}), 500

    score = analysis["total_score"]
    game.set_score(score)
    result = game.check_end(analysis)

    if result:
        game.game_over = True
        physician_response = "알겠습니다. 바로 확인하겠습니다."
    else:
        try:
            physician_response = doctor.respond(game.scenario, game.history, analysis)
        except Exception:
            physician_response = "죄송합니다. 잠시 후 다시 시도해 주세요."

    game.history.append({"role": "assistant", "content": physician_response})
    save_game(game)
    log_repo.log_turn(game, message, physician_response, analysis, result)
    if result:
        log_repo.finalize_game_session(game, result)

    return jsonify({
        "analysis": analysis,
        "score": score,
        "total_score": game.score,
        "physician_response": physician_response,
        "turn": game.turn,
        "result": result,
    })


if __name__ == "__main__":
    app.run(debug=True)
