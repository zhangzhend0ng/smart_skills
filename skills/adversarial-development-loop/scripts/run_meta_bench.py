#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Meta-benchmark runner for the adversarial-development-loop skill.

Smoke-tests whether a REFUTE report catches the seeded flaws in fixture code.
Read the framework contract in references/framework-manual.md before editing.

Modes (exactly one):
  --verify                   validate every seed's manifest.json + fixture.py
  --list                     list all seeds
  --score SEED_ID REPORT     score one REFUTE report file against one seed
  --score-all DIR            score every seed against report files in DIR
  --demo                     self-test the scoring logic (all seeds, pass/fail pairs)

Scoring (see framework-manual.md §3):
  defect seed PASS = concept-level hit on expected_keywords (case-insensitive
                     substring, i.e. synonyms authored into the manifest)
                     AND max severity in report >= expected_severity
  clean seed  PASS = no [blocker] and no [major] in report
  All seeds PASS  = this baseline passes.

--score-all DIR: report file per seed named <seed-id with '/' -> '_'>.md,
  e.g. scoring-detection/01-false-perfect -> DIR/scoring-detection_01-false-perfect.md.
  A seed without a report is reported as MISSING (baseline incomplete -> FAIL).
  --json prints a machine-readable aggregate (per-seed status: pass|fail|missing).

--demo: for EVERY seed, built-in pass/fail report pairs exercise all branches
  of score_report (hit+severity, severity-too-low, no-keyword-hit; clean benign,
  clean over-report). NOTE the circular-validation caveat: demo reports are
  authored by the same author as the manifests, so demo green only proves
  scorer<->manifest self-consistency, not skill effectiveness on real code.

Honest limitations (must not be overstated):
  - Seeds are toy-level smoke tests, not a measure of skill quality.
  - Manifests are authored by the same author as the skill -> circular
    validation: a green bench only proves REFUTE's detection consistency
    against labeled seeds, not that the skill works on real code.
  - Real calibration (manual REFUTE passes on real targets) is out of scope.

Requires: Python 3.8+ (`from __future__ import annotations`; stdlib only).
Exits nonzero on any failure. Write operations live in scripts/new_seed.py —
this runner stays read-only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS_ROOT = os.path.join(SKILL_ROOT, "assets", "meta-bench", "seeds")

REQUIRED_FIELDS = ("id", "flaw_type", "expected_severity", "expected_keywords", "description")
VALID_FLAW_TYPES = (
    "false-perfect", "false-worst", "degenerate-zero", "magic-threshold",
    "dead-branch", "config-hygiene", "stale-doc", "symmetry",
    "single-layer-fix", "none",
)
VALID_SEVERITIES = ("blocker", "major", "minor")
SEVERITY_ORDER = {"blocker": 3, "major": 2, "minor": 1, "none": 0}
CLEAN_SEVERITY_CAP = "minor"  # clean seeds: nothing above minor allowed

# 命名白名单(M1 修复):domain/name 仅 [a-z0-9-](无下划线,保证 --score-all
# 报告文件名扁平化单射、防路径穿越);NN >= 2 位数字
NAME_RE = re.compile(r"^[a-z0-9-]+$")
ENTRY_RE = re.compile(r"^([0-9]{2,})-(.+)$")

SEVERITY_PATTERN = re.compile(r"\[(blocker|major|minor)\]", re.IGNORECASE)


def report_filename(seed_id: str) -> str:
    """--score-all 报告文件名:seed_id 的 '/' -> '_'(见模块 docstring)。"""
    return seed_id.replace("/", "_") + ".md"


def find_manifests(root: str = SEEDS_ROOT) -> list[tuple[str, str]]:
    """Return list of (seed_id, manifest_path) found under root, sorted."""
    found: list[tuple[str, str]] = []
    if not os.path.isdir(root):
        return found
    for domain in sorted(os.listdir(root)):
        domain_dir = os.path.join(root, domain)
        if not os.path.isdir(domain_dir):
            continue
        for entry in sorted(os.listdir(domain_dir)):
            manifest_path = os.path.join(domain_dir, entry, "manifest.json")
            if os.path.isfile(manifest_path):
                # 用正斜杠拼接 id,保证与 manifest 中冻结的 id 格式一致
                # (os.path.join 在 Windows 产反斜杠,会与 manifest 失配)
                found.append(("%s/%s" % (domain, entry), manifest_path))
    return found


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def seed_dir_errors(domain: str, entry: str) -> list[str]:
    """seed 目录命名校验(白名单 + NN 前缀;对抗 M1)。"""
    errors: list[str] = []
    if not NAME_RE.match(domain):
        errors.append("domain %r must match [a-z0-9-]+" % domain)
    m = ENTRY_RE.match(entry)
    if not m:
        errors.append("seed dir %r must match <NN>-<name> with NN >= 2 digits" % entry)
    elif not NAME_RE.match(m.group(2)):
        errors.append("seed name %r must match [a-z0-9-]+" % m.group(2))
    return errors


