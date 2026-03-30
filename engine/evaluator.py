import json


class SBAREvaluator:

    def __init__(self, client):
        self.client = client

    def evaluate(self, scenario, report_text):
        prompt = f"""
You are evaluating an ICU nurse's cumulative SBAR report.
You know the true scenario and must verify whether the nurse has reported information accurately so far.

Ground truth scenario:
Patient:
{json.dumps(scenario.patient, ensure_ascii=False, indent=2)}

Monitor:
{json.dumps(scenario.monitor, ensure_ascii=False, indent=2)}

Ventilator:
{json.dumps(scenario.ventilator, ensure_ascii=False, indent=2)}

Labs:
{json.dumps(scenario.labs, ensure_ascii=False, indent=2)}

Good communication goals:
{json.dumps(scenario.goal, ensure_ascii=False, indent=2)}

Nurse cumulative report so far:
{report_text}

Evaluate both SBAR completeness and factual accuracy.
This is cumulative scoring across the whole report history, not only the latest turn.

Important scoring discipline:
- Be strict.
- A greeting, acknowledgement, apology, or vague sentence alone is not SBAR.
- Do not infer missing content from politeness or implication.
- Only score an item as 1 when the nurse explicitly states that information somewhere in the cumulative report.
- If the report is only a greeting such as "안녕하세요", most or all rubric items should be 0.
- "facts_only" should be 1 only when the report contains clinical facts and avoids irrelevant content.
- "assessment" should be 1 only when the nurse explicitly interprets the problem.
- "recommendation" should be 1 only when the nurse clearly asks for or suggests a concrete action.
- "contact_information" should be 1 only when the nurse explicitly asks for callback/follow-up or gives contact/availability information.

Score each SBAR rubric item as:
0 = absent or not clear
1 = clearly present

SBAR rubric:
1. identify_self
2. patient_name
3. situation
4. context
5. recent_findings
6. facts_only
7. assessment
8. recommendation
9. contact_information

Also create a factual checklist using the true scenario.
- verified_facts: facts correctly reported by the nurse
- missing_items: clinically important items still missing
- incorrect_items: items that were stated incorrectly, exaggerated, or contradicted the scenario

Return JSON only in this format:
{{
  "identify_self": 0 or 1,
  "patient_name": 0 or 1,
  "situation": 0 or 1,
  "context": 0 or 1,
  "recent_findings": 0 or 1,
  "facts_only": 0 or 1,
  "assessment": 0 or 1,
  "recommendation": 0 or 1,
  "contact_information": 0 or 1,
  "total_score": 0-9,
  "overall_status": "insufficient" or "needs_correction" or "ready_for_action",
  "verified_facts": ["short Korean strings"],
  "missing_items": ["short Korean strings"],
  "incorrect_items": ["short Korean strings"],
  "next_focus": ["short Korean strings, max 3"],
  "feedback": "short Korean explanation"
}}

Rules:
- If the nurse states incorrect medical facts, include them in incorrect_items.
- If incorrect_items is non-empty, overall_status should usually be "needs_correction".
- If many clinically important items are missing, overall_status should be "insufficient".
- Use concise Korean phrases for arrays.
- total_score must equal the sum of the 9 binary rubric items.
- Very short non-clinical reports should have low scores, usually 0 or 1.
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return json.loads(response.choices[0].message.content)
