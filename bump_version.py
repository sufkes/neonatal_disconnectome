#!/usr/bin/env python3
"""
bump_version.py

Bumps the version in lib/constants.py, commits the change, and creates an
annotated git tag — all in one step.

Usage:
  python bump_version.py major          # 1.2.3 → 2.0.0
  python bump_version.py minor          # 1.2.3 → 1.3.0
  python bump_version.py patch          # 1.2.3 → 1.2.4
  python bump_version.py 2.1.0          # set exact version

Options:
  --dry-run   Show what would happen without making any changes
  --no-tag    Update the file and commit but skip creating the git tag

After running this script, push the tag to trigger the CI build:
  git push origin --tags
"""

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

CONSTANTS_FILE = Path("lib/constants.py")

VERSION_RE = re.compile(r'^(__version__\s*=\s*")[^"]*(")', re.MULTILINE)
DATE_RE = re.compile(r'^(__build_date__\s*=\s*")[^"]*(")', re.MULTILINE)


# ── Helpers ──────────────────────────────────────────────────────────────────


def run(cmd: list[str], check=True) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running {' '.join(cmd)}:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def current_version() -> str:
    content = CONSTANTS_FILE.read_text()
    m = VERSION_RE.search(content)
    if not m:
        print(f"Error: could not find __version__ in {CONSTANTS_FILE}", file=sys.stderr)
        sys.exit(1)
    return VERSION_RE.search(content).group(0).split('"')[1]


def bump(version: str, part: str) -> str:
    try:
        major, minor, patch = map(int, version.split("."))
    except ValueError:
        print(
            f"Error: current version '{version}' is not in MAJOR.MINOR.PATCH format.",
            file=sys.stderr,
        )
        sys.exit(1)

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        # Treated as an exact version string
        if not re.match(r"^\d+\.\d+\.\d+$", part):
            print(
                f"Error: '{part}' is not a valid version (expected MAJOR.MINOR.PATCH "
                "or one of: major, minor, patch).",
                file=sys.stderr,
            )
            sys.exit(1)
        return part


def update_constants(new_version: str, dry_run: bool) -> None:
    content = CONSTANTS_FILE.read_text()
    today = date.today().isoformat()

    new_content = VERSION_RE.sub(
        lambda m: m.group(1) + new_version + m.group(2), content
    )
    new_content = DATE_RE.sub(lambda m: m.group(1) + today + m.group(2), new_content)

    if new_content == content:
        print(
            "Warning: file content unchanged — version may already be set.",
            file=sys.stderr,
        )

    if dry_run:
        print(f"[dry-run] Would write to {CONSTANTS_FILE}:")
        for line in new_content.splitlines():
            if "__version__" in line or "__build_date__" in line:
                print(f"  {line}")
    else:
        CONSTANTS_FILE.write_text(new_content)
        print(f"Updated {CONSTANTS_FILE}")


def git_commit_and_tag(new_version: str, dry_run: bool, no_tag: bool) -> None:
    tag = f"v{new_version}"

    # Check for uncommitted changes other than constants.py
    dirty = run(["git", "status", "--porcelain"], check=False)
    other_dirty = [l for l in dirty.splitlines() if CONSTANTS_FILE.name not in l]
    if other_dirty:
        print(
            "Warning: you have other uncommitted changes. Commit or stash them before "
            "bumping the version to keep the release commit clean.",
            file=sys.stderr,
        )

    if dry_run:
        print(f"[dry-run] Would run: git add {CONSTANTS_FILE}")
        print(
            f'[dry-run] Would run: git commit -m "chore: bump version to {new_version}"'
        )
        if not no_tag:
            print(f'[dry-run] Would run: git tag -a {tag} -m "Release {tag}"')
        return

    run(["git", "add", str(CONSTANTS_FILE)])
    run(["git", "commit", "-m", f"chore: bump version to {new_version}"])
    print(f"Committed version bump.")

    if not no_tag:
        run(["git", "tag", "-a", tag, "-m", f"Release {tag}"])
        print(f"Created tag {tag}.")
        print(f"\nTo trigger the CI build, push the tag:")
        print(f"  git push origin {tag}")
        print(f"  # or push everything at once:")
        print(f"  git push origin --follow-tags")


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Bump version in lib/constants.py and create a git tag.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "part",
        help="Version part to bump (major / minor / patch) or an exact version like 2.1.0.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making any changes.",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Update the file and commit but skip creating the git tag.",
    )
    args = parser.parse_args()

    if not CONSTANTS_FILE.exists():
        print(
            f"Error: {CONSTANTS_FILE} not found. Run this script from the project root.",
            file=sys.stderr,
        )
        sys.exit(1)

    old_version = current_version()
    new_version = bump(old_version, args.part)

    print(f"Bumping version:  {old_version}  →  {new_version}")
    if args.dry_run:
        print("(dry-run mode — no changes will be made)\n")

    update_constants(new_version, dry_run=args.dry_run)
    git_commit_and_tag(new_version, dry_run=args.dry_run, no_tag=args.no_tag)


if __name__ == "__main__":
    main()
