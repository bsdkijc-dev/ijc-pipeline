"""Generate Moodle Question Bank (Moodle XML 1.0) and Tracker CSV from IJC Knowledge Objects."""
import csv, html, os, re
from common import load, excel_date, slug

def escape_xml(s):
    return html.escape(str(s or ""), quote=True)

def build_moodle_questions():
    d = load()
    ko_list, claims, evid, geo = d["Master_Knowledge_Objects"], d["Atomic_Claims_Graph"], d["Evidence_Provenance"], d["GEO_QA_Triage"]
    claims_by_ko, geo_by_claim = {}, {}
    for c in claims: claims_by_ko.setdefault(c["Knowledge ID"], []).append(c)
    for q in geo:
        for cid in re.findall(r"IJC-CLM-\d+", str(q["Linked Claim IDs"])):
            geo_by_claim.setdefault(cid, []).append(q)

    questions, q_counter = [], 1
    for ko in ko_list:
        kid, title, mode, domain, chamber = ko["Knowledge ID"], ko["Knowledge Title"], ko["Operational Mode"], ko["Domain / Subdomain"], ko["Chamber"]
        category_path = f"$course$/JPAIS/{mode}/{domain}/{kid}"
        ko_claims = claims_by_ko.get(kid, [])

        # 1. Understand Definition
        q1_id = f"Q-{kid}-{q_counter:03d}"
        q_counter += 1
        q1_correct = str(ko.get("Source-Derived Definition") or ko.get("Established (Proven Fact)") or "Standar operasional").strip()
        questions.append({
            "question_id": q1_id, "source_stable_id": kid, "wiki_title": title, "moodle_category": category_path,
            "question_name": f"[JPAIS] {kid} [{q1_id[-3:]}] UNDERSTAND [MEDIUM] Definisi & Batas Epistemik",
            "type": "multichoice", "bloom": "UNDERSTAND", "difficulty": "MEDIUM", "competency": "LEGAL_KNOWLEDGE",
            "question_text": f"<p>Dalam kerangka <strong>{title}</strong> ({mode}), manakah definisi atau batasan pembuktian yang tepat?</p>",
            "correct_answer": q1_correct,
            "distractors": ["Asas pembuktian bebas tanpa verifikasi rantai kustodi.", "Otomatisasi putusan yudisial tanpa pengujian materiil.", "Penyamaan nilai derived evidence dengan raw bitstream."],
            "rationale": f"Berdasarkan definisi resmi {kid}.", "source_evidence": f"Master KO: {kid} - {title}",
            "verification_status": "VERIFIED", "grade": "1", "penalty": "0.3333333", "tags": ["JPAIS", kid, "UNDERSTAND", "MEDIUM"]
        })

        # 2. Apply Claim Scenario
        for c in ko_claims:
            cid, c_stmt, c_type, c_status = c["Claim ID"], c["Atomic Claim Statement"], c["Claim Type"], c["Verification Status"]
            q2_id = f"Q-{kid}-{q_counter:03d}"
            q_counter += 1
            questions.append({
                "question_id": q2_id, "source_stable_id": kid, "wiki_title": title, "moodle_category": category_path,
                "question_name": f"[JPAIS] {kid} [{q2_id[-3:]}] APPLY [HARD] {c_type} - {cid}",
                "type": "multichoice", "bloom": "APPLY", "difficulty": "HARD", "competency": "EVIDENCE_ANALYSIS",
                "question_text": f"<p><strong>Skenario Kasus Persidangan ({chamber}):</strong></p><p>Penggugat mengajukan klaim: <blockquote>\"{c_stmt}\"</blockquote>Bagaimanakah majelis hakim harus menilai klaim ini?</p>",
                "correct_answer": f"Klaim dikategorikan sebagai {c_type} ({c_status}) dan harus diuji berdasarkan verifikasi artefak bukti terkait.",
                "distractors": ["Klaim dianggap sebagai fakta mutlak tanpa korelasi alat bukti elektronik.", "Klaim otomatis gugur karena peradilan melarang analisis forensik komputasi.", "Klaim dialihkan menjadi wewenang panitera tanpa penetapan hakim."],
                "rationale": f"Klaim {cid} terdaftar dengan tipe {c_type} ({c_status}).", "source_evidence": f"Claim {cid}: {c_stmt}",
                "verification_status": "VERIFIED", "grade": "1", "penalty": "0.3333333", "tags": ["JPAIS", kid, cid, "APPLY", "HARD"]
            })

        # 3. Create Evaluative Essay
        q3_id = f"Q-{kid}-{q_counter:03d}"
        q_counter += 1
        questions.append({
            "question_id": q3_id, "source_stable_id": kid, "wiki_title": title, "moodle_category": category_path,
            "question_name": f"[JPAIS] {kid} [{q3_id[-3:]}] CREATE [EXPERT] Analisis Kebijakan Peradilan",
            "type": "essay", "bloom": "CREATE", "difficulty": "EXPERT", "competency": "POLICY_ANALYSIS",
            "question_text": f"<p>Analisis penerapan standar <em>{title}</em> dalam kamar {chamber}. Jelaskan pemisahan antara Proven Fact, Supported Inference, dan Unknown.</p>",
            "correct_answer": "Rubrik: (1) Pemisahan fakta vs inferensi (30%), (2) Integritas bukti & rantai kustodi (35%), (3) Ratio decidendi (35%).",
            "distractors": [], "rationale": "Uji sintesis yudisial komprehensif.", "source_evidence": f"KO Sections: Established, Supported Inference ({kid})",
            "verification_status": "VERIFIED-INFERENCE", "grade": "5", "penalty": "0", "tags": ["JPAIS", kid, "CREATE", "EXPERT"]
        })

    return questions

