import json


class Scenario:

    def __init__(self, data):
        self.title       = data["title"]
        self.monitor     = data["monitor"]
        self.ventilator  = data["ventilator"]
        self.labs        = data["labs"]
        self.goal        = data.get("goal", [])
        self.difficulty  = data.get("difficulty", 1)
        self.personality = data.get("personality", "calm ICU attending physician")

        # patient: 하위 호환을 위해 문자열도 허용, 아니면 구조화된 딕셔너리 사용
        raw = data.get("patient", {})
        if isinstance(raw, str):
            # 구버전 시나리오 — 문자열을 그대로 note에 넣고 나머지는 기본값
            self.patient = {"note": raw}
        else:
            self.patient = raw

    # evaluator / physician_agent 에서 str(scenario.patient) 형태로 쓰던 곳은
    # scenario.patient_summary 를 사용하도록 점진적으로 교체 가능
    @property
    def patient_summary(self) -> str:
        """사람이 읽기 좋은 한 줄 요약 (프롬프트용)"""
        p = self.patient
        parts = []
        if p.get("name"):   parts.append(p["name"])
        if p.get("age"):    parts.append(f"{p['age']}세")
        if p.get("gender"): parts.append(p["gender"])
        if p.get("diagnosis"):
            dx = p["diagnosis"]
            if isinstance(dx, list):
                parts.append(" / ".join(dx))
            else:
                parts.append(dx)
        return ", ".join(parts) if parts else p.get("note", "N/A")


def load_scenario(name: str) -> Scenario:
    with open(f"scenarios/{name}.json", encoding="utf-8") as f:
        data = json.load(f)
    return Scenario(data)