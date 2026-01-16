"""
github_models_chat.py
---------------------

- Minimal wrapper for GitHub Models chat-completion endpoints.
- Provides:
  - ChatGithub        class (llm.invoke / llm(...) / llm.list_models)
  - get_all_models()  helper (returns every model ID)

Requirements
------------
pip install requests

Environment variables
---------------------
GH_MODELS_TOKEN : fine-grained PAT with 'models:read'
GH_MODELS_ORG   : (optional) org login to attribute usage
"""

from __future__ import annotations

import json
import os
import typing as _t

import requests


# ---------------------------------------------------------------------
# Helper: fetch full model catalog
def get_all_models(token: str | None = None) -> list[str]:
    """
    Return a list of every model ID currently published on GitHub Models.

    token : PAT with 'models:read', or None to pull from $GH_MODELS_TOKEN
    """
    token = token or os.getenv("GH_MODELS_TOKEN")
    if not token:
        raise RuntimeError(
            "GitHub Models token missing 🟨 pass token=... or set GH_MODELS_TOKEN."
        )

    hdrs = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = "https://models.github.ai/catalog/models"
    r = requests.get(url, headers=hdrs, timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json()]


# ---------------------------------------------------------------------
# Main wrapper
class ChatGithub:
    """
    Minimal chat-completion client for GitHub Models.

    llm = ChatGithub(model="openai/gpt-4.1", temperature=0.3)
    llm.invoke("Hello")                    # non-streaming
    for t in llm("stream me", stream=True):  # alias for invoke(...)
        ...

    Static utility:
        ChatGithub.list_models()  -> list[str]
    """

    # --- construction -------------------------------------------------
    def __init__(
        self,
        *,
        token: str | None = None,
        org: str | None = None,
        model: str = "openai/gpt-4.1",
        api_version: str = "2022-11-28",
        **default_params,
    ):
        self.token = token or os.getenv("GH_MODELS_TOKEN")
        if not self.token:
            raise RuntimeError(
                "GitHub Models token missing 🟨 pass token=... or set GH_MODELS_TOKEN."
            )

        self.org = org or os.getenv("GH_MODELS_ORG")
        self.endpoint = (
            f"https://models.github.ai/orgs/{self.org}/inference/chat/completions"
            if self.org
            else "https://models.github.ai/inference/chat/completions"
        )

        self.model = model
        self.api_version = api_version
        self.default_params = default_params

        self._headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": self.api_version,
            "Content-Type": "application/json",
        }

    # --- public call --------------------------------------------------
    def invoke(
        self,
        input: str | list[dict],
        *,
        stream: bool = False,
        system: str | None = None,
        **overrides,
    ) -> str | _t.Iterator[str]:
        """
        Send a prompt (or full message list) and return the assistant's reply.

        input      user string or list of (role, content) dicts
        stream     True -> return iterator of delta tokens
        system     optional system prompt inserted at top
        overrides  per-call params (temperature, tools, ...)
        """
        if isinstance(input, str):
            messages = [{"role": "user", "content": input}]
        else:
            messages = list(input)  # shallow copy to avoid mutating caller
        if system:
            messages.insert(0, {"role": "system", "content": system})

        body = dict(
            model=self.model,
            messages=messages,
            stream=stream,
            **self.default_params,  # ctor defaults
            **overrides,            # call-time overrides
        )

        r = requests.post(self.endpoint, headers=self._headers, json=body, stream=stream)
        r.raise_for_status()

        if not stream:
            return r.json()["choices"][0]["message"]["content"]

        def _stream():
            for line in r.iter_lines():
                if line.startswith(b"data: "):
                    delta = json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta

        return _stream()

    # convenience function-call alias
    __call__ = invoke

    # --- static utility ----------------------------------------------
    @staticmethod
    def list_models(token: str | None = None) -> list[str]:
        """List every model ID available on the platform."""
        return get_all_models(token)


from github_models_chat import ChatGithub
import os

# 1. Define these at the very start of your program
os.environ["GH_MODELS_TOKEN"] = "<YOUR_GH_MODELS_TOKEN>"
# os.environ["GH_MODELS_ORG"] = "py-org"  # optional

# instantiate with default temperature
llm = ChatGithub(model="openai/gpt-4.1", temperature=0.3)

# single non-streaming prompt
print("Assistant:", llm.invoke("Tell me a story"))


# fetch catalog
models = ChatGithub.list_models()
print(f"GitHub currently hosts {len(models)} models.")
print("First five:", models[:5])



@workspace

Repo scope:
service/functions/Product/WebApp_Product_BackEnd

Goal:
Create what is MISSING for “#12 Traceability: Functional-to-Technical Requirement Mapping & Test Coverage”:
1) Create/Update traceability documentation so it fully meets #12 requirements
2) Add ONLY the missing tests (unit / integration / performance) that can be implemented
   using REAL code/routes/modules in this repo, with NO guessing.

IMPORTANT:
Do NOT reference any images. The requirements are written below.