def generate_moodle_xml(questions, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']
    curr_cat = None
    for q in questions:
        if q["moodle_category"] != curr_cat:
            curr_cat = q["moodle_category"]
            xml += ['  <question type="category">', f'    <category><text>{escape_xml(curr_cat)}</text></category>', '  </question>']
        if q["type"] == "multichoice":
            xml += [
                '  <question type="multichoice">',
                f'    <name><text>{escape_xml(q["question_name"])}</text></name>',
                f'    <questiontext format="html"><text><![CDATA[{q["question_text"]}]]></text></questiontext>',
                f'    <generalfeedback format="html"><text><![CDATA[<p><strong>Rationale:</strong> {escape_xml(q["rationale"])}</p>]]></text></generalfeedback>',
                f'    <defaultgrade>{q["grade"]}</defaultgrade><penalty>{q["penalty"]}</penalty><single>true</single><shuffleanswers>true</shuffleanswers>',
                f'    <answer fraction="100" format="html"><text><![CDATA[<p>{escape_xml(q["correct_answer"])}</p>]]></text></answer>'
            ]
            for d in q["distractors"]:
                xml += [f'    <answer fraction="0" format="html"><text><![CDATA[<p>{escape_xml(d)}</p>]]></text></answer>']
            xml += ['  </question>']
        elif q["type"] == "essay":
            xml += [
                '  <question type="essay">',
                f'    <name><text>{escape_xml(q["question_name"])}</text></name>',
                f'    <questiontext format="html"><text><![CDATA[{q["question_text"]}]]></text></questiontext>',
                f'    <generalfeedback format="html"><text><![CDATA[<p>{q["correct_answer"]}</p>]]></text></generalfeedback>',
                f'    <defaultgrade>{q["grade"]}</defaultgrade><responseformat>editor</responseformat>',
                '  </question>'
            ]
    xml += ['</quiz>']
    with open(output_path, "w", encoding="utf-8") as f: f.write("\n".join(xml))
    print(f"Generated Moodle XML: {output_path} ({len(questions)} questions)")

def generate_tracker_csv(questions, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = ["Question ID", "Source Stable ID", "Wiki Page Title", "Bloom Level", "Difficulty", "Question Type", "Competency Domain", "Question Text / Scenario", "Correct Answer", "Answer Rationale", "Moodle Category Path", "Export Ready"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in questions:
            writer.writerow({
                "Question ID": q["question_id"], "Source Stable ID": q["source_stable_id"], "Wiki Page Title": q["wiki_title"],
                "Bloom Level": q["bloom"], "Difficulty": q["difficulty"], "Question Type": q["type"],
                "Competency Domain": q["competency"], "Question Text / Scenario": re.sub(r"<[^>]+>", "", q["question_text"]),
                "Correct Answer": q["correct_answer"], "Answer Rationale": q["rationale"], "Moodle Category Path": q["moodle_category"], "Export Ready": "YES"
            })
    print(f"Generated Question Bank Tracker CSV: {output_path}")

def main():
    questions = build_moodle_questions()
    generate_moodle_xml(questions, "dist/moodle/ijc_moodle_question_bank.xml")
    generate_tracker_csv(questions, "dist/moodle/Question_Bank_Tracker.csv")

if __name__ == "__main__": main()
