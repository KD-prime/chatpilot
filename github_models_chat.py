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

Create OR update the MASTER README.md at:
service/functions/Product/WebApp_Product_BackEnd/README.md

Intent:
This is the “front door” documentation for the entire WebApp_Product_BackEnd. It must be high-quality, beginner-friendly, and accurate to what exists in the workspace.

Core Rules (non-negotiable):
- Do NOT invent: files, folders, endpoints/routes, triggers, env vars, services, cloud resources, or technologies.
- Only describe what you can confirm from code/config/docs in the repo.
- If something cannot be confirmed, write: “Not found in repo”.
- Keep any existing useful content, but restructure and polish it into the template below (do not delete valuable info).

Process (do this in order):
1) Scan the folder tree under service/functions/Product/WebApp_Product_BackEnd
2) Identify major modules/subsystems based on real directories and key files
3) Read any existing README(s) and relevant config (pyproject.toml, requirements.txt, Dockerfile, host.json, function.json, yaml/yml, json) to infer how it runs
4) Then write/update the master README

Master README Template (must include all sections):

# WebApp Product Backend

## 1) What This Is
Explain in plain English:
- What the backend is responsible for
- Typical consumers (e.g., UI, gateway, internal services) — keep generic unless the repo explicitly names them
- What types of capabilities it provides (based on real modules found)

## 2) How It’s Organized (Folder Map)
- Provide a concise map of the major subfolders directly under WebApp_Product_BackEnd
- For each subfolder:
  - 1–2 sentence description (based on actual files)
  - A link to that folder’s README.md (relative path)
- If some folders don’t have code/config and are not important, briefly mention they exist but keep focus on main ones

## 3) High-Level Architecture (ASCII Diagram Only)
- Include a terminal-style ASCII diagram inside a Markdown code block (```).
- Use box-style ASCII (+---+ and |   |) and arrows (--> or <-->).
- Show a generic layered flow:
  Client/UI --> Gateway/Edge --> Backend Modules/Services --> Data Stores/External Integrations
- ONLY name specific components if the repo explicitly references them (in code/config/docs).
- Ensure alignment is clean and readable (monospace spacing).
- Include a small legend if helpful.

## 4) Key Runtime Flows (Generic, Accurate)
Describe 2–4 flows at a conceptual level without assuming route paths, e.g.:
- “A client request enters the gateway, is validated, then forwarded to module X”
- “A backend module calls an external integration, then stores results”
If actual routes or triggers are explicitly present in code/config, you may include them, otherwise keep generic.

## 5) Local Development
Only include what can be confirmed from repo artifacts:
- Prerequisites (runtime versions if specified)
- Install dependencies
- Run locally (how to start the service(s) / function host / app)
- Testing and linting commands if present
- How to validate it works (health check / sample request) ONLY if present in code/docs; otherwise provide a generic validation approach and label it as such

## 6) Configuration and Environment Variables
- Extract env vars ONLY from code/config (don’t guess).
- Group them by category:
  - Auth / Identity
  - Data / Storage
  - External Integrations
  - Observability / Logging
  - App Settings
- For each env var, include:
  - name
  - what it controls (from usage context)
  - where it is referenced (file path)
If none are found, say “Not found in repo”.

## 7) Deployment (High Level, Repo-Based)
- Describe how it is deployed ONLY based on what the repo contains (infra folder, pipelines, scripts, platform hints).
- Link to the relevant deployment files/docs (relative paths).
- If unclear, say “Not found in repo” and list what would be needed to confirm.

## 8) Where to Look Next
- Provide a short “next links” list pointing to the most important subfolder READMEs and any onboarding docs.

Quality Bar:
- Write like an internal engineering README: clear headings, tight wording, no fluff.
- Prefer bullet points and short paragraphs.
- Use consistent terminology.
- Avoid over-claiming. If uncertain, state it explicitly.

Deliverables:
- Update/create service/functions/Product/WebApp_Product_BackEnd/README.md
- After writing, output a short summary:
  - What sections were added/updated
  - Which folders were linked
  - Any “Not found in repo” gaps discovered

