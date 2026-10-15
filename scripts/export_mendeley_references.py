from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.article09.article import REFERENCES


OUT = ROOT / "references" / "article09_qmi_references.ris"
REFERENCE_IDS = [
    "ABBAS-2021", "BALDI-HORNIK-1989", "CARO-2022", "CEREZO-VQA-2021",
    "CEREZO-CHALLENGES-2022", "DEMSAR-2006", "DU-2021", "EFRON-TIBSHIRANI-1993",
    "EGGINGER-2024", "GIL-FUSTER-2024", "GNEITING-RAFTERY-2007", "GOLDBERGER-2004",
    "GUO-2017", "HAVLICEK-2019", "HELBER-2019", "HOLM-1979", "HUANG-2021",
    "KRIZHEVSKY-2009", "MANGINI-2022", "MARI-2020", "ODAGIU-2025", "DINOV2-2024",
    "PEREZ-SALINAS-2020", "SCHNABEL-ROTH-2025", "SCHULD-KILLORAN-2019",
    "SCHULD-SWEKE-MEYER-2021", "THANASILP-2024", "WANG-2025", "MEDMNIST-2023",
]


def parse_reference(reference: str):
    match = re.match(r"^(.*?) \((\d{4})\) (.*?)\. (.*)$", reference)
    if not match:
        raise ValueError(reference)
    authors, year, title, remainder = match.groups()
    doi_match = re.search(r"https://doi\.org/(\S+)$", remainder)
    doi = doi_match.group(1) if doi_match else ""
    container = re.sub(r"\.?\s*https://doi\.org/\S+$", "", remainder).strip()
    return authors, year, title, container, doi


def author_lines(authors: str):
    if " et al" in authors:
        return [authors.replace(" et al", ""), "others"]
    return [part.strip() for part in authors.split(",") if part.strip()]


def main():
    if len(REFERENCE_IDS) != len(REFERENCES):
        raise RuntimeError("Reference identifier count does not match bibliography")
    records = []
    for citation_id, reference in zip(REFERENCE_IDS, REFERENCES):
        authors, year, title, container, doi = parse_reference(reference)
        record = ["TY  - JOUR", f"ID  - {citation_id}"]
        record.extend(f"AU  - {author}" for author in author_lines(authors))
        record.extend([f"PY  - {year}", f"TI  - {title}", f"JO  - {container}"])
        if doi:
            record.extend([f"DO  - {doi}", f"UR  - https://doi.org/{doi}"])
        record.extend([f"N1  - Imported for Article 09 QMI manuscript; citation key {citation_id}", "ER  - "])
        records.append("\n".join(record))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n\n".join(records) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} records to {OUT}")


if __name__ == "__main__":
    main()
