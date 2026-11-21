from adapters.tools import CodeDiffBundle, ProjectContext, TaskGraph

class CodeSynthesizer:
    def __init__(self, prompt_template_path: str):
        self.template = self._load_prompt(prompt_template_path)
        
    def synthesize(self, tasks: TaskGraph, context: ProjectContext) -> CodeDiffBundle:
        """Returns diff bundles with explicit target paths & impact scoring."""
        pass
