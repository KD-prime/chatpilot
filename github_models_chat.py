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


@workspace

Repo scope:
service/functions/Product/WebApp_Product_BackEnd

Context:
I have manually deleted EVERYTHING under:
service/functions/Product/WebApp_Product_BackEnd/tests/
So tests/ is empty (or will be empty). Recreate it cleanly.

Goal:
Rebuild a clean, canonical tests/ structure with:
- 5 top-level test category folders (each with README.md)
- tests/README.md index
- tests/run_all_tests.py runnable via: python run_all_tests.py (when executed from tests/)
- tests/requirements.txt + tests/dev_requirements.txt
- Recreate essential tests based ONLY on real app code (no guessing)

Canonical tests/ structure (MUST match exactly; do not add extra folders):
tests/
  README.md
  run_all_tests.py
  requirements.txt
  dev_requirements.txt
  unit_tests/
    README.md
  functional_tests/
    README.md
  integration_tests/
    README.md
  regression_tests/
    README.md
  performance_tests/
    README.md

Hard Rules:
- Do NOT invent endpoints/routes/env vars/services. Only use what exists in workspace.
- Only create test files for features you can prove exist by reading code.
- If something cannot be confirmed, write “Not found in repo” in docs and skip test creation for it.
- Prefer pytest if confirmed by repo dependencies/config/imports.
- Do not require external services to be running; mock external calls unless local emulators already exist and are clearly configured in repo.

Process (do in this order):
1) Scan repo for testing stack & entrypoints:
   - Look for: dev_requirements.txt, requirements*.txt, pyproject.toml
   - Identify: pytest usage, httpx, fastapi, TestClient, ASGITransport
2) Find how the FastAPI app is constructed:
   - locate main.py (or equivalent) and app = FastAPI()
   - identify included routers and their route prefixes + methods (from decorators)
3) Identify core modules worth testing:
   - services/*
   - integrations/*
   - config/settings usage
   - any auth/security modules

Deliverables:

A) Create the canonical folder structure above exactly (no extras).
- Create README.md in each of the 5 category folders with:
  1) Purpose (novice-friendly)
  2) What belongs here in this repo
  3) Candidate coverage list (REAL modules paths only)
  4) How to run (only if confirmed; otherwise “Proposed”)

B) Create tests/README.md (index)
Must include:
- Overview
- Folder guide (what each category is)
- How to install deps:
  pip install -r dev_requirements.txt
- How to run all:
  python run_all_tests.py
- How to run subsets:
  python run_all_tests.py --path unit_tests
  python run_all_tests.py --path functional_tests --k "auth"
- Notes on mocking + test conventions used in this repo (based on actual patterns found).

C) Create tests/requirements.txt and tests/dev_requirements.txt
Rules:
- Prefer referencing repo-level files using -r ../<file> if those exist.
- If no repo-level requirement file exists, infer deps ONLY from actual imports in app/tests stack.
- Do not pin random versions unless pinned elsewhere in repo.
- Ensure dev_requirements includes pytest and any libs needed to execute tests.

D) Create tests/run_all_tests.py (must support “python run_all_tests.py”)
Hard Requirements:
- Must be runnable when current working dir is tests/:
  python run_all_tests.py
- Must run ALL tests under tests/ recursively.
- Use pytest.main([...]) if pytest is present.
- Add repo root to sys.path so imports resolve.
- Provide clear output:
  - repo root detected
  - tests directory detected
  - runner detected
  - PASS/FAIL summary
  - exit code
  - list failed node IDs if available
- Provide CLI flags:
  --path <subpath>      (default: ".")
  --k <expr>
  --maxfail N (default 1)
  --verbose / --quiet
  --pdb / --lf
  --capture {no,sys,fd} (default no)
  --junitxml <file>
- Exit codes: 0 pass, non-zero fail/error.
- If pytest missing: print exact instruction to install via dev_requirements.txt then exit 2.

E) Create initial test files (ONLY if confirmable from code)
Create only the tests you can prove:
1) A basic app health/root test IF a health/root endpoint exists.
   - If not found, create a “startup/config import test” that ensures app imports successfully.
2) One services-layer unit test for a service module containing pure logic (mock integrations).
3) One integration-wrapper test (mocked) only if integrations modules exist.

Place the tests in the appropriate category folders:
- unit_tests/test_*.py
- functional_tests/test_*.py
- integration_tests/test_*.py
(Do not create tests in regression_tests/ or performance_tests/ unless there is a clear basis in repo)

Output:
- Print the final tests/ tree you created.
- Provide a summary table:
  file created → why it exists → what it covers
- Provide the exact commands that should work:
  cd service/functions/Product/WebApp_Product_BackEnd/tests
  pip install -r dev_requirements.txt
  python run_all_tests.py


# fetch catalog
models = ChatGithub.list_models()
print(f"GitHub currently hosts {len(models)} models.")
print("First five:", models[:5])
