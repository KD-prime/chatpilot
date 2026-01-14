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

Non-Negotiable Structure Rule:
There MUST NOT be a top-level folder: tests/api/
All endpoint/API tests must live under:
tests/functional_tests/api/<area>/test_*.py

Allowed canonical structure (ONLY these top-level folders under tests/):
tests/
  README.md
  run_all_tests.py
  requirements.txt
  dev_requirements.txt
  unit_tests/
  functional_tests/
  integration_tests/
  regression_tests/
  performance_tests/

Inside category folders you may create subfolders like:
- tests/functional_tests/api/auth/
- tests/unit_tests/services/
- tests/integration_tests/integrations/
But do NOT create tests/api at the top level.

Hard Rules:
- Do NOT invent endpoints/routes/env vars/services/files.
- Only reference and test what exists in workspace.
- If something cannot be confirmed, write exactly: “Not found in repo”.
- NO EMPTY README.md files (must contain useful content even if folder is empty).
- Prefer pytest if confirmed via real files/imports.
- External dependencies must be mocked unless repo clearly uses a local emulator.
- Keep diffs clean and easy to review.

You are allowed to MOVE existing test files to satisfy the structure rule:
- You MAY move tests/api/** into tests/functional_tests/api/**
- You MAY move tests/test_main.py into tests/functional_tests/ (or functional_tests/smoke/)
- Do NOT delete tests; only relocate and update imports/paths if needed.
- After moving, remove the old top-level tests/api folder.

Process (do in order):

1) Scan backend code (REAL discovery)
- Locate FastAPI app creation (main.py or equivalent).
- Enumerate routes: path + method + handler module by reading decorators and router includes.
- Identify core modules: services/**, integrations/**, config/settings usage.
Create/Update:
- TEST_SURFACE_MAP.md (repo root)
  Include tables:
  - Routes discovered (method, path, module:function)
  - Service modules discovered
  - Integration modules discovered
  - Settings/env usage discovered (only if explicitly referenced)

2) Scan current tests (if any exist)
- Detect existing patterns: pytest, asyncio markers, TestClient vs httpx AsyncClient + ASGITransport,
  patch/AsyncMock usage, fixtures style.
- Build a current test inventory (real paths only).

3) Enforce category-first structure (NO tests/api)
- Ensure these exist:
  tests/unit_tests/
  tests/functional_tests/
  tests/integration_tests/
  tests/regression_tests/
  tests/performance_tests/
- If any top-level tests/api exists:
  - Move it to: tests/functional_tests/api/
    Example: tests/api/auth/test_auth.py -> tests/functional_tests/api/auth/test_auth.py
- If tests/test_main.py exists at top-level:
  - Move it to: tests/functional_tests/test_main.py (or tests/functional_tests/smoke/test_main.py)
- If other stray test folders exist, classify and move them into the right category folder.
- After migration, DELETE the now-empty old folders (especially tests/api).

4) Fix and expand READMEs (NO EMPTY READMEs)
Create/Update:
A) tests/README.md (single index, must be high quality)
Must include:
- Overview + how this repo organizes tests (category-first)
- Structure diagram (simple ASCII)
- How to install test deps (dev_requirements)
- How to run all tests: python run_all_tests.py (from tests/)
- How to run subsets (examples with --path under category folders)
- Conventions: naming, fixtures, mocking patterns (based on real tests)

B) For each category folder, create/update README.md with:
- Purpose
- What belongs here in THIS repo
- What exists currently (list real test files in that folder)
- What it covers (brief)
- How to run this subset (ONLY if confirmable; else “Proposed”)
- Where to add new tests
If folder has no tests yet: write “No test files in this folder yet” plus guidance.

5) Find missing potential tests (gap analysis based on real code)
Create/Update:
- TEST_GAP_REPORT.md (repo root)
Include:
- “Current Test Inventory” table:
  test path | category | what it validates | source modules
- “Top 10–15 Highest-Value Gaps”:
  gap | why it matters | exact source module paths | suggested new test path under correct category

6) Implement new tests (ONLY what is confirmable)
Add 5–10 high-value tests maximum, placed only under category folders:
- Unit tests:
  tests/unit_tests/services/test_<service>.py OR tests/unit_tests/utils/test_<util>.py
- Functional/API tests:
  tests/functional_tests/api/<area>/test_<area>.py
- Integration wrapper tests (mocked):
  tests/integration_tests/integrations/test_<integration>.py

Requirements for new tests:
- Must import real modules and assert real behavior found in code
- Must include success + failure path only where code supports it
- Must follow existing pytest style in repo (async markers, AsyncMock/patch, client style)
- Must not require real external services

7) Ensure run_all_tests.py runs everything
- Ensure tests/run_all_tests.py discovers tests recursively under tests/ (including category folders)
- It must run when executed from tests/:
  cd .../tests
  python run_all_tests.py
- Print clear PASS/FAIL summary + list failures for debugging.

8) Update TRACEABILITY.md + TESTING.md (if they exist; create if requested previously)
- TRACEABILITY.md must map functional -> technical -> tests
- Must reference real test paths in the category folders
- Any unknown requirement must be marked: “Inferred from code (confirm with PO/BA)” and cite file paths

Output (must provide):
1) Final tests/ tree (after reorg)
2) Summary table: moved from → moved to (for every moved test)
3) List of files created/updated (1–3 bullets each)
4) Top 10 test gaps (from TEST_GAP_REPORT.md)
5) Commands:
   cd service/functions/Product/WebApp_Product_BackEnd/tests
   python run_all_tests.py
   python run_all_tests.py --path functional_tests/api/<area>
   python run_all_tests.py --path unit_tests --k "<keyword>" --maxfail 1 --capture no
