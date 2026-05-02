from agents.base import BaseAgent


class TesterAgent(BaseAgent):
    role = "tester"
    icon = "\U0001f9ea"
    context_hint = "Output complete test files that can be run directly. Cover happy path, error cases, and edge cases."
