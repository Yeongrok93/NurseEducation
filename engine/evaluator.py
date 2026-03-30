import json


class SBAREvaluator:

    def __init__(self, client):
        self.client = client

    def evaluate(self, scenario, message):

        prompt = f"""
너는 중환자실에서 간호사의 SBAR 노티를 받는 의사이다. 
        
Patient:
{scenario.patient}

Monitor:
{scenario.monitor}

Ventilator:
{scenario.ventilator}

Goals for good communication:
{scenario.goal}

Nurse message:
{message}
Evaluate the message according to the SBAR-LA rubric below.

Score each item as:
0 = not present
1 = clearly present

SBAR-LA Rubric:

Situation
1. Identifies self (states own name or role)
2. Provides patient name
3. Provides second patient identifier (age, DOB, room number etc.)
4. Clearly expresses the situation or urgency

Background
5. States the context (diagnosis, admission reason, patient condition)
6. States recent findings (vitals, labs, symptoms)
7. Provides facts only (no irrelevant information)

Assessment
8. Provides summary assessment of the problem

Recommendation
9. Provides concrete suggested action
10. Provides contact information or confirmation of follow-up

Return JSON only with the following format:

{{
 "identify_self":0 or 1,
 "patient_name":0 or 1,
 "patient_identifier":0 or 1,
 "situation":0 or 1,
 "context":0 or 1,
 "recent_findings":0 or 1,
 "facts_only":0 or 1,
 "assessment":0 or 1,
 "recommendation":0 or 1,
 "contact_information":0 or 1,
 "total_score":0-10,
 "feedback":"short explanation in Korean"
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        result = json.loads(response.choices[0].message.content)
        return result