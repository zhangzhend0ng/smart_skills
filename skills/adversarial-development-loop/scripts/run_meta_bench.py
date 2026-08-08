#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Meta-benchmark runner for the adversarial-development-loop skill.

Smoke-tests whether a REFUTE report catches the seeded flaws in fixture code.
Read the framework contract in references/framework-manual.md before editing.

Modes (exactly one):
  --verify                    validate every seed's manifest.json + fixture.py
  --list                      list all seeds
  --score SEED_ID REPORT      score one REFUTE report file against one seed
  --demo                      self-test the scoring logic with built-in reports

Scoring (see framework-manual.md §3):
  defect seed PASS = concept-level hit on expected_keywords (case-insensitive
                     substring, i.e. synonyms authored into the manifest)
                     AND max severity in report >= expected_severity
  clean seed  PASS = no [blocker] and no [major] in report
  All seeds PASS  = this baseline passes.

Anti-gaming: an over-eager reviewer that flags everything [blocker] fails on
the clean seeds (precision bound); a report that merely mentions the topic
without the flaw concept, or marks it too low severity, fails on the defect
seeds.

Honest limitations (must not be overstated):
  - Seeds are toy-level smoke tests, not a measure of skill quality.
  - Manifests are authored by the same author as the skill -> circular
    validation: a green bench only proves REFUTE's detection consistency
    against labeled seeds, not that the skill works on real code.
  - Real calibration (manual REFUTE passes on real targets) is out of scope.

Requires: Python 3 (stdlib only). Exits nonzero on any failure.
"""

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

SEVERITY_PATTERN = re.compile(r"\[(blocker|major|minor)\]", re.IGNORECASE)


def find_manifests(root=SEEDS_ROOT):
    """Return list of (seed_id, manifest_path) found under root, sorted."""
    found = []
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


def load_manifest(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_manifest(manifest, expected_id):
    """Return list of error strings for one manifest (empty == valid)."""
    errors = []
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


def severity_name(level):
    for name, order in SEVERITY_ORDER.items():
        if order == level:
            return name
    return "none"


def max_severity_in(text):
    """Return highest severity level found in report text, or None."""
    levels = [SEVERITY_ORDER[m.group(1).lower()] for m in SEVERITY_PATTERN.finditer(text)]
    if not levels:
        return None
    return max(levels)


def keyword_hit(text, keywords):
    """True if any keyword appears as a case-insensitive substring."""
    lower = text.lower()
    return any(k.lower() in lower for k in keywords if k)


def score_report(text, manifest):
    """Return (passed, reasons). See module docstring for the contract."""
    reasons = []
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


def cmd_verify(args):
    manifests = find_manifests()
    if not manifests:
        sys.exit("no seeds found under %s" % SEEDS_ROOT)
    failures = 0
    seen = set()
    for seed_id, path in manifests:
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            print("ERROR %s: cannot load manifest: %s" % (seed_id, exc))
            failures += 1
            continue
        errors = validate_manifest(manifest, seed_id)
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


def cmd_list(args):
    for seed_id, path in find_manifests():
        try:
            manifest = load_manifest(path)
        except (OSError, ValueError) as exc:
            sys.exit("cannot load manifest %s: %s (run --verify)" % (path, exc))
        print("%-45s %-16s %s"
              % (seed_id, manifest.get("flaw_type", "?"), manifest.get("expected_severity", "?")))
    return 0


def cmd_score(args):
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


def cmd_demo(args):
    """Self-test the scoring logic. Exits nonzero if any path is wrong."""
    seed_ids = dict(find_manifests())
    checks = [
        ("scoring-detection/01-false-perfect",
         "空输入返回 100 属假满分(false-perfect):无数据不可观测,应退出总分 [blocker]",
         True, "defect seed detected"),
        ("scoring-detection/05-clean-toy",
         "全部函数防御不足,一律 [blocker] 需重写 [major]",
         False, "clean seed rejects gamey over-reporting"),
        ("scoring-detection/03-magic-threshold",
         "85 这个数可以补个注释 [minor]",
         False, "severity below expectation fails"),
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Meta-benchmark runner for adversarial-development-loop "
                    "(contract: references/framework-manual.md).")
    parser.add_argument("--verify", action="store_true", help="validate all seed manifests")
    parser.add_argument("--list", action="store_true", help="list all seeds")
    parser.add_argument("--score", nargs=2, metavar=("SEED_ID", "REPORT"),
                        help="score a REFUTE report file against one seed")
    parser.add_argument("--demo", action="store_true", help="self-test scoring logic")
    parser.add_argument("--json", action="store_true",
                        help="with --score: print a machine-readable JSON result (for aggregation)")
    args = parser.parse_args(argv)

    chosen = [name for name, val in vars(args).items()
              if name in ("verify", "list", "score", "demo") and val not in (False, None)]
    if len(chosen) != 1:
        parser.error("choose exactly one mode: --verify | --list | --score | --demo")
    if args.verify:
        return cmd_verify(args)
    if args.list:
        return cmd_list(args)
    if args.score:
        return cmd_score(args)
    return cmd_demo(args)


if __name__ == "__main__":
    sys.exit(main())
