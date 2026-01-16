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
Check whether we have implemented “#12 Traceability: Functional-to-Technical Requirement Mapping & Test Coverage”
AND verify whether the repo already contains tests aligned to the specific “test requirements” below.

IMPORTANT:
Do NOT reference any images. The requirements are written below.

========================
#12 Traceability Table Requirements (must be verifiable from repo)
A traceability table (Markdown) exists (preferably in TRACEABILITY.md) mapping:

| Functional Requirement | Technical Requirement (with source file paths) | Unit Test(s) | Integration Test(s) | Performance Test(s) | Notes/Gaps |

Rules:
- Functional Requirement must be sourced from docs OR written as:
  “Inferred from code (confirm with PO/BA)” and cite source file paths.
- Technical Requirement must cite real file paths (routes/services/integrations/config).
- Tests must cite real test file paths that exist.
- If a test type does not exist, write exactly: “Not found in repo”.

========================
Specific “Test Requirements” to check for (from the template)

Functional Requirements:
1) RAG — Ability to retrieve relevant documents and generate grounded responses for user queries.
2) GraphRAG — Ability to traverse knowledge graphs and retrieve connected entities for context-rich generation.
3) SAM (if applicable) — treat as a functional requirement only if there is supporting code in repo; otherwise “Not found in repo”.

Technical Requirements:
1) Implement vector-based similarity search and LLM prompt engineering for factual generation.
2) Implement graph traversal algorithms, entity linking, and hybrid retrieval combining graph and embeddings.
3) For SAM: only if code exists; otherwise “Not found in repo”.

Unit Test Requirements (what to look for in tests):
U1) Validate embedding generation.
U2) Validate vector store indexing and retrieval precision for sample queries.
U3) Validate graph node/edge creation.
U4) Validate graph traversal logic and entity extraction accuracy.

Integration Test Requirements (what to look for in tests):
I1) Test end-to-end flow from query → retrieval → LLM generation → response formatting.
I2) Test combined flow of graph traversal + vector retrieval → context building → generation.

Performance Test Requirements (what to look for in tests):
P1) Measure latency and throughput for high-volume queries, ensuring response times meet SLOs.
P2) Stress test graph traversal: large-scale graphs and nested retrieval scenarios for scalability.

========================
Process (must do in this order)

1) Scan for traceability artifacts:
- TRACEABILITY.md
- TESTING.md
- tests/README.md
- any docs mentioning traceability/coverage/ALM/JIRA

2) Scan codebase to determine if RAG / GraphRAG / SAM are actually present:
- look for retrieval modules, embeddings usage, vector DB integrations, graph traversal code, entity extraction code
- if absent, mark “Not found in repo”

3) Scan tests folder to confirm which of U1–U4, I1–I2, P1–P2 are already covered.
- only count coverage if a test file explicitly asserts behavior related to that requirement

OUTPUT REQUIRED (must be explicit):
A) Does a #12 traceability table exist? If yes: file path and line/section pointer.
B) For EACH functional/technical requirement above (RAG, GraphRAG, SAM):
   - Status: Covered / Partially covered / Not found in repo
   - Supporting technical source file paths (real paths) OR “Not found in repo”
C) For EACH test requirement U1–U4, I1–I2, P1–P2:
   - Status: Covered / Not covered / Not found in repo
   - Existing test file paths that cover it (real paths) OR “Not found in repo”
D) A short gap list: what is missing for #12 and/or missing tests aligned to U/I/P requirements.

Rules:
- Do NOT invent anything.
- If something cannot be confirmed from repo, write exactly: “Not found in repo”.
- If you infer a mapping from structure, label it:
  “Inferred from code (confirm with PO/BA)” and cite the relevant source file paths.
