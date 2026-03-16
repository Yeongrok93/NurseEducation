class GameState:

    def __init__(self, scenario):
        self.scenario = scenario  # app.py에서 deepcopy 후 전달

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

    def _update_patient_condition(self):
        monitor = self.scenario.monitor
        if self.turn >= 6:
            drop = (self.turn - 5) * 2
            monitor["spo2"] = max(70, monitor["spo2"] - drop)

    def check_end(self):
        if self.score >= 9:
            return "SUCCESS"
        if self.turn >= self.max_turn:
            return "TIME_OVER"
        return None