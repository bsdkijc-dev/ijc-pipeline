"""Synchronize IJC Judicial Knowledge Graph into Neo4j and export Cypher script."""
import os, re
from common import load, slug

def main():
    d = load()
    statements = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (k:KnowledgeObject) REQUIRE k.id IS UNIQUE;",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Claim) REQUIRE c.id IS UNIQUE;",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE;",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (q:Query) REQUIRE q.id IS UNIQUE;"
    ]

    for ko in d["Master_Knowledge_Objects"]:
        kid = ko["Knowledge ID"]
        title = ko["Knowledge Title"].replace("'", "\\'")
        mode = ko["Operational Mode"].replace("'", "\\'")
        chamber = ko["Chamber"].replace("'", "\\'")
        domain = ko["Domain / Subdomain"].replace("'", "\\'")
        status = ko["Review Status"].replace("'", "\\'")
        defn = str(ko.get("Source-Derived Definition", "")).replace("'", "\\'")
        statements.append(f"MERGE (k:KnowledgeObject {{id: '{kid}'}}) SET k.title = '{title}', k.mode = '{mode}', k.chamber = '{chamber}', k.domain = '{domain}', k.status = '{status}', k.definition = '{defn}';")

    for ev in d["Evidence_Provenance"]:
        eid = ev["Evidence ID"]
        etype = ev["Evidence Type"].replace("'", "\\'")
        desc = ev["Artefak / Evidence Description"].replace("'", "\\'")
        status = ev["Verification Status"].replace("'", "\\'")
        sha = ev["SHA-256 Hash Baseline"].replace("'", "\\'")
        statements.append(f"MERGE (e:Evidence {{id: '{eid}'}}) SET e.type = '{etype}', e.description = '{desc}', e.status = '{status}', e.sha256 = '{sha}';")

    ev_set = {e["Evidence ID"] for e in d["Evidence_Provenance"]}
    for c in d["Atomic_Claims_Graph"]:
        cid, kid = c["Claim ID"], c["Knowledge ID"]
        stmt = c["Atomic Claim Statement"].replace("'", "\\'")
        ctype, status = c["Claim Type"].replace("'", "\\'"), c["Verification Status"].replace("'", "\\'")
        statements.append(f"MERGE (c:Claim {{id: '{cid}'}}) SET c.statement = '{stmt}', c.type = '{ctype}', c.status = '{status}';")
        statements.append(f"MATCH (k:KnowledgeObject {{id: '{kid}'}}), (c:Claim {{id: '{cid}'}}) MERGE (k)-[:HAS_CLAIM]->(c);")
        for eid in re.findall(r"IJC-EVD-\d+", str(c.get("Linked Evidence ID", ""))):
            if eid in ev_set:
                statements.append(f"MATCH (c:Claim {{id: '{cid}'}}), (e:Evidence {{id: '{eid}'}}) MERGE (c)-[:SUPPORTED_BY]->(e);")

    for q in d["GEO_QA_Triage"]:
        qid = q["Query ID"]
        prompt = q["Target Judicial Prompt / Question"].replace("'", "\\'")
        ans = q["GEO Short Answer (Evidence-First)"].replace("'", "\\'")
        triage = q.get("Cassation Triage Classification", "QUESTION OF LAW").replace("'", "\\'")
        statements.append(f"MERGE (q:Query {{id: '{qid}'}}) SET q.prompt = '{prompt}', q.answer = '{ans}', q.triage = '{triage}';")
        for cid in re.findall(r"IJC-CLM-\d+", str(q.get("Linked Claim IDs", ""))):
            statements.append(f"MATCH (q:Query {{id: '{qid}'}}), (c:Claim {{id: '{cid}'}}) MERGE (q)-[:ADDRESSES]->(c);")
        for eid in re.findall(r"IJC-EVD-\d+", str(q.get("Linked Evidence IDs", ""))):
            if eid in ev_set:
                statements.append(f"MATCH (q:Query {{id: '{qid}'}}), (e:Evidence {{id: '{eid}'}}) MERGE (q)-[:CITES_EVIDENCE]->(e);")

    os.makedirs("dist/neo4j", exist_ok=True)
    with open("dist/neo4j/import.cypher", "w", encoding="utf-8") as f:
        f.write("\n".join(statements))
    print(f"Exported Cypher script: dist/neo4j/import.cypher ({len(statements)} statements)")

if __name__ == "__main__": main()
