# adapters/tools.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict

class ProjectContext(BaseModel):
    """Lean, structured context extracted from project structure."""
    naming_conventions: Dict[str, str] = Field(default_factory=dict)
    module_boundaries: List[Dict[str, str]] = Field(default_factory=list)
    auth_patterns: List[Dict[str, str]] = Field(default_factory=list)
    db_schema_snippet: Optional[str] = None
    common_files: List[str] = []
    cache_version: str = ""  # For invalidation
    last_updated: float = 0.0

class TaskStep(BaseModel):
    """A single deterministic step in the workflow."""
    name: str = Field(..., description="Descriptive action (e.g., 'create_user_model')")
    input_context: List[str] = Field(default_factory=list)  # e.g., ['ProjectContext', 'task_1_output']
    expected_artifact: str = Field(..., description="Output artifact path or type (e.g., 'app/models/user.rb')")
    prompt_template_key: Optional[str] = None  # Reference to a templated prompt

class TaskGraph(BaseModel):
    """Ordered step graph with explicit dependencies."""
    steps: List[TaskStep] = Field(..., min_items=1)
    context_dependencies: List[str] = Field(default_factory=list)
    
    @field_validator("steps")
    def check_step_ordering(cls, v, values):
        if len(v) != values.get("expected_artifacts", {}).get("count"):
            raise ValueError("Step count mismatch with expected artifacts.")
        return v

class CodeDiffBundle(BaseModel):
    """Generated code in unified diff format."""
    diffs: List[Dict[str, str]] = Field(..., min_items=1)
    target_paths: List[str] = Field(...)
    estimated_impact: str = "medium"  # low/medium/high

class ValidationError(Exception):
    """Raised when validation fails beyond retry capacity."""
    pass

class ValidationResult(BaseModel):
    """Deterministic output from the validation gate."""
    passed: bool = False
    errors: List[Dict[str, str]] = Field(default_factory=list)
    suggestions: Optional[List[str]] = None
    confidence_score: float = 0.0
    step_name: str = "validator"
