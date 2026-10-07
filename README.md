# Bulk Certificate Generator

A backend service that generates personalized PDF certificates for large recipient lists. Built with FastAPI, SQLAlchemy, SQLite, and ReportLab.

## Features

- Create bulk certificate-generation jobs.
- Validate recipient names, email addresses, and duplicate emails.
- Process recipients asynchronously through a separate worker process.
- Generate a personalized PDF certificate for each recipient.
- Track job progress, successful generations, and failures.
- Isolate individual recipient failures so other recipients can continue.
- Retrieve job results and download completed certificates.
- Persist job and recipient status in a relational database.

## Technology Stack

- **Python** — application language
- **FastAPI** — REST API
- **SQLAlchemy** — database access and ORM
- **SQLite** — local relational database
- **ReportLab** — PDF generation
- **Pydantic** — request validation
- **pytest** — automated tests

## Architecture

1. The client submits a bulk certificate-generation request.
2. FastAPI validates the request and stores the job and recipients in SQLite.
3. A separate worker polls the database for pending recipients.
4. The worker generates a PDF for each recipient.
5. The worker stores each recipient's status and certificate path.
6. Clients can query job progress, inspect recipient results, and download generated certificates.

```text
Client
  |
  v
FastAPI REST API
  |
  v
SQLite Database <----- Certificate Worker
                           |
                           v
                     ReportLab PDF
                           |
                           v
                 storage/certificates/
```

## Requirements

- Python 3.11 or newer recommended
- pip
- Windows, macOS, or Linux

## Installation

Clone the repository or navigate to the project directory.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate it on Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Application

Run the API in the first terminal:

```bash
python -m uvicorn app.main:app --reload
```

Run the worker in a second terminal from the project root, with the same virtual environment activated:

```bash
python -m app.workers.certificate_worker
```

API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Keep both processes running while generating certificates.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/certificate-jobs` | Create a bulk generation job |
| GET | `/api/v1/certificate-jobs/{job_id}` | Retrieve job status and progress |
| GET | `/api/v1/certificate-jobs/{job_id}/results` | Retrieve recipient-level results |
| GET | `/api/v1/certificates/{certificate_id}` | Download a completed PDF |
| GET | `/health` | Health check |

## Example Request

Submit a POST request to `/api/v1/certificate-jobs`:

```json
{
  "event_name": "Python Development Workshop",
  "completion_date": "2026-10-07",
  "recipients": [
    {
      "name": "Omkar Chavan",
      "email": "omkar@example.com"
    },
    {
      "name": "Rahul Sharma",
      "email": "rahul@example.com"
    }
  ]
}
```

The API returns HTTP `202 Accepted` with a job ID and status/result URLs.

## Job Statuses

- `queued` — waiting for the worker.
- `processing` — at least one recipient is being processed or remains pending.
- `completed` — all recipients completed successfully.
- `completed_with_errors` — processing finished with one or more failed recipients.

Recipient statuses:

- `pending`
- `processing`
- `completed`
- `failed`

## Output

Generated PDFs are stored under:

```text
storage/certificates/
```

The SQLite database is created as:

```text
certificates.db
```

These files are local runtime artifacts and should not be committed to source control.

## Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

## Design Decisions and Limitations

- SQLite keeps the project free to run locally and avoids external infrastructure.
- A separate worker keeps PDF generation outside the API request lifecycle.
- Each recipient has an independent status and error field to support failure isolation.
- The current worker is designed for a single worker process. Safe multi-worker claiming and crash recovery would require additional coordination.
- The worker currently polls the database rather than using a dedicated message broker.
- This implementation does not send certificates by email.
