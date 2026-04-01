import copy
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from supabase import Client, create_client


logger = logging.getLogger(__name__)


class SupabaseLogRepository:

    def __init__(self, url: Optional[str], key: Optional[str]):
        self.enabled = bool(url and key)
        self.client: Optional[Client] = None

        if not self.enabled:
            return

        try:
            self.client = create_client(url, key)
            self._ensure_research_users_table()
        except Exception:
            logger.exception("Failed to initialize Supabase client.")
            self.enabled = False

    def create_game_session(self, session_id: str, game, user_id: Optional[str] = None) -> Optional[str]:
        if not self.client:
            return None

        payload = {
            "id": session_id,
            "user_id": user_id,
            "scenario": game.scenario.name,
            "start_time": self._now_iso(),
            "total_turns": game.max_turn,
            "final_orientation": None,
            "final_anxiety": None,
            "final_aggression": None,
        }

        try:
            response = self.client.table("sessions").insert(payload).execute()
            if response.data:
                return response.data[0]["id"]
        except Exception:
            logger.exception("Failed to create game session log.")

        return None

    def log_turn(
        self,
        game,
        nurse_message: str,
        physician_response: str,
        analysis: dict,
        result: Optional[str],
    ) -> None:
        if not self.client or not game.db_session_id:
            return

        payload = {
            "id": str(uuid4()),
            "session_id": game.db_session_id,
            "turn": game.turn,
            "nurse_input": nurse_message,
            "patient_response": physician_response,
            "analysis": analysis,
            "patient_state": self._build_patient_state(game),
            "nurse_state": self._build_nurse_state(game, analysis, result),
            "phase": game.turn,
            "created_at": self._now_iso(),
        }

        try:
            self.client.table("interactions").insert(payload).execute()
        except Exception:
            logger.exception("Failed to create game turn log.")

    def finalize_game_session(self, game, result: Optional[str]) -> None:
        if not self.client or not game.db_session_id or not result:
            return

        payload = {
            "end_time": self._now_iso(),
            "result": result,
            "total_turns": game.turn,
            "final_orientation": None,
            "final_anxiety": None,
            "final_aggression": None,
        }

        try:
            self.client.table("sessions").update(payload).eq("id", game.db_session_id).execute()
        except Exception:
            logger.exception("Failed to finalize game session log.")

    def _build_patient_state(self, game) -> dict:
        return {
            "monitor": copy.deepcopy(game.scenario.monitor),
            "ventilator": copy.deepcopy(getattr(game.scenario, "ventilator", {})),
            "labs": copy.deepcopy(getattr(game.scenario, "labs", {})),
            "patient": copy.deepcopy(getattr(game.scenario, "patient", {})),
        }

    def _build_nurse_state(self, game, analysis: dict, result: Optional[str]) -> dict:
        return {
            "score": game.score,
            "turn_score": analysis.get("total_score", 0),
            "game_over": game.game_over,
            "result": result,
            "history_length": len(game.history),
        }

    def _ensure_research_users_table(self) -> None:
        if not self.client:
            return
        try:
            self.client.table("research_users").select("id").limit(1).execute()
            logger.info("research_users table is available.")
        except Exception:
            logger.warning(
                "research_users table not found. "
                "Run supabase/research_users.sql in the Supabase SQL Editor to create it. "
                "Local fallback auth will be used until then."
            )

    # ── Research user helpers ──

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        if not self.client:
            return None
        try:
            response = (
                self.client.table("research_users")
                .select("*")
                .eq("username", username)
                .eq("password", password)
                .execute()
            )
            if response.data:
                return response.data[0]
        except Exception:
            logger.exception("Failed to authenticate user.")
        return None

    def register_user(self, username: str, password: str) -> Optional[dict]:
        if not self.client:
            return None
        try:
            response = (
                self.client.table("research_users")
                .insert({"username": username, "password": password})
                .execute()
            )
            if response.data:
                return response.data[0]
        except Exception:
            logger.exception("Failed to register user.")
        return None

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
