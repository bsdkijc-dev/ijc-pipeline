"""Synchronize IJC Judicial Knowledge Objects and Claims into Qdrant Vector Search."""
import hashlib, json, math, os, re
from common import load

COLLECTION_NAME = "ijc_judicial_knowledge"
VECTOR_SIZE = 384

def deterministic_vector(text, dim=VECTOR_SIZE):
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower()) or ["empty"]
    for w in words:
        h = int(hashlib.sha256(w.encode("utf-8")).hexdigest()[:8], 16)
        sign = 1.0 if ((h >> 16) & 1) else -1.0
        vec[h % dim] += sign
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [round(x / norm, 6) for x in vec]

def id_to_int(s):
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF

def main():
    d = load()
    points = []
    for ko in d["Master_Knowledge_Objects"]:
        kid = ko["Knowledge ID"]
        text = f"{ko['Knowledge Title']}. {ko.get('Source-Derived Definition', '')} {ko.get('Established (Proven Fact)', '')}"
        points.append({
            "id": id_to_int(kid), "vector": deterministic_vector(text),
            "payload": {"entity_id": kid, "entity_type": "KNOWLEDGE_OBJECT", "title": ko["Knowledge Title"], "mode": ko["Operational Mode"], "chamber": ko["Chamber"], "text": text}
        })
    for c in d["Atomic_Claims_Graph"]:
        cid = c["Claim ID"]
        text = f"Claim {cid}: {c['Atomic Claim Statement']}. Type: {c['Claim Type']}."
        points.append({
            "id": id_to_int(cid), "vector": deterministic_vector(text),
            "payload": {"entity_id": cid, "entity_type": "CLAIM", "knowledge_id": c["Knowledge ID"], "claim_type": c["Claim Type"], "text": text}
        })

    os.makedirs("dist/qdrant", exist_ok=True)
    with open("dist/qdrant/collection_schema.json", "w", encoding="utf-8") as f:
        json.dump({"collection_name": COLLECTION_NAME, "vectors_config": {"size": VECTOR_SIZE, "distance": "Cosine"}}, f, indent=2)
    with open("dist/qdrant/points.json", "w", encoding="utf-8") as f:
        json.dump(points, f, indent=2)
    print(f"Exported Qdrant points: dist/qdrant/points.json ({len(points)} vector points)")

if __name__ == "__main__": main()
