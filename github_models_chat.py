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

Context (must respect):
This repo ALREADY has tests, e.g.:
- tests/test_main.py
- tests/api/** (e.g., tests/api/auth/test_auth.py)
- some README.md files under tests/**

Goal:
Create high-quality, enterprise-grade testing documentation + traceability mapping,
WITHOUT breaking or restructuring existing tests.

Non-Negotiable Rules:
- Do NOT move, rename, or delete any existing tests or folders.
- Do NOT invent endpoints/routes, env vars, requirements, services, or files.
- Only reference what exists in the workspace (code/config/docs).
- If something cannot be confirmed from the repo, write exactly: “Not found in repo”.
- If you infer something from code structure, label it clearly as:
  “Inferred from code (confirm with PO/BA)”, and cite the source file paths.

Process (do in this order):
1) Scan the folder tree under WebApp_Product_BackEnd.
2) Identify what testing framework/tools are actually used by checking real files:
   - dev_requirements.txt / requirements*.txt / pyproject.toml
   - existing test files (imports like pytest, httpx, TestClient, etc.)
3) Read existing tests to understand how they are structured (api tests vs general tests).
4) Then create/update docs below.

Deliverables:

A) Create/Update: tests/README.md (source of truth for test layout)
Path:
service/functions/Product/WebApp_Product_BackEnd/tests/README.md

Must include:
1) “What’s in tests/” — describe CURRENT structure based on what exists:
   - tests/test_main.py (what it validates, based on assertions)
   - tests/api/** (group by subfolders like auth, etc.)
2) “Test Categories in THIS repo” — map categories to real folders/files:
   - Unit tests (pure functions/modules; no HTTP client)
   - Functional/API tests (endpoint-level tests with TestClient/AsyncClient)
   - Integration tests (real external service/emulator usage, if any)
   - Regression tests (tests that prevent previously fixed bugs)
   - Performance tests (load/latency), if any exist
   For each category: say where they currently live in THIS repo, or “Not found in repo”.
3) “How to run tests” — ONLY if commands are confirmable from repo config.
   If not confirmable, provide a clearly labeled “Proposed” section.
4) “How to add a new test” — follow existing conventions in this repo:
   naming, folder placement, fixtures, mocking patterns.

B) Create/Update: TESTING.md (high-quality testing guide)
Path:
service/functions/Product/WebApp_Product_BackEnd/TESTING.md

Must include:
1) Short definitions (unit/functional/integration/regression/performance) in plain English
2) Recommended order: what to test first (high-signal)
3) Mocking guidance based on repo reality:
   - how to patch correctly (AsyncMock/patch if used)
   - what to mock vs what not to mock
4) “Coverage Strategy” — what parts of the system deserve tests first, based on:
   - auth/security critical paths
   - core business logic
   - external integrations
   - config/validation
   Reference REAL modules by file paths.
5) If pytest is used: include a brief pytest section (markers, async tests).
   If not: “Not found in repo”.

C) Create/Update: TRACEABILITY.md (functional→technical→tests mapping)
Path:
service/functions/Product/WebApp_Product_BackEnd/TRACEABILITY.md

Must include a traceability table (Markdown) with columns:
- Functional Requirement
- Technical Requirement (with source file paths)
- Existing Unit Test(s) (real test paths)
- Existing Functional/API Test(s) (real test paths)
- Existing Integration Test(s) (real test paths or “Not found in repo”)
- Existing Performance Test(s) (real test paths or “Not found in repo”)
- Notes / Gaps

Rules for traceability rows:
- Prefer explicit requirements if found in docs/READMEs; otherwise create inferred rows:
  “Inferred from code (confirm with PO/BA)”
- Every inferred row MUST cite the code files that justify it.
- Link to EXISTING tests where possible (e.g., tests/api/auth/test_auth.py, tests/test_main.py).
- Identify gaps where no test exists and recommend where to add it (path suggestion),
  but do not create new test .py files unless explicitly asked.

D) Optional clarity folders (documentation-only, no restructuring)
Only if it improves clarity and does NOT already exist:
- tests/unit/README.md
- tests/integration/README.md
- tests/performance/README.md

These should:
- Explain what belongs there in this repo
- Reference current tests that already exist elsewhere (do not move them)

E) Link from Master README
Update:
service/functions/Product/WebApp_Product_BackEnd/README.md

Add section: “Testing & Traceability”
with links to:
- TESTING.md
- TRACEABILITY.md
- tests/README.md

Output (must provide):
1) A list of files created/updated and what changed in each (1–3 bullets per file).
2) A “Current Test Inventory” table:
   Test file → category (unit/functional/integration) → what it validates (1 line).
3) Top 5 highest-value test gaps (based on repo scan), each with:
   - what to test
   - why it matters
   - suggested location (test file path)
   - source modules (file paths)
