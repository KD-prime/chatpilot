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
This repo ALREADY has tests and structure like:
- tests/test_main.py
- tests/api/** (e.g., tests/api/auth/test_auth.py)
- existing README.md files inside tests/**

New Goal:
In addition to documentation + traceability, CREATE NEW TEST SCRIPTS (.py) in the existing test structure under tests/, in the appropriate folders, and update/add README.md files where needed.

Non-Negotiable Rules:
- Do NOT move, rename, or delete any existing tests or folders.
- Follow the existing test style in the repo (pytest markers, async patterns, TestClient/AsyncClient usage, patch/AsyncMock usage, fixtures).
- Do NOT invent endpoints/routes. Only test routes/triggers that are discoverable in code (routers included, FastAPI app setup, route decorators, etc.).
- Do NOT invent env vars/services. If a dependency is external, mock it (unless there is a local emulator already used in repo).
- Use only files/modules that exist in the workspace.
- If something cannot be confirmed from the repo, write “Not found in repo” in docs and do not create a fake test for it.

Process (do in this order):
1) Scan the WebApp_Product_BackEnd code to identify:
   - FastAPI app creation and router includes
   - route paths + HTTP methods (from code)
   - core services modules (services/*)
   - integrations modules (integrations/*)
   - config/settings usage (config.py, settings, etc.)
2) Scan existing tests to match conventions:
   - how they create app/client
   - how they patch/mocks async funcs
   - how they structure fixtures
   - naming conventions and folder placement
3) Identify 5–10 high-value test gaps (missing coverage) based on code.
4) Implement new tests to fill those gaps with minimal risk:
   - prefer deterministic tests
   - mock external calls
   - test both success + failure paths

Deliverables (must implement all):

A) Create/Update testing docs + traceability (same as before)
1) Update/create:
   - tests/README.md
   - TESTING.md
   - TRACEABILITY.md
2) Ensure docs reflect the REAL test structure and the NEW tests you add.

B) Add NEW TEST FILES in the correct existing folders under tests/
Guidelines:
- API/endpoint tests go under tests/api/<module>/test_*.py
- Non-API tests go under tests/<area>/test_*.py (only if that area already exists; otherwise create a minimal folder + README.md)
- Keep tests small and focused.

Minimum new tests to create (choose based on what exists in code):
1) Health/Root behavior test (if route exists) OR startup/config sanity test
   - If an endpoint exists in main/app, add to tests/test_main.py or a new test file beside it.
2) Auth-related tests (expand beyond current) if auth routes/services exist:
   - Add at least 2 additional cases not already covered:
     - invalid payload validation
     - missing/expired token behavior (only if implemented)
     - refresh/logout edge cases
3) One services-layer unit test file (no HTTP):
   - Create tests/services/test_<service>.py for a service module that contains logic.
   - Mock integrations.
4) One integration wrapper test file (mocked):
   - Create tests/integrations/test_<integration>.py validating error mapping, retries/timeouts if present.
5) One negative/error-shape test:
   - Ensure API returns consistent error response for a known failure path (only if defined in code).

Important:
- Do not write placeholder tests. Every test must actually import real modules and assert real behavior.
- If the repo uses async routes/services, use pytest.mark.asyncio consistently.
- If FastAPI app exists, prefer httpx.AsyncClient + ASGITransport if that’s already used (as seen in tests/test_main.py).
- Reuse existing fixtures patterns rather than inventing new ones.

C) Create/Update README.md inside each tests subfolder you touch
For each tests subfolder where you add tests (e.g., tests/api/auth/, tests/services/, tests/integrations/):
- Ensure there is a README.md describing:
  - purpose of that test folder
  - what files exist there (list real test files)
  - what they cover (brief)
  - how to run that subset (pytest -k / path-based) ONLY if pytest is confirmable; otherwise “Not found in repo” + “Proposed”

D) Ensure tests are runnable
- If pytest is configured in repo, ensure imports resolve and paths are correct.
- If needed, add minimal conftest.py only if it improves reuse and matches repo style (do not over-engineer).
- Do not change application code unless necessary for testability; if necessary, make minimal, safe changes and explain why.

Output (must provide):
1) A list of NEW files created (test .py + README.md) and UPDATED files.
2) A “Current Test Inventory” table:
   test path → type (unit/functional/api) → what it validates.
3) Commands to run:
   - all tests
   - a single folder (e.g., tests/api/auth)
   - a single test file
   Only if pytest/tooling is confirmable from repo; otherwise mark commands as “Proposed”.
