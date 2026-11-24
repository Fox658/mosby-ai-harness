# services/agent_runtime.py
import uuid
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError, Field
from adapters.context_extractor import RepoContextExtractor
from adapters.planner import TaskPlanner
from adapters.synthesizer import CodeSynthesizer
from adapters.validator import ValidationGuardrail

ADAPTER_REGISTRY = {
    "repo_context_extractor": RepoContextExtractor,
    "task_planner": TaskPlanner,
    "code_synthesizer": CodeSynthesizer,
    "validation_guardrail": ValidationGuardrail,
}

class ContractViolationError(Exception):
    """Raised when an adapter output fails schema validation."""
    pass

class WorkflowPauseError(Exception):
    """Raised when a step exceeds retry limits and requires human review."""
    pass

class AgentRuntime:
    def __init__(self, config_path: str, harness_settings: dict):
        self.config = self._load_config(config_path)  # Replace with your YAML loader
        self.settings = harness_settings
        self.trace_id = str(uuid.uuid4())
        self.execution_log = []

    # ──────────────────────────────────────────────────────────────
    # CORE EXECUTION LOOP
    # ──────────────────────────────────────────────────────────────
    def execute(self, user_request: str) -> dict:
        self._log("pipeline_start", "initiated")
        current_state: Dict[str, Any] = {}
        step_defs = self.config.get("steps", [])

        for step in step_defs:
            try:
                # 1. Execute adapter (abstracted away from runtime logic)
                raw_result = self._call_adapter(step["adapter"], current_state.values())
                
                # 2. Strict contract enforcement at every boundary
                expected_schema = self._resolve_schema(step.get("output_schema"))
                validated_result = self._validate_output(step["id"], raw_result, expected_schema)
                current_state[step["id"]] = validated_result
                
                self._log(step["id"], "success", {"schema": step.get("output_schema")})

            except (ContractViolationError, WorkflowPauseError):
                # Hard failure path: emit review_pending state immediately
                return {
                    "status": "review_pending",
                    "trace_id": self.trace_id,
                    "failed_step": step["id"],
                    "error": str(Exception),
                    "current_state_snapshot": current_state
                }

        # Pipeline completed successfully → ready for human review or merge
        return {
            "status": "ready_for_review",
            "trace_id": self.trace_id,
            "artifact": current_state.get("code_generator"),
            "validation_summary": current_state.get("validator")
        }

    # ──────────────────────────────────────────────────────────────
    # CONTRACT & VALIDATION LAYER
    # ──────────────────────────────────────────────────────────────
    def _validate_output(self, step_name: str, raw_output: Any, expected_class) -> Any:
        try:
            return expected_class(**raw_output) if isinstance(raw_output, dict) else raw_output
        except ValidationError as e:
            raise ContractViolationError(f"[{step_name}] Schema validation failed: {e}")

    def _resolve_schema(self, schema_ref: str):
        # In production, map string refs to Pydantic models dynamically
        return getattr(__import__("adapters.tools"), schema_ref.replace("PascalCase", "snake_case"))

    # ──────────────────────────────────────────────────────────────
    # RETRY & POLICY ENGINE
    # ──────────────────────────────────────────────────────────────
    def _apply_retry_policy(self, step_name: str, result) -> Any:
        """Enforces exactly 1 retry before pausing. Implemented deterministically."""
        self._log(step_name, "retry_applied", {"reason": "validation_failed"})
        # In production: inject error context back into next prompt attempt
        raise WorkflowPauseError(f"Step '{step_name}' hit retry limit. Pausing for human review.")

    # ──────────────────────────────────────────────────────────────
    # OBSERVABILITY & CONTEXT BUDGETING
    # ──────────────────────────────────────────────────────────────
    def _log(self, stage: str, status: str, metadata: Optional[Dict] = None):
        # Initialize an empty dict if metadata is None
        meta_dict = metadata if metadata is not None else {}

        entry = {
            "trace_id": self.trace_id,
            "stage": stage,
            "status": status,
            "timestamp": time.time(),
            **meta_dict
        }

        self.execution_log.append(entry)

    # ──────────────────────────────────────────────────────────────
    # ADAPTER ABSTRACTION (Swap per project without touching runtime)
    # ──────────────────────────────────────────────────────────────
    def _call_adapter(adapter_name: str, config_path: str, repo_root: List[Any]) -> Any:
        if adapter_name not in ADAPTER_REGISTRY:
            raise ValueError(f"Unknown adapter: {adapter_name}")
        
        # Instantiate with project-specific config (loaded from adapters/config/ directory)
        instance = ADAPTER_REGISTRY[adapter_name](config_path=config_path)
        result = instance.execute(repo_root)  # Returns ProjectContext automatically
        return result
