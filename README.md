# Box company brain

A minimal, runnable reference app that turns scattered company content into
**governed knowledge**: review new files with
[Box AI Extract](https://developer.box.com/guides/box-ai/ai-tutorials/extract-metadata-structured),
stamp governance metadata, publish approved content to a
[Box Hub](https://developer.box.com/guides/hubs-api/), and answer questions with
[Box AI Ask](https://developer.box.com/guides/box-ai/ai-tutorials/ask-questions)
grounded in that trusted layer.

It implements the **stage → review → approve → publish → ask** flow so humans
and agents work from the same permission-aware source of truth.

This is the companion repository to the tutorial
**[Build your company brain](https://developer.box.com/tutorials/company-brain)**.

## What it does

| Capability | How |
| --- | --- |
| Authenticate as a shared Service Account | Client Credentials Grant (`enterprise_id`) |
| Review staged files with a fixed schema | `POST /2.0/ai/extract_structured` (`review.py`) |
| Write governance metadata | `POST /2.0/files/:id/metadata/...` (`intake.py`) |
| Approve, move, and publish to a domain Hub | Metadata update + file move + Hubs API (`publish.py`) |
| Ask grounded questions with citations | `POST /2.0/ai/ask` against the hub (`ask.py`) |
| Find low-health approved content | Metadata query (`health.py`) |

## Project layout

```
box-company-brain/
├── box_client.py          # CCG Service Account auth
├── review.py              # Box AI structured review schema
├── intake.py              # Review staging folder + stamp metadata
├── publish.py             # Approve, move, create/reuse domain Hub
├── ask.py                 # Query the hub with citations
├── health.py              # Find approved files below a health threshold
├── make_sample_content.py # Generates sample_content/ for testing
├── sample_content/        # Upload into your Company Brain folders in Box
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.11+**
- A [free Box developer account](https://account.box.com/signup/developer),
  or a [Box Enterprise account](https://www.box.com/pricing) with **Box AI**
  and **Box Hubs** enabled
- A **Client Credentials Grant (CCG)** Platform App, **authorized**, with:
  - **Read and write all files and folders stored in Box**
  - **Manage AI**
  - **Manage enterprise properties** (create/write metadata)
- **Admin access** to create a **Knowledge Governance** metadata template
- A **Company Brain** folder tree in Box (see Setup), with the app's
  **Service Account** invited as **Editor** on the top-level folder

## Setup

1. **Clone and enter the project**

   ```bash
   git clone https://github.com/box-community/box-company-brain.git
   cd box-company-brain
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. **Create the Company Brain folders in Box**

   ```
   Company Brain/
   ├── security/
   │   ├── _staging/
   │   └── approved/
   ├── legal/
   │   ├── _staging/
   │   └── approved/
   ├── product/
   │   ├── _staging/
   │   └── approved/
   ├── operating-rules/
   └── outputs/
   ```

   Note the **staging** and **approved** folder IDs for the domain you will
   run end to end (for example `security`). Invite the Service Account
   (Developer Console → App Details → Service Account ID) as **Editor** on
   the top-level **Company Brain** folder.

4. **Create the Knowledge Governance metadata template** (Admin Console →
   **Metadata** → **New**). Add fields:

   | Field name | Type |
   | --- | --- |
   | Domain | Text |
   | Owner | Text |
   | Status | Text |
   | Content Health Score | Number |
   | Summary | Text |
   | Tags | Text |
   | Review Notes | Text |

   Copy the **template key** (keys are camelCase, e.g. `contentHealthScore`).

5. **Configure credentials**

   ```bash
   cp .env.example .env
   ```

   Fill in client credentials, enterprise ID, template key, and the staging /
   approved folder IDs.

   > **Never commit `.env`.** It is already in `.gitignore`.

6. **Generate and upload sample content** (optional)

   ```bash
   python make_sample_content.py
   ```

   Upload `sample_content/security/*.pdf` into `security/_staging`.

## Run

Work one domain end to end (example: security).

**1. Review everything in staging**

```bash
python intake.py
```

Each file gets AI review output and a `staged` governance metadata stamp.
Copy a file ID from the output into `.env` as `FILE_ID=...`.

**2. Approve and publish**

```bash
# .env should include FILE_ID, APPROVED_FOLDER_ID, DOMAIN, CONTENT_OWNER
python publish.py
```

Marks the file approved, moves it to `approved/`, creates (or reuses) a
domain Hub, and writes `BOX_HUB_ID` to `.env`.

> Wait a few minutes for Hub indexing before asking questions.

**3. Query the company brain**

```bash
python ask.py
# or:
python ask.py What is our approved policy for handling customer data at rest?
```

**4. (Optional) surface low-health approved content**

```bash
python health.py
python health.py 70
```

## How it works

1. **Staging** holds untrusted uploads. `intake.py` runs a fixed extract schema
   so every review returns the same fields.
2. Results are written as **Knowledge Governance** metadata (`staged`,
   unassigned owner) so status is searchable and auditable.
3. A human sets an owner and runs `publish.py`: status → `approved`, file moves
   to `approved/`, folder is added to a domain Hub.
4. `ask.py` queries that Hub with citations. Hubs and Box AI inherit Box
   permissions — agents only see what the Service Account (or user) can access.
5. Keep agent rules in `operating-rules/` and generated work in `outputs/` so
   every agent reads the same current rules and writes back under governance.

## Security notes

- Authenticate as the Service Account; share only the Company Brain folder tree.
- Prefer Hub `viewer` for consumers and `editor` for domain curators.
- Treat content health scores as signals for human review, not automatic approval.
- Answer only from approved Hub content and cite sources.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `invalid_client` | Check `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` / `BOX_ENTERPRISE_ID`. |
| `404 Not Found` | Invite the Service Account as **Editor** on the Company Brain folder. |
| `metadata_template must have both scope and template_key` | Set `BOX_METADATA_TEMPLATE_KEY` in `.env`. |
| Metadata `400` invalid parameters | Field keys in `build_governance` must match the template keys exactly (`domain`, `owner`, `status`, `contentHealthScore`, …). |
| Empty / irrelevant AI answers | Wait for Hub indexing; confirm approved files contain text. |
| `ModuleNotFoundError` | `source .venv/bin/activate` |

## License

[MIT](./LICENSE)
