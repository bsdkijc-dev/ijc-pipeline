"""Integrity checks. Fails the build (exit 1) so bad data never reaches the wiki/Kaggle."""
import hashlib, os, re, sys
from common import load

WORDS = ["", "test", "password", "foo", "bar", "123", "1234", "12345", "123456", "1",
         "a", "abc", "hello", "admin", "secret", "sample", "example", "data", "null"]
TRIVIAL = {hashlib.sha256(w.encode()).hexdigest(): w for w in WORDS}
HEX = "0123456789abcdef"


def sequential_run(h, n=8):
    run = 1
    for a, b in zip(h, h[1:]):
        run = run + 1 if HEX.index(b) == (HEX.index(a) + 1) % 16 else 1
        if run >= n:
            return True
    return False


def main():
    d = load()
    errors, warns = [], []
    ko = {r["Knowledge ID"] for r in d["Master_Knowledge_Objects"]}
    ev = {r["Evidence ID"]: r for r in d["Evidence_Provenance"]}
    cl = {r["Claim ID"] for r in d["Atomic_Claims_Graph"]}

    for e in ev.values():
        i, h = e["Evidence ID"], str(e["SHA-256 Hash Baseline"]).strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", h):
            errors.append(f"{i}: hash is not 64 hex chars")
        elif h in TRIVIAL:
            errors.append(f"{i}: hash is SHA-256 of the trivial string {TRIVIAL[h]!r}, not of an evidence file")
        elif sequential_run(h):
            errors.append(f"{i}: hash contains an ascending hex run (looks hand-typed)")
        if "VERIFIED" in str(e["Hash Verified?"]) and "UNVERIFIED" not in str(e["Hash Verified?"]) \
                and e["Verification Status"] != "PASS":
            warns.append(f"{i}: hash VERIFIED but verification status is {e['Verification Status']}")

    for c in d["Atomic_Claims_Graph"]:
        if c["Knowledge ID"] not in ko:
            errors.append(f"{c['Claim ID']}: unknown Knowledge ID {c['Knowledge ID']}")
        for x in re.findall(r"IJC-EVD-\d+", str(c["Linked Evidence ID"])):
            if x not in ev:
                errors.append(f"{c['Claim ID']}: unknown evidence {x}")

    for q in d["GEO_QA_Triage"]:
        for x in re.findall(r"IJC-CLM-\d+", str(q["Linked Claim IDs"])):
            if x not in cl:
                errors.append(f"{q['Query ID']}: unknown claim {x}")
        for x in re.findall(r"IJC-EVD-\d+", str(q["Linked Evidence IDs"])):
            if x not in ev:
                errors.append(f"{q['Query ID']}: unknown evidence {x}")

    total = len(d["Master_Knowledge_Objects"])
    passed = sum(r["Review Status"] == "PASS" for r in d["Master_Knowledge_Objects"])
    print(f"Knowledge objects: {passed}/{total} PASS ({100*passed//max(total,1)}%)")
    for w in warns: print("WARN ", w)
    for e in errors: print("ERROR", e)
    if errors and not os.getenv("ALLOW_INVALID"):
        sys.exit(1)


if __name__ == "__main__":
    main()
