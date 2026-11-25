Excellent choice. Let’s move into **Phase 2: Production Hardening**. We’ll transform your synchronous prototype into a resilient, distributed-ready system without losing the conceptual clarity we’ve built so far.

---

### 🔍 Concept First: What "Production Hardening" Actually Means
In agentic workflows, production readiness isn’t about adding more AI features. It’s about **making probabilistic execution deterministic in its failure modes**. A sync prototype works for one user on one machine. Production requires it to survive:
- Network timeouts & LLM API rate limits
- Partial step failures (e.g., code generation succeeds, validation fails)
- Multi-instance deployments & concurrent requests
- State loss during restarts or cache evictions

Hardening solves this by introducing **explicit state management**, **idempotent execution**, and **graceful degradation patterns**. The core runtime logic stays identical; only the execution envelope changes.

---

### 🧱 Production Architecture Components & Trade-offs

| Component | What It Does | Why It’s Necessary | Trade-off & Mitigation |
|-----------|--------------|-------------------|------------------------|
| **Async Job Wrapper (Sidekiq)** | Transforms sync controller actions into background jobs with persistence, retries, and status updates | Prevents thread blocking; enables horizontal scaling & graceful shutdowns | Adds job state management complexity. Mitigation: Use `sidekiq-cron` or status callbacks to push progress back to the UI without polling. |
| **Durable State Persistence** | Serializes `current_state`, `trace_id`, and step metadata to DB/Redis with TTLs | Survives process restarts, cache clears, or partial failures | Slight I/O latency on each step. Mitigation: Use PostgreSQL `jsonb` for structured state; only persist at step boundaries, not mid-execution. |
| **Idempotency Keys** | Unique token per workflow run prevents duplicate execution if a request times out or retries | Stops AI from generating the same diff twice, corrupting DB or wasting tokens | Requires key generation/storage strategy. Mitigation: `idempotency_key = hash(user_id + repo_hash + step_name)` stored in Redis/DB. |
| **Graceful Degradation** | Detects LLM timeouts/API errors → falls back to deterministic parsing where possible, or safely pauses with clear error state | Prevents cascade failures & silent data corruption | Requires explicit fallback routing logic per adapter. Mitigation: Keep adapters thin; wrap LLM calls in timeout + retry decorators. |
| **Observability Hooks** | Tracks step latency, token estimates, retry counts, and validation pass/fail rates | Enables alerting, cost tracking, and post-mortem analysis | Adds infrastructure overhead. Mitigation: Start with structured logging + Prometheus metrics; defer full dashboards until v2. |

---

### 🔌 How It Plugs Into Your Existing Scaffold
Your `agent_runtime.py` doesn’t change architecture-wise. Instead, you wrap it in a production envelope:
1. **Job Entry Point**: Sidekiq job receives payload → generates `idempotency_key` → checks DB for existing run → if new, initializes state & starts pipeline.
2. **Step Execution Loop**: Calls `_call_adapter()` as before, but now each step:
   - Persists intermediate state to DB
   - Tracks latency/cost in metrics
   - Enforces retry/backoff on network/API failures (not just validation failures)
3. **Completion/Timeout Handling**: On success → marks `ready_for_review`. On hard failure → emits `review_pending` or `failed` with full trace log for audit.
4. **State Recovery**: If a worker crashes mid-pipeline, the next worker picks up from the last persisted step state using the same `idempotency_key`.

---

### ⚠️ Anti-Patterns & Explicit Trade-offs (Production-Ready)
| Risk | Why It Happens | How This Design Prevents It |
|------|----------------|----------------------------|
| **Duplicate work on retries** | HTTP timeouts cause client to resubmit, spawning duplicate jobs | Idempotency keys + DB-side unique constraints prevent re-execution |
| **Context drift across workers** | Different nodes cache differently; state gets out of sync | Centralized state store (Postgres) with versioning & atomic updates |
| **Over-engineering caching early** | Adding Redis/Vault before proving demand → maintenance debt | Start with DB-backed sessions + TTLs. Add distributed cache only when scaling >50 concurrent jobs |
| **Ignoring LLM provider variability** | Assuming fixed latency/cost per step causes job starvation | Adaptive backoff, per-step timeouts, and budget guards instead of hard limits |

---

### 🛠️ Next Implementation Focus (Pick One)
We’ve mapped the production envelope. To keep the learning loop tight and concept-driven, which sub-layer should we drill into next?

1. **Idempotency & State Persistence Layer**: How to generate keys, store state atomically, and safely resume interrupted workflows without duplicating work.
2. **Async Job Wrapper + Retry/Timeout Policies**: How Sidekiq integrates with your runtime, handles provider outages gracefully, and pushes status updates back to your Rails controller.

Reply with `1` or `2`, and I’ll provide the exact architectural blueprint + minimal implementation scaffolding. We’ll keep it concept-first, production-aware, and strictly aligned with your reusable-harness goal.