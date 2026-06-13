import argparse, json, re, zipfile
from pathlib import Path

SLUG="xiaojiao_provider_output_repair_candidate_error_guard_1008L"
FINAL_STATUS="XIAOJIAO_PROVIDER_OUTPUT_REPAIR_AND_CANDIDATE_ERROR_GUARD_PASS"
MARKER="ALL_1008L_PROVIDER_OUTPUT_REPAIR_AND_CANDIDATE_ERROR_GUARD_CHECKS_OK"
SECRET_PATTERNS=[re.compile(r"sk-[A-Za-z0-9_\-]{12,}"), re.compile(r"gho_[A-Za-z0-9_]{12,}"), re.compile(r"(?i)(authorization|bearer)\s*[:=]\s*['\"]?[^'\"]{12,}")]
FORBIDDEN=[".env","token","secret","node_modules","__pycache__",".db",".sqlite","dist","build","coverage",".DS_Store"]

def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def no_secret(p):
    text=Path(p).read_text(encoding="utf-8", errors="ignore")
    return not any(rx.search(text) for rx in SECRET_PATTERNS)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root", default="."); args=ap.parse_args(); root=Path(args.root)
    result_path=root/"docs/audit"/f"{SLUG}_result.json"
    manifest_path=root/"docs/audit_packages"/f"{SLUG}_manifest.json"
    zip_path=root/"docs/audit_packages"/f"{SLUG}.zip"
    for p in [result_path, manifest_path, zip_path]:
        if not p.exists(): raise SystemExit(f"VALIDATION_FAILED missing {p}")
    result=load(result_path); manifest=load(manifest_path)
    if result.get("final_status") != FINAL_STATUS or result.get("pass") is not True:
        raise SystemExit("VALIDATION_FAILED status")
    if result.get("marker") != MARKER:
        raise SystemExit("VALIDATION_FAILED marker")

    if result.get("provider_called") is not False or result.get("model_called") is not False:
        raise SystemExit("VALIDATION_FAILED no provider expected")
    if result.get("teacher_review_required") is not True or result.get("formal_apply_performed") is not False:
        raise SystemExit("VALIDATION_FAILED review gate")

    with zipfile.ZipFile(zip_path) as zf:
        names=sorted(zf.namelist())
    if names != sorted(manifest.get("entries") or []):
        raise SystemExit("VALIDATION_FAILED manifest zip mismatch")
    if manifest.get("manifest_minus_zip") != [] or manifest.get("zip_minus_manifest") != []:
        raise SystemExit("VALIDATION_FAILED manifest diffs")
    for name in names:
        if "\\" in name or name.startswith("/") or ":" in name:
            raise SystemExit(f"VALIDATION_FAILED bad zip path {name}")
        lower=name.lower()
        if any(f in lower for f in FORBIDDEN):
            raise SystemExit(f"VALIDATION_FAILED forbidden zip path {name}")
        if not no_secret(root/name):
            raise SystemExit(f"VALIDATION_FAILED possible secret leakage {name}")
    print(MARKER)

if __name__=="__main__":
    main()
