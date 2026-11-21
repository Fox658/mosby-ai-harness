from adapters.tools import ProjectContext

class RepoContextExtractor:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)  # Curated paths, cache TTL, hash strategy
        
    def extract(self, repo_root: str) -> ProjectContext:
        """Returns a structured convention map. Never returns raw file contents."""
        pass  # Implementation detail isolated here