def validate_manifest(manifest: dict, expected_id: str, domain: str, entry: str) -> list[str]:
    """Return list of error strings for one manifest (empty == valid)."""
    errors = seed_dir_errors(domain, entry)
    for field in REQUIRED_FIELDS:
        if field not in manifest:
            errors.append("missing required field: %s" % field)
    if "id" in manifest and manifest["id"] != expected_id:
        errors.append("id %r does not match directory %r" % (manifest["id"], expected_id))
    if "flaw_type" in manifest and manifest["flaw_type"] not in VALID_FLAW_TYPES:
        errors.append("invalid flaw_type %r" % manifest["flaw_type"])
    if "expected_severity" in manifest and manifest["expected_severity"] not in VALID_SEVERITIES:
        errors.append("invalid expected_severity %r" % manifest["expected_severity"])
    if "flaw_type" in manifest and manifest["flaw_type"] == "none":
        if manifest.get("expected_severity") != CLEAN_SEVERITY_CAP:
            errors.append("clean seed (flaw_type=none) must use expected_severity=minor")
    if "expected_keywords" in manifest:
        if not isinstance(manifest["expected_keywords"], list) or not all(
            isinstance(k, str) for k in manifest["expected_keywords"]
        ):
            errors.append("expected_keywords must be a list of strings")
    if ("expected_keywords" in manifest and manifest.get("flaw_type") != "none"
            and not manifest["expected_keywords"]):
        errors.append("defect seed must have non-empty expected_keywords")
    return errors


def severity_name(level: int) -> str:
    for name, order in SEVERITY_ORDER.items():
        if order == level:
            return name
    return "none"


def max_severity_in(text: str) -> int | None:
    """Return highest severity level found in report text, or None."""
    levels = [SEVERITY_ORDER[m.group(1).lower()] for m in SEVERITY_PATTERN.finditer(text)]
    if not levels:
        return None
    return max(levels)


def keyword_hit(text: str, keywords: list[str]) -> bool:
    """True if any keyword appears as a case-insensitive substring."""
    lower = text.lower()
    return any(k.lower() in lower for k in keywords if k)


def score_report(text: str, manifest: dict) -> tuple[bool, list[str]]:
    """Return (passed, reasons). See module docstring for the contract."""
    reasons: list[str] = []
    if manifest["flaw_type"] == "none":
        sev = max_severity_in(text)
        if sev is None or sev <= SEVERITY_ORDER["minor"]:
            reasons.append("clean seed: no blocker/major raised (max severity: %s)"
                           % (severity_name(sev) if sev else "none"))
            return True, reasons
        reasons.append("clean seed FAIL: report raised %s, expected none above minor"
                       % severity_name(sev))
        return False, reasons

    flaw = manifest["flaw_type"]
    expected = manifest["expected_severity"]
    hit = keyword_hit(text, manifest["expected_keywords"])
    sev = max_severity_in(text)
    sev_ok = sev is not None and sev >= SEVERITY_ORDER[expected]
    if hit and sev_ok:
        reasons.append("flaw type identified (%s) with severity %s >= expected %s"
                       % (flaw, severity_name(sev), expected))
        return True, reasons
    if not hit:
        reasons.append("no concept-level hit on expected_keywords for %s" % flaw)
    if not sev_ok:
        reasons.append("severity too low: report max %s, expected %s"
                       % (severity_name(sev) if sev else "none", expected))
    return False, reasons


