"""Build all distribution artifacts: Kaggle, Wiki, Moodle XML, Neo4j Cypher, and Qdrant Vectors."""
import csv, importlib.util, json, os, sys

scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

def import_script(name, filename):
    filepath = os.path.join(scripts_dir, filename)
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

common = import_script("common", "common.py")
load, excel_date, slug = common.load, common.excel_date, common.slug

build_moodle = import_script("build_moodle", "build_moodle.py")
sync_neo4j = import_script("sync_neo4j", "sync_neo4j.py")
sync_qdrant = import_script("sync_qdrant", "sync_qdrant.py")

d = load()
os.makedirs("dist/kaggle", exist_ok=True)
os.makedirs("dist/wiki", exist_ok=True)

# 1. Kaggle CSVs
for name, rows in d.items():
    with open(f"dist/kaggle/{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            r = dict(r)
            if "Verified At" in r: r["Verified At"] = excel_date(r["Verified At"])
            w.writerow(r)
user = os.getenv("KAGGLE_USERNAME", "your-kaggle-username")
json.dump({"title": "IJC Four-Mode Judicial Knowledge Management System", "id": f"{user}/ijc-judicial-knowledge", "licenses": [{"name": "CC-BY-4.0"}]}, open("dist/kaggle/dataset-metadata.json", "w"), indent=2)

# 2. MediaWiki Pages
claims, evid, geo = d["Atomic_Claims_Graph"], d["Evidence_Provenance"], d["GEO_QA_Triage"]
ev_by_id = {e["Evidence ID"]: e for e in evid}

def page(k):
    kid = k["Knowledge ID"]
    mine = [c for c in claims if c["Knowledge ID"] == kid]
    qs = [q for q in geo if any(c["Claim ID"] in str(q["Linked Claim IDs"]) for c in mine)]
    t = [f"= {k['Knowledge Title']} =", '{| class="wikitable"', f"|-\n! ID\n| {kid}", f"|-\n! Mode\n| {k['Operational Mode']}", f"|-\n! Chamber / Domain\n| {k['Chamber']} / {k['Domain / Subdomain']}", f"|-\n! Reference\n| {k['Case / File Reference']}", f"|-\n! Confidentiality\n| {k['Confidentiality']}", f"|-\n! Review status\n| {k['Review Status']}", f"|-\n! Verified\n| {k['Knowledge Grapher']}, {excel_date(k['Verified At'])}", "|}", "", "== Definition ==", str(k["Source-Derived Definition"]), "", "== Established ==", str(k["Established (Proven Fact)"]), "", "== Supported inference ==", str(k["Supported Inference"]), "", "== Unknown / not established ==", str(k["Unknown / Not Established"]), "", "== Atomic claims =="]
    for c in mine:
        t.append(f"* '''{c['Claim ID']}''' ({c['Claim Type']}, {c['Verification Status']}): {c['Atomic Claim Statement']}")
        for x in str(c["Linked Evidence ID"]).replace(" ", "").split(","):
            if x in ev_by_id:
                e = ev_by_id[x]
                t.append(f"** {x} [{e['Evidence Type']}, {e['Verification Status']}]: {e['Artefak / Evidence Description']}")
    if qs:
        t += ["", "== Related questions =="] + [f"* {q['Query ID']}: {q['Target Judicial Prompt / Question']}" for q in qs]
    t += ["", "[[Category:IJC Knowledge Objects]]", f"[[Category:{slug(k['Operational Mode'])}]]"]
    return "\n".join(t)

index = ["= IJC Knowledge Objects ="]
for k in d["Master_Knowledge_Objects"]:
    title = f"IJC:{k['Knowledge ID']}"
    open(f"dist/wiki/{slug(title)}.wiki", "w", encoding="utf-8").write(page(k))
    index.append(f"* [[{title}|{k['Knowledge ID']}]] – {k['Knowledge Title']} ({k['Review Status']})")
open("dist/wiki/IJC_Index.wiki", "w", encoding="utf-8").write("\n".join(index))
print(f"built {len(d['Master_Knowledge_Objects'])} wiki pages and {len(d)} csv files")

# 3. Moodle XML
build_moodle.main()

# 4. Neo4j Cypher
sync_neo4j.main()

# 5. Qdrant Vectors
sync_qdrant.main()
