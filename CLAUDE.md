# CLAUDE.md — SHBVN AI Platform

## Project identity

This is the SHBVN AI Platform, a fork of RAGFlow (github.com/infiniflow/ragflow, Apache-2.0, v0.24.0) customized for Shinhan Bank Vietnam. We deliver three product tracks on one platform:

- **Track A — Internal Chatbot:** RAG over SHBVN policies, procedures, circulars, legal docs for 2000 HO employees
- **Track B — Customer Chatbot on SOL App:** RAG over public product catalog for SOL mobile banking users
- **Track C — Analytics & Data Governance:** Text-to-SQL + dashboards over the Data Warehouse for management and analysts

All work is governed by the Business Requirements Document (BRD).

## Environments

**Dev (this machine):** macOS, Apple Silicon (ARM64, M4).
**Deploy (target):** Linux, Intel x86_64, air-gapped internal network — no internet access.
**Transport:** offline bundle copied via USB from dev → server.

Implications you MUST respect:

- **Cross-architecture builds.** Build container images with `--platform linux/amd64`. Before adding a Python/Node dependency, verify an `x86_64` wheel / prebuilt binary exists upstream. Avoid packages that only ship ARM wheels.
- **No runtime internet on deploy.** Production code must not call external APIs, `pip install`, `npm install`, or fetch from HuggingFace / Docker Hub / CDNs at runtime. Everything required at runtime must already be on disk.
- **Offline bundle discipline.** When adding any new dependency, model weight, OCR resource, tokenizer, NLTK corpus, or Docker image, update the offline-bundle manifest so it's included in the USB handoff. Document what was added and where it lives on the server filesystem.
- **LLM / embedding / reranker inference.** Production uses self-hosted **vLLM or Ollama** on the internal network. Do NOT hard-code calls to OpenAI / Anthropic / Gemini / any cloud provider in deploy code paths. Use RAGFlow's `rag/llm/` abstraction and point it at the internal endpoint via `shbvn-config/`.
- **External agent tools.** RAGFlow agent tools that need internet (Tavily, Wikipedia, Google Search, etc.) must be disabled in deploy config or replaced with an internal equivalent. Do not ship a workflow that silently depends on them.
- **Validation across arch.** Code that only ran on macOS/ARM has not been validated for deploy. Before declaring work done, either run it under `linux/amd64` (Docker or CI) or explicitly flag the gap in the PR.

## Read the BRD first

**On your very first turn of any new session,** before answering anything else, read the following four sections of the BRD from `shbvn-docs/SHBVN_AI_Platform_BRD_v2.md`:

1. Section 1 — Overview
2. Section 3 — Architecture
3. Section 4 — Repository Strategy
4. Section 25 — Development Workflow

These give you project context. Then read the specific module sections relevant to the session's task.

Do not proceed with implementation work without having the BRD context. If you're unclear which module a request falls under, ask.

## Non-negotiable rules

1. **Never modify upstream RAGFlow files** (anything outside `shbvn/`, `shbvn-track-*/`, `shbvn-config/`, `shbvn-migrations/`, `shbvn-tests/`) except the minimal list in BRD section 4.3. If you must modify an upstream file, wrap the change in:
   ```python
   # === SHBVN CUSTOMIZATION START (ticket: <id>, reason: <brief>) ===
   <your code>
   # === SHBVN CUSTOMIZATION END ===
   ```

2. **Never commit secrets.** No API keys, passwords, internal URLs, personal data, or real SHBVN documents in this repo. Use `shbvn-config/secrets.yaml` (gitignored) or environment variables. If you find existing secrets in the repo, flag them and refuse to commit until they're removed.
3. **Never put real customer or employee data in tests or fixtures.** Use synthetic data only. Real PII goes in a separate, access-controlled data store — never git.
4. **Never skip the BRD's acceptance criteria.** If implementation is "working" but doesn't meet the criteria, it's not done. Ask the user before declaring a module complete.
5. **Keep upstream compatibility.** We must be able to `git merge upstream/main` monthly without heroic effort. Isolate our code in SHBVN directories.
6. **Write tests alongside code.** Unit tests in `shbvn-tests/unit/`, integration in `shbvn-tests/integration/`. Target 80% coverage for `shbvn/` code.
7. **Respect Vietnamese regulations.** PDP Law, SBV AI Circular, Cybersecurity Law. When in doubt about a compliance question, flag it rather than guess — get confirmation from the user before proceeding.
8. **Honor the air-gap.** No runtime internet access on the deploy server (see `## Environments`). Before adding any dependency, model, or external-API call, verify it can be bundled offline and run on Linux x86_64. If a change would break the air-gap assumption, stop and escalate.

## Conventions

### Code style
- Python: use `ruff` for linting, `black` for formatting, `mypy` for types (where practical)
- TypeScript: follow RAGFlow's existing conventions in `web/`
- Docstrings: Google style
- Comments in Vietnamese are OK for domain context; code identifiers are English

### Commit messages
Conventional Commits format:
```
<type>(<scope>): <short summary>

<body if needed>

Refs: BRD section <X.Y>, <ticket>
```
Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `security`.

### File locations (per BRD section 4)
- Shared cross-track code: `shbvn/`
- Track A code: `shbvn-track-a/`
- Track B code: `shbvn-track-b/`
- Track C code: `shbvn-track-c/`
- Config: `shbvn-config/`
- Tests: `shbvn-tests/`
- DB migrations: `shbvn-migrations/`
- Docs: `shbvn-docs/`

### Testing
- Every new function: at least one unit test
- Every external interface: integration test
- Security-sensitive code (Modules 2, 14): include adversarial test cases
- Run `pytest shbvn-tests/ -x` before declaring work done

## Communication preferences

- Respond in Vietnamese for discussion; write code identifiers, comments in code, and commit messages in English
- Keep explanations concise; skip throat-clearing
- When I ask a question, answer the question first, then optionally add context
- If you're uncertain, say so — don't guess. Propose 2-3 options and your recommendation
- Before any destructive action (delete file, force push, drop table), ask once

## Working patterns

### Starting a session
1. Read the BRD context (section "Read the BRD first" above)
2. Read `shbvn-docs/progress.md` to see current state
3. Confirm with me what we're working on
4. Propose a plan for the session before coding

### During the session
- Commit in small, reviewable chunks — not one giant commit at the end
- If you hit a decision point that affects architecture, stop and ask
- If you need to read many files to understand something, do so — don't pattern-match from partial context

### Ending a session
- Update `shbvn-docs/progress.md`
- Record any new architectural decisions as ADRs in `shbvn-docs/decisions/`
- Summarize what changed and what's next

## Glossary (quick reference)

See BRD section 28 for full glossary. Common ones:

- **DDD** — the sub-department within ICT Division where this project lives
- **DW** — Data Warehouse (Oracle/Teradata)
- **PDP Law** — Personal Data Protection Law (Vietnam, 01/2026)
- **SOL** — SHBVN's mobile banking app
- **S-basic, Swing Portal** — internal document management systems
- **SBV** — State Bank of Vietnam (regulator)

## Escalate to human when

- Anything touches PDP Law compliance beyond what's in the BRD
- Anything requires access to real SHBVN production data
- A change would require a dependency that isn't already vetted
- A stakeholder decision is needed (e.g., a product decision by Retail Banking)
- An ambiguity in the BRD can be interpreted multiple reasonable ways
