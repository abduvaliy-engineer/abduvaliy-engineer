"""Live GitHub data for the profile. Standard library only.

Every number on the cards comes from here. Anything that fails raises, so a
bad API day keeps yesterday's drawings instead of publishing broken ones.
"""
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com/"


def token():
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    try:  # local runs: borrow the gh CLI login
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


class GitHub:
    def __init__(self, tok=None):
        self.tok = tok
        self.calls = 0

    def get(self, path, **params):
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "abduvaliy-profile",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if self.tok:
            headers["Authorization"] = f"Bearer {self.tok}"
        for attempt in range(3):
            try:
                self.calls += 1
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429, 500, 502, 503) and attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise RuntimeError(f"GitHub API {e.code} for {path}") from e
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 2:
                    time.sleep(3 * (attempt + 1))
                    continue
                raise RuntimeError(f"GitHub API unreachable for {path}") from e
        raise RuntimeError(f"GitHub API kept failing for {path}")


def repo_info(gh, repo):
    r = gh.get(f"repos/{repo}")
    return {"stars": r["stargazers_count"], "language": r["language"], "pushed_at": r["pushed_at"],
            "size": r["size"], "private": r["private"]}


def pull(gh, repo, number):
    p = gh.get(f"repos/{repo}/pulls/{number}")
    return {"number": number, "title": p["title"], "additions": p["additions"],
            "deletions": p["deletions"], "merged_at": p["merged_at"], "url": p["html_url"]}


def merged_pulls(gh, repo, login):
    found = gh.get("search/issues", q=f"repo:{repo} author:{login} is:pr is:merged", per_page=100)
    pulls = [pull(gh, repo, item["number"]) for item in found["items"]]
    return sorted(pulls, key=lambda p: p["merged_at"] or "")


def collect(cfg, gh):
    """Everything live the drawings need, keyed by project/contribution id."""
    live = {"projects": {}, "contributions": {}}
    for p in cfg["projects"]:
        if p.get("repo"):
            live["projects"][p["id"]] = repo_info(gh, p["repo"])
    for c in cfg["contributions"]:
        if not c.get("repo"):
            continue
        info = repo_info(gh, c["repo"])
        if c.get("pr"):
            info["pulls"] = [pull(gh, c["repo"], c["pr"])]
        else:
            info["pulls"] = merged_pulls(gh, c["repo"], cfg["login"])
        if not info["pulls"]:
            raise RuntimeError(f"no merged pull requests found in {c['repo']}")
        live["contributions"][c["id"]] = info
    return live


def offline(cfg):
    """The snapshot stored in profile.json, for tests and previews without network."""
    return {"projects": {p["id"]: p["snapshot"] for p in cfg["projects"] if p.get("repo")},
            "contributions": {c["id"]: c["snapshot"] for c in cfg["contributions"] if c.get("repo")}}
