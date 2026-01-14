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
1) Keep existing tests and structure (DO NOT move/rename/delete existing tests).
2) Ensure standardized test-category folders exist under tests/:
   - tests/unit_tests/
   - tests/functional_tests/
   - tests/integration_tests/
   - tests/regression_tests/
   - tests/performance_tests/
   Each must have a README.md (create or update) that links to EXISTING tests (e.g., tests/api/**, tests/test_main.py) and explains where new tests should go.

3) Add ONE script:
   tests/run_all_tests.py
   so I can run ALL tests by doing:
   cd service/functions/Product/WebApp_Product_BackEnd/tests
   python run_all_tests.py

4) Add requirements files under tests/:
   - tests/requirements.txt
   - tests/dev_requirements.txt (or tests/requirements-dev.txt if that naming already exists)
   These must be consistent with what the repo actually uses.

5) Ensure there is a high-quality index README at:
   tests/README.md
   (create if missing, update if present)

Non-Negotiable Rules:
- Do NOT invent endpoints/routes/env vars/services/files.
- Only reference what exists in the workspace.
- Do NOT break current test execution.
- Detect the actual test runner used in the repo; prefer pytest if present.
- If a dependency/version cannot be confirmed, do not pin random versions; prefer referencing repo-level requirement files via -r.

Task A — Create/Update tests/README.md (index)
Create or update:
service/functions/Product/WebApp_Product_BackEnd/tests/README.md

Must include:
1) Overview of test philosophy (short, beginner-friendly)
2) Current test structure (what exists today):
   - tests/test_main.py (what it validates)
   - tests/api/** (group by subfolders)
   - any other existing test folders
3) Category view (links to):
   - unit_tests/README.md
   - functional_tests/README.md
   - integration_tests/README.md
   - regression_tests/README.md
   - performance_tests/README.md
4) How to install test deps:
   - pip install -r dev_requirements.txt
5) How to run all tests:
   - python run_all_tests.py
6) How to run subsets (examples):
   - python run_all_tests.py --path api/auth --verbose
   - python run_all_tests.py --k "auth and not slow" --maxfail 1 --capture no
7) Conventions:
   - naming (test_*.py)
   - where to place new tests
   - mocking guidance (based on what repo uses)

Task B — Category folders + READMEs
Create the five folders if missing (do not move tests into them):
- tests/unit_tests/
- tests/functional_tests/
- tests/integration_tests/
- tests/regression_tests/
- tests/performance_tests/

For EACH folder create/update README.md including:
1) Purpose (plain English)
2) What qualifies as this category in THIS repo
3) “Existing tests that belong here” with links to REAL test files (do not invent)
4) “Where new tests should go” (conventions + suggested filenames)
5) Candidate coverage list of REAL application .py modules (paths only)

Task C — Create tests/run_all_tests.py (must work with “python run_all_tests.py”)
Create:
service/functions/Product/WebApp_Product_BackEnd/tests/run_all_tests.py

Hard Requirements:
- Running from tests/ MUST work:
  python run_all_tests.py
- Runs entire suite under tests/ including tests/test_main.py and tests/api/**
- Uses pytest programmatically via pytest.main([...]) if pytest is confirmed in repo
- Adds repo root to sys.path so imports resolve
- Debug-friendly output:
  - repo root detected, tests path used, runner detected
  - PASS/FAIL summary + exit code
- CLI flags (argparse):
  --path <subpath> (default tests/)
  --k <expr>
  --maxfail N (default 1)
  --verbose / --quiet
  --pdb / --lf
  --capture {no,sys,fd} (default no)
  --junitxml <file>
- If pytest not installed, print actionable message pointing to dev_requirements.txt and exit 2
- Proper exit codes: 0 pass, non-zero fail/error

Task D — Add tests requirements files
Create under tests/:
1) requirements.txt
2) dev_requirements.txt (or requirements-dev.txt if repo naming prefers)

Rules:
- Prefer referencing repo-level requirements with -r ../<file> ONLY if those files exist.
- If no repo-level files exist, derive deps from actual imports in tests (pytest/httpx/etc.)
- Do not pin arbitrary versions unless already pinned elsewhere in repo.

Output:
- Summary table: created/updated files and what changed
- Show the CLI help (or concise usage) for run_all_tests.py
- Confirm default workflow works:
  cd tests && pip install -r dev_requirements.txt && python run_all_tests.py
