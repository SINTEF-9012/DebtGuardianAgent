"""
Minimal client for fetching refactoring targets from a CodeScene instance
(cloud or on-prem / Docker).

Typical local Docker URL: http://localhost:3003
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional


def _api_get(base_url: str, path: str, token: str) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def list_projects(base_url: str, token: str) -> list:
    """Return [{id, name}, …] for every project visible to the token."""
    return _api_get(base_url, "/api/v2/projects", token)


def _find_project_id(base_url: str, token: str,
                     project_id: Optional[int] = None,
                     project_name: Optional[str] = None) -> int:
    if project_id is not None:
        return project_id
    projects = list_projects(base_url, token)
    if project_name:
        for p in projects:
            if p.get("name", "").lower() == project_name.lower():
                return p["id"]
        names = [p.get("name") for p in projects]
        raise ValueError(
            f"Project '{project_name}' not found. Available: {names}"
        )
    if len(projects) == 1:
        return projects[0]["id"]
    names = [f"{p['id']}: {p.get('name')}" for p in projects]
    raise ValueError(
        f"Multiple projects found — specify --codescene-project: {names}"
    )


def fetch_hotspot_file_paths(
    base_url: str,
    token: str,
    repo_root: str,
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
) -> List[str]:
    """
    Fetch prioritised hotspot file paths from CodeScene and resolve them
    against *repo_root* so they are absolute paths.

    CodeScene's hotspot API returns objects with a 'name' field that is
    the repo-relative file path.  We try both the v2 refactoring-targets
    endpoint and the v1 hotspots endpoint for compatibility.
    """
    pid = _find_project_id(base_url, token, project_id, project_name)

    # Try v2 refactoring targets first (prioritised list)
    try:
        data = _api_get(
            base_url,
            f"/api/v2/projects/{pid}/refactoring-targets",
            token,
        )
        entries = data if isinstance(data, list) else data.get("targets", data.get("entries", []))
    except urllib.error.HTTPError:
        # Fall back to v1 hotspots
        data = _api_get(
            base_url, f"/api/v1/projects/{pid}/analyses/latest/hotspots", token
        )
        entries = data if isinstance(data, list) else data.get("hotspots", [])

    repo = Path(repo_root)
    paths: List[str] = []
    for entry in entries:
        rel = entry.get("name") or entry.get("file") or entry.get("path", "")
        if not rel:
            continue
        full = repo / rel
        if full.exists():
            paths.append(str(full))
        else:
            # Keep the relative path; coordinator will skip missing files
            paths.append(str(full))

    return paths


def fetch_hotspots_to_file(
    base_url: str,
    token: str,
    repo_root: str,
    output_path: str,
    project_id: Optional[int] = None,
    project_name: Optional[str] = None,
) -> str:
    """Convenience: fetch hotspots and write one-per-line to *output_path*."""
    paths = fetch_hotspot_file_paths(
        base_url, token, repo_root, project_id, project_name
    )
    with open(output_path, "w") as f:
        f.write("\n".join(paths) + "\n")
    print(f"[CodeScene] Wrote {len(paths)} hotspot paths to {output_path}")
    return output_path
