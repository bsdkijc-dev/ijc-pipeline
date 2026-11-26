<div align="center">

<img src="assets/logo.png" alt="IJC Four-Mode Judicial Knowledge Pipeline Logo" width="140">

# IJC Four-Mode Judicial Knowledge Pipeline

### Convert the IJC knowledge workbook into Kaggle tables, MediaWiki pages, Moodle XML, Neo4j graphs, and Qdrant vectors.

[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE) ![Stack](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white) [![CI](https://github.com/bsdkijc-dev/ijc-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/bsdkijc-dev/ijc-pipeline/actions/workflows/pipeline.yml) [![Kaggle](https://img.shields.io/badge/Kaggle-Dataset-20BEFF?style=flat&logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/judicialcollege/ijc-judicial-knowledge)

[Documentation](scripts/) · [Kaggle](https://www.kaggle.com/datasets/judicialcollege/ijc-judicial-knowledge) · [Repository](https://github.com/bsdkijc-dev/ijc-pipeline)

</div>

---

Scripts that turn the Indonesian Judicial College (IJC) knowledge workbook (`data/ijc.xlsx`) into Kaggle tables, wiki pages, a Moodle question bank, a Neo4j graph and Qdrant vectors.

| Script (in `scripts/`) | What it does |
|---|---|
| `common.py` | Loads the IJC workbook from Google Sheets when credentials are set, otherwise from `data/ijc.xlsx` |
| `validate.py` | Integrity checks; stops the build if the data is invalid |
| `build.py` | Builds all outputs: Kaggle CSVs, wiki pages, Moodle XML, Neo4j Cypher and Qdrant vectors |
| `build_moodle.py` | Builds the Moodle XML question bank and a tracker CSV |
| `publish_wiki.py` | Uploads the wiki pages to MediaWiki |
| `sync_neo4j.py` | Syncs the knowledge graph into Neo4j and exports a Cypher script |
| `sync_qdrant.py` | Syncs the knowledge objects and claims into Qdrant |

The GitHub Actions workflows in `.github/workflows/` run the pipeline. Credentials (Google Sheets, Kaggle user name, MediaWiki) come from environment variables or repository secrets, never from the code.

Published dataset: https://www.kaggle.com/datasets/judicialcollege/ijc-judicial-knowledge

## Author and citation

**Author:** Cecep Mustafa, Indonesian Judicial College (IJC). ORCID: [0000-0003-0037-497X](https://orcid.org/0000-0003-0037-497X)

**Cite as:** Mustafa, C. (2026). *IJC Four-Mode Judicial Knowledge pipeline* [Computer software]. GitHub. https://github.com/bsdkijc-dev/ijc-pipeline

GitHub also shows a "Cite this repository" button, built from `CITATION.cff`.

## Licence

MIT. See `LICENSE`.

---

<div align="center">

**IJC Four-Mode Judicial Knowledge Pipeline**

[github.com/bsdkijc-dev/ijc-pipeline](https://github.com/bsdkijc-dev/ijc-pipeline)

</div>
