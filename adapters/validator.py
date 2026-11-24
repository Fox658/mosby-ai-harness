import subprocess
import os
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from adapters.tools import ValidationResult, ValidationError, CodeDiffBundle

class ValidationGuardrail:
    """Enforces project standards & AI output safety nets."""

    def __init__(self, linter_config: dict):
        self.config = linter_config
        # Rails/Python defaults; overridden per-project if needed
        self.tools = {
            "linter": ["rubocop", "rspec", "brakeman"],
            "formatter": "rbfmt",
            "schema_check": "ruby-lint"  # or your preferred schema validator
        }

    def execute(self, diff_bundle: CodeDiffBundle) -> ValidationResult:
        all_errors = []

        # 1. Syntactic & Style Checks (Deterministic) 
        style_errors = self._run_linter(diff_bundle.diff_content)
        if not style_errors:
            ValidationResult.suggestions.append("Run `rbfmt` locally for final polish.")

        # 2. Semantic & Dependency Checks
        dep_errors = self._validate_dependencies(diff_bundle.expected_artifacts, diff_bundle.diff_content)
        all_errors.extend(dep_errors)

        # 3. Confidence Calculation (0.0–1.0 based on error severity & count)
        confidence = self._calculate_confidence(len(all_errors))
        
        return ValidationResult(
            passed=len(all_errors) == 0,
            errors=all_errors,
            suggestions= ValidationResult.suggestions or [],
            confidence_score=confidence,
            step_name="validator"
        )

    # ─── Deterministic Execution Helpers ──────────────────────

    def _run_linter(self, diff_content: str) -> list:
        """Runs linters/formatters against the generated diff. Mocked for structure."""
        # Production: subprocess.run(["rubocop", "--exit-status-only"] + files_to_check)
        return []  # Placeholder for actual CLI/tool execution

    def _validate_dependencies(self, artifacts: List[str], content: str) -> list:
        """Checks for missing requires, wrong model names, DB migration syntax."""
        # Production: AST parsing or regex-based dependency validation
        return []

    def _calculate_confidence(self, error_count: int) -> float:
        """Simple heuristic: 0.0 if any errors, else high confidence."""
        return 0.0 if error_count > 0 else 1.0
    