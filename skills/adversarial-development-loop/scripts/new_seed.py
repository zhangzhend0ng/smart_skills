#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scaffold a new meta-bench seed (write mode; the ONLY write path in the tooling).

Usage:
  python scripts/new_seed.py <domain> <name> <flaw_type> [--severity s]

Creates assets/meta-bench/seeds/<domain>/<NN>-<name>/ with:
  - fixture.py: stub docstring (author fills in the seeded flaw)
  - manifest.json: frozen schema; expected_keywords=[] and a placeholder
    description — SEMANTIC DISTILLATION (flaw classification, keywords,
    description) is intentionally left to human/agent, NOT automated
    (iter 119 boundary, see framework-manual.md §7).
    An unfinished seed FAILS `--verify` loudly: that is the intended gate
    ("seed not finished = not allowed through").

Safety:
  - domain/name whitelisted to [a-z0-9-]+ (no underscore — keeps --score-all
    report-name flattening injective, prevents path traversal; adversarial M1)
  - never overwrites an existing seed dir; rejects duplicate name in domain
  - NN = max existing numeric prefix in domain + 1 (>= 2 digits)

Severity default map (covers ALL 10 VALID_FLAW_TYPES; assertion guards future
extensions — adversarial B1):
  blocker: false-perfect, false-worst, degenerate-zero
  major:   magic-threshold, dead-branch, config-hygiene, stale-doc,
           symmetry, single-layer-fix
  minor:   none
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS_ROOT = os.path.join(SKILL_ROOT, "assets", "meta-bench", "seeds")

VALID_FLAW_TYPES = (
    "false-perfect", "false-worst", "degenerate-zero", "magic-threshold",
    "dead-branch", "config-hygiene", "stale-doc", "symmetry",
    "single-layer-fix", "none",
)
VALID_SEVERITIES = ("blocker", "major", "minor")
DEFAULT_SEVERITY = {
    "false-perfect": "blocker",
    "false-worst": "blocker",
    "degenerate-zero": "blocker",
    "magic-threshold": "major",
    "dead-branch": "major",
    "config-hygiene": "major",
    "stale-doc": "major",
    "symmetry": "major",
    "single-layer-fix": "major",
    "none": "minor",
}
# B1:映射表键集 == 枚举集(防未来加枚举漏映射)
assert set(DEFAULT_SEVERITY) == set(VALID_FLAW_TYPES), "severity map must cover all flaw types"

NAME_RE = re.compile(r"^[a-z0-9-]+$")
ENTRY_RE = re.compile(r"^([0-9]{2,})-(.+)$")

FIXTURE_TEMPLATE = '''"""Fixture: {flaw_type} ({name})。待完成——由人/agent 在此填入种子缺陷。

模板说明:
1. 写一个最小、自包含、可读(<60 行)的领域代码片段,含一个种子缺陷
   (或干净反例用 flaw_type=none)。
2. 语义蒸馏(缺陷归类/关键词/描述)属人/agent 职责,不得自动化(iter 119 边界)。
3. 完成后跑 python scripts/run_meta_bench.py --verify——未完成种子会响亮 FAIL。
"""
'''


def next_entry(domain_dir: str, name: str) -> str | None:
    """Return '<NN>-<name>' for the new seed, or None if name already exists."""
    existing = [e for e in os.listdir(domain_dir) if os.path.isdir(os.path.join(domain_dir, e))]
    for e in existing:
        m = ENTRY_RE.match(e)
        if m and m.group(2) == name:
            return None  # 同 domain 下重名
    nums = [int(m.group(1)) for e in existing if (m := ENTRY_RE.match(e))]
    nn = (max(nums) + 1) if nums else 1
    return "%02d-%s" % (nn, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new meta-bench seed (write mode).")
    parser.add_argument("domain", help="seed domain, e.g. scoring-detection ([a-z0-9-]+)")
    parser.add_argument("name", help="seed name, e.g. false-perfect ([a-z0-9-]+)")
    parser.add_argument("flaw_type", choices=VALID_FLAW_TYPES)
    parser.add_argument("--severity", choices=VALID_SEVERITIES,
                        help="override default severity (defaults per flaw_type, see header)")
    args = parser.parse_args(argv)

    for label, value in (("domain", args.domain), ("name", args.name)):
        if not NAME_RE.match(value):
            sys.exit("invalid %s %r: must match [a-z0-9-]+ (no underscore)" % (label, value))

    domain_dir = os.path.join(SEEDS_ROOT, args.domain)
    os.makedirs(domain_dir, exist_ok=True)
    entry = next_entry(domain_dir, args.name)
    if entry is None:
        sys.exit("seed '%s/%s' already exists — refusing to overwrite"
                 % (args.domain, args.name))

    seed_dir = os.path.join(domain_dir, entry)
    os.makedirs(seed_dir)
    seed_id = "%s/%s" % (args.domain, entry)

    fixture_path = os.path.join(seed_dir, "fixture.py")
    with open(fixture_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(FIXTURE_TEMPLATE.format(flaw_type=args.flaw_type, name=args.name))

    manifest = {
        "id": seed_id,
        "flaw_type": args.flaw_type,
        "expected_severity": args.severity or DEFAULT_SEVERITY[args.flaw_type],
        "expected_keywords": [],  # 语义蒸馏占位:须人/agent 填写(iter 119 边界)
        "description": "TODO: 语义蒸馏占位——缺陷说明由人/agent 填写(未完成种子 --verify 会响亮 FAIL)",
    }
    manifest_path = os.path.join(seed_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print("created %s" % seed_id)
    print("NOTE: expected_keywords/description 是占位——语义蒸馏(缺陷归类/关键词/描述)须人/agent 完成;")
    print("      run_meta_bench.py --verify 对未完成种子会 FAIL,这是有意的响亮门。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
