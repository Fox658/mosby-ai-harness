import re 
import json
from typing import List, Dict, Optional
from adapters.tools import TaskGraph, TaskStep, ProjectContext

class TaskPlanner:
    """Decomposes natural language requests into deterministic subtasks."""
    def __init__(self, prompt_template_path: str):
        self.template = self._load_prompt(prompt_template_path)  # Versioned YAML/JSON

    def execute() -> TaskGraph:
        # In production: call LLM with templated instruction + injected context
        # For now: return a deterministic mock that respects constraints
        plan = {
            "steps":[
                TaskStep(
                    name="extract_requirements",
                    input_context=["task_planner_output"],
                    expected_artifact="requirements.json",
                    prompt_template_key="requirements_extraction"
                ),
                TaskStep(
                    name="map_to_conventions",
                    input_context=["requirements.json", "ProjectContext"],
                    expected_artifact="convention_map.json",
                    prompt_template_key="convention_alignment"
                ),
                TaskStep(
                    name="generate_diffs",
                    input_context=["requirements.json", "convention_map.json"],
                    expected_artifact="diff_bundle.patch",
                    prompt_template_key="code_synthesis"
                )
            ],
            "context_dependencies": ["ProjectContext"]
        }    
        return TaskGraph(**plan)
    
    def _load_prompt(self, path: str):
        # Load versioned prompt template (YAML/JSON)
        pass  # Implementation detail isolated here