def cmd_verify(args: argparse.Namespace) -> int:
    manifests = find_manifests()
    if not manifests:
        sys.exit("no seeds found under %s (exit 2)" % SEEDS_ROOT)
    failures = 0
    seen = set()
    for seed_id, path in manifests:
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            print("ERROR %s: cannot load manifest: %s" % (seed_id, exc))
            failures += 1
            continue
        domain, entry = seed_id.split("/", 1)
        errors = validate_manifest(manifest, seed_id, domain, entry)
        if seed_id in seen:
            errors.append("duplicate seed id")
        seen.add(seed_id)
        if not os.path.isfile(os.path.join(os.path.dirname(path), "fixture.py")):
            errors.append("missing fixture.py")
        if errors:
            print("FAIL %s:" % seed_id)
            for err in errors:
                print("  - %s" % err)
            failures += 1
        else:
            print("PASS %s (%s/%s)"
                  % (seed_id, manifest["flaw_type"], manifest["expected_severity"]))
    print("%d/%d manifests valid" % (len(manifests) - failures, len(manifests)))
    return 0 if failures == 0 else 1


def cmd_list(args: argparse.Namespace) -> int:
    for seed_id, path in find_manifests():
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            sys.exit("cannot load manifest %s: %s (run --verify)" % (path, exc))
        print("%-45s %-16s %s"
              % (seed_id, manifest.get("flaw_type", "?"), manifest.get("expected_severity", "?")))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    seed_id, report_path = args.score
    matches = [p for sid, p in find_manifests() if sid == seed_id]
    if not matches:
        sys.exit("unknown seed id %r (use --list)" % seed_id)
    try:
        manifest = load_manifest(matches[0])
    except (OSError, ValueError) as exc:
        sys.exit("cannot load manifest %s: %s (run --verify)" % (matches[0], exc))
    try:
        with open(report_path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        sys.exit("cannot read report file %s: %s" % (report_path, exc))
    passed, reasons = score_report(text, manifest)
    if args.json:
        print(json.dumps({
            "seed": seed_id,
            "passed": passed,
            "reasons": reasons,
            "flaw_type": manifest["flaw_type"],
            "expected_severity": manifest["expected_severity"],
        }, ensure_ascii=False))
    else:
        print("%s %s: %s" % ("PASS" if passed else "FAIL", seed_id, "; ".join(reasons)))
    return 0 if passed else 1


def cmd_score_all(args: argparse.Namespace) -> int:
    """批量评分(--score-all):本地回流工作流的基线命令。"""
    report_dir = args.score_all
    if not os.path.isdir(report_dir):
        sys.exit("report directory not found: %s (exit 2)" % report_dir)
    manifests = find_manifests()
    if not manifests:
        sys.exit("no seeds found under %s (exit 2)" % SEEDS_ROOT)

    results: list[dict] = []
    found_reports = 0
    for seed_id, path in manifests:
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            sys.exit("cannot load manifest %s: %s (run --verify)" % (path, exc))
        rname = report_filename(seed_id)
        rpath = os.path.join(report_dir, rname)
        if not os.path.isfile(rpath):
            results.append({"seed": seed_id, "status": "missing", "passed": False,
                            "reasons": ["no report file: %s" % rname]})
            continue
        found_reports += 1
        try:
            with open(rpath, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            sys.exit("cannot read report file %s: %s" % (rpath, exc))
        passed, reasons = score_report(text, manifest)
        results.append({"seed": seed_id, "status": "pass" if passed else "fail",
                        "passed": passed, "reasons": reasons,
                        "flaw_type": manifest["flaw_type"],
                        "expected_severity": manifest["expected_severity"]})
    if found_reports == 0:
        sys.exit("no report files (*.md) found in %s (exit 2)" % report_dir)

    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    missing = sum(1 for r in results if r["status"] == "missing")
    if args.json:
        print(json.dumps({"seeds": results, "summary": {
            "passed": passed, "failed": failed, "missing": missing, "total": len(results),
        }}, ensure_ascii=False))
    else:
        for r in results:
            print("%-7s %s: %s" % (r["status"].upper(), r["seed"], "; ".join(r["reasons"])))
        print("summary: %d/%d passed, %d failed, %d missing"
              % (passed, len(results), failed, missing))
    return 0 if (failed == 0 and missing == 0) else 1


def cmd_demo(args: argparse.Namespace) -> int:
    """Self-test the scoring logic across ALL seeds (pass/fail pairs)."""
    seed_ids = dict(find_manifests())
    # (seed, report, expect_pass, label) — 覆盖 score_report 全分支(M2:干净种子也带负例)
    checks = [
        # 缺陷种子:命中 + 严重级达标 → PASS
        ("scoring-detection/01-false-perfect",
         "空输入返回 100 属假满分(false-perfect):无数据不可观测,应退出总分 [blocker]",
         True, "defect hit+severity"),
        ("scoring-detection/02-degenerate-zero",
         "空数据返回 0 是假最差(false-worst):检测工具漏报比误报危险,应退出总分 [blocker]",
         True, "defect hit+severity"),
        ("scoring-detection/03-magic-threshold",
         "85 是魔数(magic-threshold),无出处且与默认上限 70 矛盾 [major]",
         True, "defect hit+severity"),
        ("scoring-detection/04-dead-branch",
         "clamp 后判断 clamped<0 是死代码(dead-branch),分支不可达 [major]",
         True, "defect hit+severity"),
        # 缺陷种子:严重级不足 → FAIL
        ("scoring-detection/01-false-perfect",
         "这是假满分(false-perfect),但只标了 [minor]",
         False, "severity too low"),
        ("scoring-detection/03-magic-threshold",
         "85 这个数可以补个注释 [minor]",
         False, "severity too low"),
        # 缺陷种子:关键词不中(概念未识别)→ FAIL
        ("scoring-detection/04-dead-branch",
         "这个函数有点长,建议拆分 [major]",
         False, "no keyword hit"),
        # 干净种子:良性报告(无 blocker/major)→ PASS
        ("scoring-detection/05-clean-toy", "逻辑清晰,阈值有出处,无发现", True, "clean benign"),
        ("scoring-detection/06-clean-config", "max 优先级正确,默认值有出处", True, "clean benign"),
        ("scoring-detection/07-clean-verdict",
         "无数据退出总分,实现符合契约 [minor]", True, "clean benign"),
        ("scoring-detection/08-out-of-scope", "静态查找表,本 skill 不适用", True, "out-of-scope benign"),
        # 干净种子:泛化 over-report → FAIL
        ("scoring-detection/05-clean-toy",
         "全部函数防御不足,一律 [blocker] 需重写 [major]",
         False, "clean gamey"),
        ("scoring-detection/08-out-of-scope", "查找表缺默认值 [blocker]", False, "out-of-scope over-report"),
    ]
    failures = 0
    for seed, report, expect, label in checks:
        if seed not in seed_ids:
            print("FAIL demo: seed %s not found (run --verify first)" % seed)
            failures += 1
            continue
        try:
            manifest = load_manifest(seed_ids[seed])
        except (OSError, ValueError) as exc:
            sys.exit("cannot load manifest %s: %s (run --verify)" % (seed_ids[seed], exc))
        passed, reasons = score_report(report, manifest)
        ok = (passed == expect)
        print("%s demo[%s] %s: %s -> %s"
              % ("PASS" if ok else "FAIL", label, seed,
                 "PASS" if passed else "FAIL", "; ".join(reasons)))
        if not ok:
            failures += 1
    print("demo %s" % ("OK" if failures == 0 else "%d FAIL" % failures))
    return 0 if failures == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Meta-benchmark runner for adversarial-development-loop "
                    "(contract: references/framework-manual.md).")
    parser.add_argument("--verify", action="store_true", help="validate all seed manifests")
    parser.add_argument("--list", action="store_true", help="list all seeds")
    parser.add_argument("--score", nargs=2, metavar=("SEED_ID", "REPORT"),
                        help="score a REFUTE report file against one seed")
    parser.add_argument("--score-all", metavar="DIR",
                        help="score every seed against reports in DIR "
                             "(file name: <seed-id with '/'->'_'>.md)")
    parser.add_argument("--demo", action="store_true", help="self-test scoring logic (all seeds)")
    parser.add_argument("--json", action="store_true",
                        help="with --score/--score-all: machine-readable JSON output")
    args = parser.parse_args(argv)

    chosen = [name for name, val in vars(args).items()
              if name in ("verify", "list", "score", "score_all", "demo")
              and val not in (False, None)]
    if len(chosen) != 1:
        parser.error("choose exactly one mode: --verify | --list | --score | --score-all | --demo")
    if args.verify:
        return cmd_verify(args)
    if args.list:
        return cmd_list(args)
    if args.score:
        return cmd_score(args)
    if args.score_all:
        return cmd_score_all(args)
    return cmd_demo(args)


if __name__ == "__main__":
    sys.exit(main())
