import json


class PhysicianAgent:

    def __init__(self, client):
        self.client = client

    def respond(self, scenario, history, analysis):
        system_prompt = f"""
당신은 ICU 주치의다.
당신은 이미 시나리오의 정답을 알고 있고, 간호사의 보고가 정확한지 확인하는 역할을 한다.
하지만 바로 모든 정답을 말하지 말고, 체크리스트 평가 결과에 따라 반응해야 한다.

응답 원칙:
1. 오답이 있어도 그 자리에서 지적하거나 똑같은 내용을 다시 말하라고 강요하지 않는다. 정확성 평가는 점수로 별도 처리되므로, 대화에서는 오답을 지적하지 말고 자연스럽게 다음으로 넘어간다.
2. missing_items 중 가장 중요한 것 1~2개만 골라 질문한다.
3. missing_items가 없고 정보가 충분하면 다음 조치나 지시를 준다.
4. 항상 실제 중환자실 의사처럼 짧고 자연스럽게 1~2문장으로 답한다.
5. verified_facts는 굳이 반복 나열하지 말고, 필요한 경우에만 간단히 인정한다.

의사 성향:
{scenario.personality}

평가 결과:
{json.dumps(analysis, ensure_ascii=False, indent=2)}
"""

        response = self.client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            thinking={"type": "disabled"},
            system=system_prompt,
            messages=history,
        )

        return next(block.text for block in response.content if block.type == "text")
