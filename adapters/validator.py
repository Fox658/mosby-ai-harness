from adapters.tools import ValidationResult, CodeDiffBundle

class ValidationGuardrail:
    def __init__(self, linter_config: dict):
        self.config = linter_config  # rubocop rules, rsc profile, formatter flags
        
    def validate(self, diff_bundle: CodeDiffBundle) -> ValidationResult:
        """Runs static analysis. Returns pass/fail + actionable error list."""
        pass
