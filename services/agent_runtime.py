# services/agent_runtime.py
import json
import time
import uuid
from typing import Dict, Any
from adapters.tools import ProjectContext, TaskGraph, CodeDiffBundle, ValidationResult

class AgentRuntime:
    def __init__(self, config_path: str, harness_settings: dict):
        self.config = self._load_yaml(config_path)
        self.settings = harness_settings
        self.trace_id = str(uuid.uuid4())
        
    def _run_step(self, step_id: str, adapter_func, inputs: list):
        # 1. Execute adapter (simulates LLM or deterministic tool)
        raw_output = adapter_func(inputs)
        
        # 2. Strict contract validation
        output_schema = self.config["steps"][self._find_step(step_id)].get("output_schema")
        validator_class = _get_pydantic_model(output_schema)
        
        try:
            validated_output = validator_class(**raw_output) if isinstance(raw_output, dict) else raw_output
        except Exception as e:
            raise ValidationError(f"Schema violation at {step_id}: {e}")
            
        return validated_output

    def _apply_retry_policy(self, step_name: str, result, attempts):
        if attempts < self.settings["retry_policy"]["max_attempts"]:
            # Auto-retry with refined prompt (simplified)
            print(f"[RETRY] {step_name} attempt {attempts+1}/{self.settings['retry_policy']['max_attempts']}")
            return self._run_step(step_name, self.current_adapter, [result])
        
        # Exhausted: halt & flag for human review
        raise WorkflowPauseError(f"Step '{step_name}' exceeded retry limit. Pausing workflow.", step_name)

    def execute(self, user_request: str):
        print(f"[TRACE] {self.trace_id} | Starting pipeline")
        current_state = {}
        
        for step in self.config["steps"]:
            try:
                result = self._run_step(step["id"], self._load_adapter_for_step(step["adapter"]), [])
                
                # Enforce 1-retry → pause policy on code/validation steps
                if step["id"] in ["code_generator", "validator"]:
                    if not isinstance(result, CodeDiffBundle) or result.passed == False:
                        # Retry exactly once, then pause
                        try:
                            self._apply_retry_policy(step["id"], result, 0)
                        except WorkflowPauseError as e:
                            print(f"[PAUSE] {e}")
                            return {"status": "review_pending", "trace_id": self.trace_id, "failed_step": step["id"]}
                
                current_state[step["id"]] = result
                print(f"[OK] Step '{step['id']}' passed validation.")
                
            except (ValidationError, WorkflowPauseError) as e:
                return {"status": "review_pending", "trace_id": self.trace_id, "error": str(e)}

        # Pipeline complete → ready for human review or merge
        return {
            "status": "ready_for_review",
            "trace_id": self.trace_id,
            "artifact": current_state["code_generator"],
            "validation_summary": current_state["validator"]
        }
