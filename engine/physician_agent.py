class PhysicianAgent:

    def __init__(self, client):

        self.client = client

    def respond(self, scenario, history):

        system_prompt = f"""
당신은 중환자실(ICU)에서 간호사의 노티를 받는 담당 의사입니다.

당신의 역할은 문제를 바로 해결하는 것이 아니라,
간호사가 SBAR 방식으로 적절하게 의사소통하도록 돕는 것입니다.

규칙:

1. 간호사의 메시지에 SBAR 정보가 충분하지 않으면 추가 질문을 하십시오.
2. 충분한 정보가 제공되기 전에는 치료 지시를 바로 내리지 마십시오.
3. 간호사가 더 많은 임상 정보를 제공하도록 유도하십시오.
4. 다음과 같은 정보가 부족하면 질문하십시오:
   - 환자 신원 정보
   - 환자의 배경 상태(진단, 입원 이유 등)
   - 활력징후
   - 인공호흡기 설정
   - 최근 검사 결과
5. 실제 중환자실 의사처럼 짧고 자연스럽게 1~2문장으로 대화하십시오.

Personality: {scenario.personality}

Patient:
{scenario.patient}

Monitor:
{scenario.monitor}

"""

        messages = [{"role": "system", "content": system_prompt}] 
        messages += history

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5
        )

        return response.choices[0].message.content