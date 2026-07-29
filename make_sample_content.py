"""Generate sample knowledge PDFs for staging / approval testing.

Pure standard library - no dependencies. Run:

    python make_sample_content.py

Upload the security/ files into security/_staging in Box, then run intake.py.
"""

from pathlib import Path

ROOT = Path("sample_content")

DOCUMENTS = {
    "security/customer-data-at-rest-policy.pdf": [
        "Customer Data at Rest Policy",
        "Domain: security | Status: draft for review | Owner: security-team",
        "",
        "Approved policy for handling customer data at rest",
        "",
        "1. All customer data at rest must be encrypted with AES-256.",
        "2. Encryption keys are stored in a managed KMS and rotated at least",
        "   annually, or immediately after a suspected compromise.",
        "3. Production data stores must live in approved regions only.",
        "4. Access to encrypted volumes requires break-glass procedures and",
        "   is logged for audit.",
        "5. Backups inherit the same encryption and retention controls as",
        "   the primary store.",
        "",
        "This document is intended as trusted security knowledge once approved.",
    ],
    "security/integration-launch-controls.pdf": [
        "Security Controls for New Integrations",
        "Domain: security | Owner: security-team",
        "",
        "Which security controls must a new integration pass before launch?",
        "",
        "Before launch, every new integration must pass:",
        "  - Threat model review with Security Engineering",
        "  - Dependency and secret scanning in CI",
        "  - Least-privilege OAuth / API scopes documented and approved",
        "  - Data classification confirmed (no unexpected PII egress)",
        "  - Logging and alerting hooks verified in staging",
        "  - Security sign-off recorded in the change ticket",
        "",
        "Integrations that fail any control remain blocked from production",
        "until remediated and re-reviewed.",
    ],
    "legal/data-processing-overview.pdf": [
        "Data Processing Overview",
        "Domain: legal",
        "",
        "High-level summary of how we process personal data under GDPR and",
        "similar regimes. Controllers, processors, and sub-processors must",
        "be documented. Transfer mechanisms require SCCs where applicable.",
    ],
    "product/platform-overview.pdf": [
        "Platform Product Overview",
        "Domain: product",
        "",
        "Our platform provides content management, collaboration, and AI",
        "capabilities for enterprise customers. Roadmap items are tracked",
        "separately and must not be treated as committed features.",
    ],
}


def _content_stream(lines: list[str]) -> bytes:
    parts = ["BT", "/F1 11 Tf", "72 720 Td", "14 TL"]
    for line in lines:
        safe = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        parts.append(f"({safe}) Tj")
        parts.append("T*")
    parts.append("ET")
    return ("\n".join(parts)).encode("latin-1")


def build_pdf(lines: list[str]) -> bytes:
    content = _content_stream(lines)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(pdf)
    count = len(objects) + 1
    pdf += f"xref\n0 {count}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()

    pdf += (
        b"trailer\n<< /Size " + str(count).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF\n"
    )
    return bytes(pdf)


def main() -> None:
    written = 0
    for relative, lines in DOCUMENTS.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(build_pdf(lines))
        print(f"Wrote {path}")
        written += 1

    rules = ROOT / "operating-rules" / "agent-operating-rules.md"
    rules.parent.mkdir(parents=True, exist_ok=True)
    rules.write_text(
        "\n".join(
            [
                "# Agent operating rules",
                "",
                "- Always authenticate as the Box service account, never a personal user.",
                "- Only operate inside the approved folders and Hubs you are given.",
                "- Answer only from approved content, and cite the source files.",
                "- Ask before deleting or overwriting content; preserve version history.",
                "- Save generated outputs back to the outputs folder for reuse.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {rules}")
    print(f"\nGenerated {written} PDFs + operating rules under {ROOT}/")
    print("Upload security/*.pdf into security/_staging in Box to test intake.")


if __name__ == "__main__":
    main()
