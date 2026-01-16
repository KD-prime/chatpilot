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

Repo scope (Frontend):
service/functions/Product/WebApp_Product_FrontEnd

Goal:
Repeat the SAME enterprise-grade approach we used for backend, but for the FRONTEND:
- category-first test structure (no random “tests/api” style top-level folders)
- filled READMEs (no blanks)
- run-all script runnable via: python run_all_tests.py (executed from the tests/ folder)
- scan the whole frontend codebase to identify missing high-value tests (based on real code)

Canonical structure (ONLY these top-level folders under the frontend tests directory):
service/functions/Product/WebApp_Product_FrontEnd/tests/
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
- tests/unit_tests/components/
- tests/unit_tests/utils/
- tests/functional_tests/pages/
- tests/functional_tests/routes/
- tests/integration_tests/api_clients/
But do NOT create extra top-level test folders.

Hard Rules:
- Do NOT invent routes, endpoints, env vars, features, components, or services.
- Only reference what exists in the workspace (code/config).
- If something cannot be confirmed, write exactly: “Not found in repo”.
- NO EMPTY README.md files (must contain useful content even if folder is empty).
- Do NOT break existing frontend build or test setup.
- Detect the actual test runner(s) used from package.json (vitest/jest/cypress/playwright/etc.).
  Do NOT assume tools that aren’t present.
- You MAY move/rename tests within the frontend tests/ folder ONLY if needed to enforce canonical structure,
  but do NOT delete test content; merge useful README content if moving.

Process (must follow in order):
1) Scan the frontend repo to detect:
   - framework/tooling (React/Vite/etc.)
   - routing approach (react-router, etc.)
   - key pages/screens/components (real file paths)
   - API client modules/hooks/services (real paths)
   - env/config usage (e.g., import.meta.env)
   - testing tools from package.json scripts + devDependencies
Create:
- service/functions/Product/WebApp_Product_FrontEnd/TEST_SURFACE_MAP_FRONTEND.md
Include tables:
- Screens/pages and their source file paths
- Reusable components and their paths
- API client/service modules and their paths
- Config/env keys referenced (ONLY if explicitly referenced in code)

2) Scan existing tests (if any exist) and record conventions:
- how tests are written
- how mocking is done (msw? vi.mock? jest.mock?)
Create:
- service/functions/Product/WebApp_Product_FrontEnd/TEST_GAP_REPORT_FRONTEND.md
Include a “Current Test Inventory” table:
test file | category | what it validates | source modules

3) Create/Update canonical tests/ structure
- Ensure category folders exist:
  unit_tests/, functional_tests/, integration_tests/, regression_tests/, performance_tests/
- Create/update README.md in each folder (no blanks).
Each category README must include:
  Purpose, What belongs here in THIS repo, What exists now (list real tests),
  How to run subset (only if confirmable; else “Proposed”), Where to add new tests.

4) Create/Update tests/README.md (index)
Must include:
- Overview + category-first policy
- Structure diagram (simple ASCII)
- How to install deps (based on detected package manager)
- How to run all tests using: python run_all_tests.py
- How to run subsets using run_all_tests.py --path ...
- Conventions in this repo (naming, where tests go, mocking strategy) based on real code/tests.

5) Create tests/run_all_tests.py (python wrapper that runs JS tests)
Create:
service/functions/Product/WebApp_Product_FrontEnd/tests/run_all_tests.py

Hard Requirements:
- Running from the tests directory MUST work:
  cd service/functions/Product/WebApp_Product_FrontEnd/tests
  python run_all_tests.py

- Detect package manager via lockfile:
  pnpm-lock.yaml -> pnpm
  yarn.lock -> yarn
  package-lock.json -> npm
  If none found, default to npm but print a warning.

- Detect test command from package.json scripts in this priority:
  1) test
  2) test:ci
  3) test:unit
  4) vitest / jest / playwright / cypress scripts if present
If none exist, print “Not found in repo” and exit 2 (do NOT invent tooling).

- Support CLI flags (argparse):
  --path <subpath>   (run subset if runner supports path filtering; if not supported, print message and run full suite)
  --watch            (only if supported)
  --ci               (use CI-friendly script if available)
  --verbose

- Debug-friendly output:
  - frontend root detected
  - package manager detected
  - chosen test script/command
  - PASS/FAIL + exit code

6) Create tests/requirements.txt and tests/dev_requirements.txt (documentation only)
Rules:
- Do NOT pin JS deps here.
- These files should be setup guidance and reference package.json/lockfile as source of truth.
requirements.txt should include:
- node version info ONLY if repo specifies it (e.g., .nvmrc, engines)
dev_requirements.txt should include:
- install command for detected package manager
- test command(s) detected
If not confirmable, write “Not found in repo”.

7) Identify and implement missing high-value tests (only confirmable)
- Add 5–10 high-value tests maximum using the repo’s actual runner and libraries.
- Prioritize:
  - critical UI components rendering and validation
  - error/empty states
  - routing/guard logic (if present)
  - API client/hooks behavior with network mocked using existing approach
- Place new tests under the correct category folder.

Output (must provide):
1) Final frontend tests/ tree
2) Summary table: created/updated/moved files
3) Current Test Inventory table
4) Top 10 test gaps (from TEST_GAP_REPORT_FRONTEND.md)
5) Commands:
   cd service/functions/Product/WebApp_Product_FrontEnd/tests
   python run_all_tests.py
   python run_all_tests.py --path unit_tests
   python run_all_tests.py --path functional_tests
