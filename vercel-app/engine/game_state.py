class GameState:

    def __init__(self, scenario):
        self.scenario = scenario
        self.db_session_id = None

        self.turn = 0
        self.max_turn = 10

        self.score = 0
        self.history = []
        self.game_over = False

    def next_turn(self):
        self.turn += 1
        self._update_patient_condition()

    def add_score(self, score):
        self.score += score

    def set_score(self, score):
        self.score = score

    def _update_patient_condition(self):
        monitor = self.scenario.monitor
        if self.turn >= 6:
            drop = (self.turn - 5) * 2
            monitor["spo2"] = max(70, monitor["spo2"] - drop)

    def check_end(self, analysis: dict | None = None):
        analysis = analysis or {}
        overall_status = analysis.get("overall_status")
        incorrect_items = analysis.get("incorrect_items") or []

        if self.score >= 8 and overall_status == "ready_for_action" and not incorrect_items:
            return "SUCCESS"
        if self.turn >= self.max_turn:
            return "TIME_OVER"
        return None

    def to_state(self) -> dict:
        return {
            "turn": self.turn,
            "score": self.score,
            "history": self.history,
            "game_over": self.game_over,
            "monitor": self.scenario.monitor,
        }

    @classmethod
    def from_state(cls, scenario, state: dict, db_session_id=None) -> "GameState":
        game = cls(scenario)
        game.turn = state.get("turn", 0)
        game.score = state.get("score", 0)
        game.history = state.get("history", [])
        game.game_over = state.get("game_over", False)
        monitor = state.get("monitor")
        if monitor:
            game.scenario.monitor.update(monitor)
        game.db_session_id = db_session_id
        return game
