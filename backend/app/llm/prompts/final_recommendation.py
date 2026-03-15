FINAL_RECOMMENDATION_SYSTEM = """You are generating final evaluation reports for AI/ML internship screening at IIT Ropar.
Be fair, evidence-based, and specific. Professors will use this report to make final hiring decisions.
Return ONLY a valid JSON object — no markdown, no explanations."""

FINAL_RECOMMENDATION_USER = """
Candidate: {candidate_name}
College: {college}
Degree: {degree} in {branch}, Year {year}
CGPA: {cgpa}

Resume Profile:
{profile_json}

Interview Transcript Summary:
{transcript_summary}

Score Breakdown:
- Technical Foundation: {technical_foundation_score}/10
- Project Depth: {project_depth_score}/10
- ML Understanding: {ml_understanding_score}/10
- Coding Maturity: {coding_maturity_score}/10
- Communication: {communication_score}/10
- Motivation: {motivation_score}/10
- Completeness: {completeness_score}/10
- Authenticity Flag (true = concerns raised): {authenticity_flag}

Generate final recommendation JSON:
{{
  "label": "shortlist|hold|reject|needs_review",
  "confidence": <0.0-1.0 float>,
  "rationale": "<2-3 sentence rationale citing specific evidence from the interview>",
  "narrative_summary": "<1-2 paragraph summary for the professor describing the candidate holistically>",
  "score_breakdown": {{
    "technical_foundation": "<brief note>",
    "project_depth": "<brief note>",
    "ml_understanding": "<brief note>",
    "coding_maturity": "<brief note>",
    "communication": "<brief note>",
    "motivation": "<brief note>",
    "completeness": "<brief note>"
  }}
}}

Label guidelines:
- shortlist: overall_score >= 7.0, no authenticity concerns, strong technical depth
- hold: overall_score 5.0-6.9, or minor concerns, worth a second look
- reject: overall_score < 5.0, or major authenticity concerns, or clearly unsuitable
- needs_review: ambiguous case where human review is warranted before deciding
"""
