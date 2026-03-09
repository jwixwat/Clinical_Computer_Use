"""
Myle topology guidance for supervised agent planning.
"""

from __future__ import annotations


def build_myle_topology_guidance() -> str:
    return """
Myle EMR topology for this environment:

Patient binding stage:

- On a cold start, the agent may use the top horizontal global navigation bar only to reach Calendar and bind to the intended patient.
- Calendar contains a left-side patient search field that can be used to search by patient name or identifier.
- A matching patient row in the left search results may be clicked to open that patient's chart.
- Once a patient is selected, the agent must treat that chart as the task boundary and stop switching patients.

Within the patient chart:

- Stay inside the bound patient's chart during a task.
- The top horizontal global navigation bar should no longer be used for general task work after patient binding.
- The right-side icon rail is the primary in-chart navigation surface.
- The folder icon opens Documents for the current patient.
- The beaker icon opens Results for the current patient.
- The person icon returns to the main current-patient chart home.
- Other right-rail icons are not generally needed for this initial scope and should be avoided unless explicitly instructed later.

- Evidence layout:

- Documents contains many substantive artifacts, including outside forms, emails, consults, discharge summaries, and some lab/result material.
- Results also contains substantive result artifacts, and there is overlap with Documents.
- There is no perfectly strict separation between Documents and Results, so the agent may search both when looking for evidence.
- Forms from insurers, government, or outside organizations are typically in Documents.

Within a note:

- The left side is note-making apparatus and visit/note context.
- The agent may need to work inside a note if the task involves opening or filling built-in forms.
- The Forms area inside a note can contain links to specific built-in form types.
- For annotation tasks, the agent may open a document in Annotate and use the textbox tool to place and fill boxes.

Practical rules:

- Prefer the current patient chart context over any global list or queue once a patient is bound.
- If the agent becomes disoriented, it should return to the patient chart home with the person icon and continue from there.
- When looking for evidence, the search box in Documents can be used to narrow relevant documents for the current patient.
""".strip()
