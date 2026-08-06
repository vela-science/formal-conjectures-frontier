#!/usr/bin/env python3
"""Generate ``sources.lock.json`` from ``sources.yaml``.

The lock records the exact content root of every source this Frontier acquires,
so accepted state is traceable to fixed bytes rather than to a floating `main`
or to whatever a publisher happens to serve today. Run it from the repository
root:

    python3 scripts/write_sources_lock.py

The output shape is the one the Erdős Frontier's lock already uses, so a single
reader consumes every Frontier's lock. This file is byte-identical across the
Frontiers that carry it; fix a bug once and copy it, rather than letting four
acquisition runs drift apart.

The rule this file exists to enforce: **every hash here is computed from bytes
this script actually fetched or read.** A declared hash is never copied through
from ``sources.yaml``. Where a source declares one, the declaration is treated
as an assertion to check, and a mismatch fails the run rather than being
retained under the same commit. Where no content hash can be computed at all,
the entry says so in ``unlocked`` and gives the reason. A hash nobody computed
is worse than no hash at all, and a source silently dropped is worse still.

Every entry therefore carries exactly one of:

  ``sha256``       a content root computed here from the bytes named by
                   ``url`` or ``path``;
  ``exact_roots``  per-file content roots computed here, for a repository
                   pinned at a commit whose individual files are the retained
                   evidence;
  ``unlocked``     a sentence saying why no content hash exists for this entry.

``error`` marks a source that should have been lockable and was not. It is
written into the lock so the gap is visible, and the run then exits non-zero.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not a data problem
    sys.exit("PyYAML is required: pip install pyyaml")

class Loader(yaml.SafeLoader):
    """SafeLoader that leaves timestamps as the strings they were written as.

    YAML resolves an unquoted `2026-08-05T21:22:46Z` to a datetime, and a
    datetime round-tripped through JSON comes back out as `...+00:00`. That is
    a different string from the one the source declared, and a lock that
    silently reformats a declared value is a lock a reader cannot diff against
    its source.
    """


Loader.add_constructor(
    "tag:yaml.org,2002:timestamp", lambda loader, node: loader.construct_scalar(node)
)

UA = {"User-Agent": "vela-frontier-sources-lock"}
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
TIMEOUT = 90

# Locators and repository identity are copied through to the lock verbatim.
# They are recorded outside the fetch branches on purpose: a routine refresh
# that cannot reach the network must still leave the inventory provenance
# intact rather than quietly narrowing the lock to whatever it could reach.
PASSTHROUGH = (
    "repo",
    "ref",
    "path",
    "paths",
    "commit",
    "tree",
    "home",
    "homepage",
    "pages_commit",
    "pages_commit_resolved",
)


def fetch(url: str, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def github_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def is_repository_landing_page(url: str, repo: str | None) -> bool:
    """True when `url` is a repository's front page rather than a locator for
    bytes. Fetching one yields rendered HTML, and recording a hash of that HTML
    as the content root would be a false pin that looks exactly like a real one.
    """
    if not repo:
        return False
    return url.rstrip("/") in (
        f"https://github.com/{repo}",
        f"http://github.com/{repo}",
    )


def resolve_commit(repo: str, rev: str) -> tuple[str, str]:
    """Return the (commit, tree) GitHub reports for `rev`, read from the API
    response rather than from what sources.yaml claims they are.
    """
    payload = json.loads(
        fetch(f"https://api.github.com/repos/{repo}/commits/{rev}", github_headers())
    )
    return payload["sha"], payload["commit"]["tree"]["sha"]


def lock_exact_roots(entry: dict, spec: dict, problems: list[str], name: str) -> None:
    """Lock a repository pinned at a commit by recomputing the content root of
    each file the acquisition treats as exact. The declared hashes in
    sources.yaml are assertions to check, never values to copy.
    """
    repo, commit = spec["repo"], spec["commit"]
    observed_commit, observed_tree = resolve_commit(repo, commit)
    if observed_commit != commit:
        problems.append(
            f"{name}: sources.yaml pins commit {commit}, but GitHub resolved it to {observed_commit}"
        )
    entry["commit"] = observed_commit
    if spec.get("tree") and spec["tree"] != observed_tree:
        problems.append(
            f"{name}: sources.yaml declares tree {spec['tree']}, "
            f"but commit {observed_commit} has tree {observed_tree}"
        )
    entry["tree"] = observed_tree

    roots: dict[str, dict] = {}
    for key, declared in sorted(spec["exact_roots"].items()):
        path = declared["path"]
        url = f"https://raw.githubusercontent.com/{repo}/{observed_commit}/{path}"
        computed = sha256(fetch(url))
        roots[key] = {"path": path, "url": url, "sha256": computed}
        if declared.get("sha256") and declared["sha256"] != computed:
            problems.append(
                f"{name}/{key}: sources.yaml declares {declared['sha256']} for {path}, "
                f"but {observed_commit} serves {computed}"
            )
    entry["exact_roots"] = roots


def lock_entry(root: Path, name: str, spec: dict, problems: list[str]) -> dict:
    entry: dict = {"kind": spec.get("kind")}
    for field in PASSTHROUGH:
        if spec.get(field) is not None:
            entry[field] = spec[field]
    url = spec.get("url")
    if url is not None:
        entry["url"] = url

    # Cited, not acquired. Another Frontier holds the bytes; its url is a
    # landing page, so the declared commit and tree are the whole of the pin.
    if spec.get("acquired_by"):
        entry["acquired_by"] = spec["acquired_by"]
        entry["unlocked"] = (
            f"cited, not acquired: the bytes are acquired by the {spec['acquired_by']} "
            "frontier and are not retained here, so the pin is the declared commit and tree"
        )
        return entry

    # Consulted as a reference. No bytes are retained, so there is nothing to
    # hash, and fetching the page to manufacture a root would misrepresent a
    # consultation as an acquisition.
    if spec.get("kind") == "reference_only":
        entry["unlocked"] = (
            "reference only: the frontier records that this was consulted, not what "
            "it said, so no bytes are retained and there is no content root to compute"
        )
        return entry

    try:
        if spec.get("exact_roots"):
            lock_exact_roots(entry, spec, problems, name)
            return entry

        if spec.get("path") is not None:
            target = root / spec["path"]
            if target.is_file():
                entry["sha256"] = sha256(target.read_bytes())
                return entry
            if url is None:
                entry["error"] = f"declared path {spec['path']} does not exist in this repository"
                problems.append(f"{name}: {entry['error']}")
                return entry

        if url is not None:
            if is_repository_landing_page(url, spec.get("repo")):
                observed_commit, observed_tree = resolve_commit(spec["repo"], spec["commit"])
                if observed_commit != spec["commit"]:
                    problems.append(
                        f"{name}: sources.yaml pins commit {spec['commit']}, "
                        f"but GitHub resolved it to {observed_commit}"
                    )
                if spec.get("tree") and spec["tree"] != observed_tree:
                    problems.append(
                        f"{name}: sources.yaml declares tree {spec['tree']}, "
                        f"but commit {observed_commit} has tree {observed_tree}"
                    )
                entry["commit"], entry["tree"] = observed_commit, observed_tree
                entry["unlocked"] = (
                    "no content locator: the url is the repository landing page, not bytes, "
                    "and this frontier retains no snapshot. The pin is the commit and tree "
                    "above, both read from the GitHub API at generation time"
                )
                return entry

            data = fetch(url)
            entry["sha256"] = sha256(data)
            if spec.get("repo") and spec.get("ref"):
                observed_commit, observed_tree = resolve_commit(spec["repo"], spec["ref"])
                entry["commit"], entry["tree"] = observed_commit, observed_tree
            return entry

        entry["unlocked"] = "no url and no in-repository path: nothing to compute a content root from"
        return entry

    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as exc:
        entry["error"] = f"{type(exc).__name__}: {exc}"
        problems.append(f"{name}: could not lock ({entry['error']})")
        return entry


def write_sources_lock(root: str | Path = ".") -> dict:
    root = Path(root)
    registry = (yaml.load((root / "sources.yaml").read_text(), Loader) or {}).get("sources", {})
    if not registry:
        sys.exit(f"{root / 'sources.yaml'} declares no sources")

    problems: list[str] = []
    locked = {name: lock_entry(root, name, spec, problems) for name, spec in registry.items()}

    stamp = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    payload = {"generated_at": stamp, "sources": locked}
    # Written even when the run failed, so the gap is on the record rather than
    # only in a terminal that has since scrolled away.
    (root / "sources.lock.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    if problems:
        raise SystemExit(
            "sources.lock.json written, but the run FAILED:\n  "
            + "\n  ".join(problems)
            + "\nNothing above was guessed at. Fix the source or the declaration; "
            "do not hand-edit the lock."
        )
    return payload


if __name__ == "__main__":
    result = write_sources_lock(sys.argv[1] if len(sys.argv) > 1 else ".")
    for name, entry in sorted(result["sources"].items()):
        if "sha256" in entry:
            state = entry["sha256"]
        elif "exact_roots" in entry:
            state = f"{len(entry['exact_roots'])} exact roots at {entry['commit'][:12]}"
        else:
            state = "unlocked: " + entry["unlocked"].split(":")[0]
        print(f"  {name:>28}  {state}")
    print(f"wrote sources.lock.json at {result['generated_at']}")
