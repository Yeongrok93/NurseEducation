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
1. 간호사 보고에 틀린 정보가 있으면 그 부분을 먼저 다시 확인하도록 요청한다.
2. 중요한 정보가 빠져 있으면 1~2개의 핵심 질문만 한다.
3. 정보가 충분하고 정확할 때만 다음 조치나 지시를 준다.
4. 항상 실제 중환자실 의사처럼 짧고 자연스럽게 1~2문장으로 답한다.
5. verified_facts는 굳이 반복 나열하지 말고, 필요한 경우에만 간단히 인정한다.
6. incorrect_items가 있으면 정답을 길게 설명하지 말고 '다시 확인' 형태로 유도한다.
7. missing_items가 있으면 그중 가장 중요한 것부터 묻는다.

의사 성향:
{scenario.personality}

평가 결과:
{json.dumps(analysis, ensure_ascii=False, indent=2)}
"""

        messages = [{"role": "system", "content": system_prompt}] + history

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
        )

        return response.choices[0].message.content
