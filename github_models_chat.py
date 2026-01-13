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
In the repo folder: service/functions/Product/WebApp_Product_BackEnd

Task:
Create OR update a README.md in every direct subfolder (and nested subfolders if they contain code).
If a README.md already exists, UPDATE it (do not delete useful content—improve/expand it).

Each README should include:

1) Purpose (plain English for a novice)
2) Key files (list actual filenames found in that folder, especially .py — do not guess)
3) How it runs (entrypoint, trigger type if applicable, and env vars referenced in code/config)
4) High-Level Architecture Diagram (ASCII ONLY — NOT Mermaid)
   - Put the diagram inside a Markdown code block (```).
   - Use box-style ASCII with +---+ and |   | formatting (terminal-style diagram).
   - Show arrows between components (--> or <-->).
   - Label components with REAL .py filenames when relevant (only if they exist in that folder).
   - Keep alignment clean and readable (monospace spacing).
   - ASCII diagram style must match a “terminal architecture diagram” with large grouped boxes:
     (Platform box at top, APIM big box containing Gateway Layer + downstream APIs,
      Frontend + External APIs boxes on the left).

5) Local dev + test steps (commands, how to run locally, how to validate it works)

Rules:
- Do NOT invent files, folders, env vars, endpoints, or triggers.
- If something is not found, explicitly write: "Not found in this folder".
- Start by scanning the folder tree under service/functions/Product/WebApp_Product_BackEnd
  and list which subfolders will get a README, then create/update the READMEs.

Output:
- After changes, provide a summary table: folder → README created/updated → key files detected.


# fetch catalog
models = ChatGithub.list_models()
print(f"GitHub currently hosts {len(models)} models.")
print("First five:", models[:5])
