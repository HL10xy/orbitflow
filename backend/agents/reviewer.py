from agents.base import BaseAgent


class ReviewerAgent(BaseAgent):
    role = "reviewer"
    icon = "\U0001f50d"
    context_hint = "Provide a structured review: Summary, Critical Issues, Suggestions, and an Approved (yes/no) verdict."
