import json


class Scenario:

    def __init__(self, name, data):
        self.name = name
        self.title = data["title"]
        self.monitor = data["monitor"]
        self.ventilator = data["ventilator"]
        self.labs = data["labs"]
        self.goal = data.get("goal", [])
        self.difficulty = data.get("difficulty", 1)
        self.personality = data.get("personality", "calm ICU attending physician")

        raw = data.get("patient", {})
        if isinstance(raw, str):
            self.patient = {"note": raw}
        else:
            self.patient = raw

    @property
    def patient_summary(self) -> str:
        p = self.patient
        parts = []
        if p.get("name"):
            parts.append(p["name"])
        if p.get("age"):
            parts.append(f"{p['age']} years")
        if p.get("gender"):
            parts.append(p["gender"])
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
    return Scenario(name, data)
