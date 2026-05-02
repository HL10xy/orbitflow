from agents.base import BaseAgent


class CoderAgent(BaseAgent):
    role = "coder"
    icon = "\U0001f4bb"
    context_hint = "Output complete, runnable code with file paths. No placeholders or pseudo-code."