========================
#12 Traceability Requirements (must be satisfied after your changes)

A) Create/Update:
service/functions/Product/WebApp_Product_BackEnd/TRACEABILITY.md

TRACEABILITY.md must include a Markdown table with EXACT columns:
| Functional Requirement | Technical Requirement (with source file paths) | Unit Test(s) | Integration Test(s) | Performance Test(s) | Notes / Gaps |

Rules:
- Functional Requirement must be sourced from docs OR written as:
  “Inferred from code (confirm with PO/BA)” and cite the source file paths.
- Technical Requirement must cite real file paths (routes/services/integrations/config).
- Tests must cite real test file paths that exist.
- If a test type does not exist, write exactly: “Not found in repo”.
- Notes/Gaps must recommend where to add tests (path suggestion) when missing.

B) Also ensure these exist and are updated (do not delete useful content):
- service/functions/Product/WebApp_Product_BackEnd/TESTING.md
- service/functions/Product/WebApp_Product_BackEnd/tests/README.md
- service/functions/Product/WebApp_Product_BackEnd/README.md
  Add a “Traceability & Test Coverage” section linking to TRACEABILITY.md, TESTING.md, tests/README.md.

========================
Functional + Technical Requirements to map (ONLY if code exists; else “Not found in repo”)

Functional Requirements:
1) RAG — Ability to retrieve relevant documents and generate grounded responses for user queries.
2) GraphRAG — Ability to traverse knowledge graphs and retrieve connected entities for context-rich generation.
3) SAM — ONLY if code exists in repo; otherwise “Not found in repo”.

Technical Requirements:
1) Vector-based similarity search + LLM prompt orchestration for factual/grounded generation.
2) Graph traversal algorithms + entity linking + hybrid retrieval combining graph + embeddings.
3) SAM — ONLY if code exists; otherwise “Not found in repo”.

========================
Test Requirements to implement IF missing and IF confirmable from code

Unit Tests:
U1) Validate embedding generation.
U2) Validate vector store indexing and retrieval precision for sample queries.
U3) Validate graph node/edge creation.
U4) Validate graph traversal logic and entity extraction accuracy.

Integration Tests:
I1) End-to-end flow: query → retrieval → LLM generation → response formatting.
I2) Combined flow: graph traversal + vector retrieval → context building → generation.

Performance Tests:
P1) Measure latency/throughput for high-volume queries (verify against SLO only if SLO exists in repo; otherwise record metrics).
P2) Stress test graph traversal: large graphs and nested retrieval scenarios for scalability.

========================
Non-Negotiable Rules for adding tests
- Do NOT invent endpoints/routes, env vars, services, models, vector DBs, or graph DBs.
- Only test what is discoverable in code (real modules, routers, functions, classes).
- If a dependency is external (Azure OpenAI, Cosmos DB, etc.), mock it unless an emulator is already used in repo.
- Follow existing test style and tooling used in this repo:
  (pytest markers, async patterns, httpx AsyncClient + ASGITransport, TestClient usage, patch/AsyncMock usage, fixtures style).
- Do NOT move/rename/delete existing tests or folders.
- Every new test must import real modules and assert real behavior.
- If a requirement cannot be implemented because code isn’t present, do NOT create placeholder tests.
  Instead: document it as “Not found in repo”.

========================
Where to put new tests (use existing repo structure)
- If repo already uses tests/api/** for API tests, keep API tests there.
- If repo already has tests/integrations/** for integration wrappers, add integration wrapper tests there.
- If repo has tests/performance_tests/** or similar, add performance tests there; otherwise create tests/performance_tests/ + README.md.
- If repo has tests/unit_tests/** or similar, add unit tests there; otherwise create tests/unit_tests/ + README.md.
- Do NOT restructure existing tests; add minimal new folders only if needed.

========================
Process (must do in this order)
1) Re-scan the repo (code + tests + docs) and produce a “Missing Coverage List” for:
   U1–U4, I1–I2, P1–P2, plus missing traceability docs sections.
2) For each missing item, decide if it is implementable from repo code.
   - If implementable: create the test(s) with minimal mocking and deterministic assertions.
   - If not implementable: do NOT create tests; document “Not found in repo” in TRACEABILITY.md.
3) Create/Update:
   - TRACEABILITY.md (complete mapping)
   - TESTING.md (how to run tests + categories present in THIS repo)
   - tests/README.md (current structure + how to add tests)
   - README.md (links section)

4) Add only necessary README.md files in any NEW test folders you create.
   NO EMPTY READMEs.

========================
Output required (must include)
1) List of files created/updated (new tests + docs) with 1–3 bullets each.
2) “Current Test Inventory” table:
   test path → category (unit/integration/performance/api/functional) → what it validates (1 line)
3) A “Coverage Map” summary:
   U1..U4, I1..I2, P1..P2 → Covered/Not covered/Not found in repo + test paths
4) Commands to run tests (only if confirmable from repo; else label “Proposed”)
   - run all
   - run unit subset
   - run integration subset
   - run performance subset

