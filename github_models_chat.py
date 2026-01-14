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

Problem:
The tests/ folder structure is messy/duplicated (e.g., performance/ vs performance_tests/, integrations/ vs integration_tests/, etc.).
Fix it by consolidating into ONE canonical structure with exactly these category folders:

tests/
  api/                      (keep as-is)
  unit_tests/
  functional_tests/
  integration_tests/
  regression_tests/
  performance_tests/
  README.md
  run_all_tests.py
  requirements.txt
  dev_requirements.txt

Hard Rules:
- Do NOT lose any existing test files or useful README content.
- You MAY move/rename files/folders inside tests/ ONLY to consolidate into the canonical structure.
- Do NOT invent tests/routes/endpoints/env vars.
- After moving, update all README links/paths accordingly.
- Delete duplicate/empty folders ONLY after their contents are migrated.
- Keep git diff clean and easy to review.

Tasks (do in this order):

1) Inventory and classify
- Print a tree of current tests/ (all folders + test_*.py + README.md).
- Identify duplicates/conflicts:
  - performance/ vs performance_tests/
  - integrations/ vs integration_tests/
  - any other duplicates

2) Consolidate folders (canonicalize)
- Ensure these canonical folders exist:
  - tests/unit_tests/
  - tests/functional_tests/
  - tests/integration_tests/
  - tests/regression_tests/
  - tests/performance_tests/
- Move files into the correct canonical folder:
  - Anything under tests/performance/ -> move into tests/performance_tests/
    Example: tests/performance/test_performance.py -> tests/performance_tests/test_performance.py
  - Anything under tests/integrations/ -> move into tests/integration_tests/ (create a subfolder if needed)
    Example:
      tests/integrations/test_azure_cosmos_db.py -> tests/integration_tests/integrations/test_azure_cosmos_db.py
      tests/integrations/test_azure_openai.py    -> tests/integration_tests/integrations/test_azure_openai.py

- If tests/api/** are functional API tests, keep them in tests/api/** (do not move).
  The category folder functional_tests/ should document that tests/api/** is where API tests live.

3) Fix READMEs
- Ensure tests/README.md exists and becomes the single index:
  - “Current structure” section (tests/api/**, tests/test_main.py, etc.)
  - “Category view” section linking to the 5 category READMEs
  - “How to run”: cd tests && python run_all_tests.py
- Ensure each canonical category folder has README.md:
  - purpose
  - what belongs here
  - links to real tests (including tests/api/** if applicable)
  - where new tests should go
- If you moved any README.md from old folders, merge useful content into the canonical README.md (don’t discard).

4) Remove duplicates safely
- After migrations, remove ONLY folders that are now empty/duplicate, e.g.:
  - tests/performance/ (if emptied)
  - tests/integrations/ (if emptied)
  - any accidental extra folders
- Double-check no references remain to deleted paths.

5) Verify run_all_tests.py behavior
- Update tests/run_all_tests.py so it:
  - runs ALL tests under tests/ recursively (including tests/api/** and new canonical folders)
  - works from inside tests/: python run_all_tests.py
  - prints clear PASS/FAIL, exit code, and failure nodeids
  - supports --path for subsets (path is relative to tests/)

6) Final output
- Print a final “Before vs After” tests/ tree.
- Provide a summary table:
  file moved from → moved to
- Confirm command:
  cd service/functions/Product/WebApp_Product_BackEnd/tests
  python run_all_tests.py
  works.

Important:
Do NOT create new folders beyond the canonical set above.
Do NOT leave both performance/ and performance_tests/ (only keep performance_tests/).
Do NOT leave both integrations/ and integration_tests/ (only keep integration_tests/).

