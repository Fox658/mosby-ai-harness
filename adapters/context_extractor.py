import os
import re
import json
import time
from pathlib import Path
from adapters.tools import ProjectContext
from typing import Optional
from datetime import datetime
import hashlib

class RepoContextExtractor:
    """Deterministic context extractor. No LLM involvement."""
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.curated_paths = [
            "app/models/", "app/controllers/", "config/routes.rb"
            "db/schema.rb", "spec/requests/"
        ]
        self.cache_file = Path(__file__).parent.parent / ".agent_context_cache.json"

    def execute(self, repo_root: str) -> ProjectContext:
        cache_path = self._resolve_cache(repo_root)
        cached = self._load_cache(cache_path)
        if cached and self._is_cache_valid(cached, repo_root):
            return cached
        context = ProjectContext()
        context.cache_version = self._compute_repo_hash(repo_root)
        context.last_updated = time.time()

        self._extract_naming_conventions(context, Path(repo_root))
        self._extract_module_boundaries(context, Path(repo_root))
        self._extract_auth_patterns(context, Path(repo_root))
        self._extract_db_schema(context, Path(repo_root))

        self._save_cache(cache_path, context)
        return context
        
    # ─── Deterministic Extraction Helpers ────────────────────────

    def _extract_naming_conventions(self, ctx: ProjectContext, root: Path):
        patterns = {
            "model_plural": re.search(r'models\.rb$', str(root / "app/models.rb") or ""),
            "controller_prefix": re.search(r'/(controllers|controllers/)', str(root)) and "controllers",
            "spec_suffix": bool(list(root.glob("**/*_spec.rb"))),
            "service_naming": ["{name}Service" for name in [f.stem for f in root.rglob("*.rb") if f.is_file() and not
                                                            f.parent.name.startswith(("vendor", "lib", ".git"))]]
        }
        ctx.naming_conventions = {k: v for k, v in patterns.items() if v}

    def _extract_module_boundaries(self, ctx: ProjectContext, root: Path):
        # Extract top-level module directories
        modules = []
        for dirpath, _, filenames in os.walk(root):
            rel = Path(dirpath).relative_to(root)
            if "app" not in str(rel): continue  # Skip non-app code
            if len(str(rel.parts)) == 2:  # Top-level app dirs (models, services, jobs, etc.)
                modules.append({"name": dirpath.name.lower(), "path": str(rel)})
        ctx.module_boundaries = modules

    def _extract_auth_patterns(self, ctx: ProjectContext, root: Path):
        auth_keywords = [r"authenticate_user!", r"Pundit\.", r"before_action.*guard", r"devise"]
        for pattern in auth_keywords:
            matches = []
            for rb_file in root.rglob("*.rb"):
                if rb_file.name.endswith("_controller.rb") or rb_file.name.endswith("_service.rb"):
                    try:
                        content = rb_file.read_text(encoding="utf-8", errors="ignore")
                        if re.search(pattern, content, re.IGNORECASE):
                            matches.append(rb_file.name)
                    except Exception: pass  # Silently skip unreadable files
            if matches:
                ctx.auth_patterns.extend(matches)

    def _extract_db_schema(self, ctx: ProjectContext, root: Path):
        schema_files = [root / "db" / "schema.rb", root / "db" / "001_create_*.rb"]
        for sf in schema_files:
            if sf.exists():
                try:
                    content = sf.read_text(encoding="utf-8")
                    # Extract a clean, sanitized snippet (first 500 chars) to avoid token bloat
                    ctx.db_schema_snippet = content[:500].strip()
                    break
                except Exception: pass

    # ─── Caching & Utility ────────────────────────────────────────

    def _compute_repo_hash(self, repo_root: str) -> str:
        h = hashlib.sha256()
        for f in Path(repo_root).rglob("*"):
            if f.is_file():
                try:
                    h.update(f.read_bytes())
                except Exception: pass
        return h.hexdigest()[:12]

    def _is_cache_valid(self, cached: ProjectContext, repo_root: str) -> bool:
        current = self._compute_repo_hash(repo_root)
        if cached.cache_version != current:
            return False
        # 24-hour TTL for dev/safety; can be tuned per project
        return time.time() - cached.last_updated < 86400

    def _load_cache(self, path: Path) -> Optional[ProjectContext]:
        if not path.exists(): return None
        with open(path, "r") as f:
            data = json.load(f)
        return ProjectContext(**data)

    def _save_cache(self, path: Path, ctx: ProjectContext):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(ctx.model_dump(), f, indent=2)
