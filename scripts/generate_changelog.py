from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?: (?P<subject>.+)$"
)
SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactoring",
    "test": "Tests",
    "ci": "CI",
    "build": "Build",
    "docs": "Documentation",
    "style": "Style",
    "chore": "Chores",
}
SECTION_ORDER = ["feat", "fix", "perf", "refactor", "test", "ci", "build", "docs", "style", "chore"]


@dataclass(frozen=True)
class Commit:
    sha: str
    subject: str
    type: str
    scope: str
    description: str
    breaking: bool


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _latest_tag() -> str | None:
    output = _git("tag", "--sort=-creatordate", check=False)
    return output.splitlines()[0] if output else None


def _commit_range(since: str | None) -> str:
    return f"{since}..HEAD" if since else "HEAD"


def _parse_commit(line: str) -> Commit | None:
    if not line:
        return None
    sha, _, subject = line.partition(" ")
    match = CONVENTIONAL_RE.match(subject)
    if match is None:
        return Commit(
            sha=sha,
            subject=subject,
            type="chore",
            scope="",
            description=subject,
            breaking=False,
        )
    return Commit(
        sha=sha,
        subject=subject,
        type=match.group("type"),
        scope=match.group("scope") or "",
        description=match.group("subject"),
        breaking=bool(match.group("breaking")),
    )


def _commits(since: str | None) -> list[Commit]:
    output = _git("log", "--pretty=format:%h %s", _commit_range(since))
    commits: list[Commit] = []
    for line in output.splitlines():
        commit = _parse_commit(line)
        if commit is not None:
            commits.append(commit)
    return commits


def _format_entry(commit: Commit) -> str:
    scope = f"**{commit.scope}:** " if commit.scope else ""
    breaking = " **BREAKING**" if commit.breaking else ""
    return f"- {scope}{commit.description} ({commit.sha}){breaking}"


def render_changelog(version: str, since: str | None, commits: list[Commit]) -> str:
    today = datetime.now(UTC).date().isoformat()
    base = since or "initial history"
    lines = [f"## {version} - {today}", "", f"_Changes since {base}_", ""]

    grouped: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        grouped[commit.type].append(commit)

    for section_type in SECTION_ORDER:
        items = grouped.pop(section_type, [])
        if not items:
            continue
        lines.append(f"### {SECTION_TITLES[section_type]}")
        lines.extend(_format_entry(commit) for commit in items)
        lines.append("")

    for section_type in sorted(grouped):
        items = grouped[section_type]
        lines.append(f"### {SECTION_TITLES.get(section_type, section_type.title())}")
        lines.extend(_format_entry(commit) for commit in items)
        lines.append("")

    if len(lines) == 4:
        lines.append("- No changes.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a changelog preview from git history.")
    parser.add_argument("--version", default="Unreleased", help="version label for the heading")
    parser.add_argument("--since", help="git tag or revision to start after")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if no commits are available for the selected range",
    )
    args = parser.parse_args()

    since = args.since if args.since is not None else _latest_tag()
    commits = _commits(since)
    if args.check and not commits:
        print("no commits found for changelog range", file=sys.stderr)
        return 1

    print(render_changelog(args.version, since, commits), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
