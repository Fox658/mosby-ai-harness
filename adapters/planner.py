from adapters.tools import TaskGraph, ProjectContext

class TaskPlanner:
    def __init__(self, prompt_template_path: str):
        self.template = self._load_prompt(prompt_template_path)  # Versioned YAML/JSON
        
    def plan(self, user_request: str, context: ProjectContext) -> TaskGraph:
        """Outputs ordered step graph + explicit context dependencies."""
        pass
