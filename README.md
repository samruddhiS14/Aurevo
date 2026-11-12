# Aurevo

Aurevo is an AI-assisted project collaboration and milestone-payment platform with separate Client and Freelancer portals. It uses React + Vite + Tailwind on the frontend and FastAPI + SQLAlchemy + PostgreSQL on the backend. PayPal Sandbox is used for milestone authorization/capture, Gemini supports scope generation and project assistance, and Redis + Celery run persistent reminders and overdue review automation.

## Current feature set

- Separate client and freelancer registration, login, dashboards, and role-checked API access.
- Project creation, project discovery, freelancer applications, and hiring.
- Versioned AI scope drafts and agreement routes; the client approves the scope, and both parties must approve the agreement version before milestone payment operations.
- Milestone deliverable uploads, submissions, review/revision/dispute statuses, audit history, and milestone-level PayPal payment records.
- PayPal Orders v2 `AUTHORIZE` flow, buyer approval, backend authorization, authorization-expiry tracking, full capture, request-id idempotency, and verified webhook processing.
- Redis + Celery review reminders and a periodic recovery sweep for the 72-hour automatic review deadline.
- Project chat, attachment sharing, context-sensitive rule-based off-platform intent detection, and platform-protection warnings. Ordinary mentions of email addresses, dates, Signal, Discord, or Wise do not trigger a warning by themselves.
- Dispute evidence records, neutral AI evidence summaries, and a mutual-resolution flow requiring both participants to accept.
- Profile editing, password changes with JWT session-version invalidation, notifications, and completed-project reviews.
- Currency-safe PayPal quote snapshots: project and agreement amounts remain in their selected currency while PayPal orders, authorizations, captures, and webhook comparisons use the saved USD quote.
- Agreement approval retry recovery, idempotent milestone generation, and a guarded agreement revision workflow before milestone work or payments begin.

## Requirements

- Python 3.11+ (use the version supported by the installed dependency lock/environment).
- Node.js 20+ and npm.
- PostgreSQL 14+.
- Redis 6.2+.
- PayPal Developer Sandbox application and sandbox buyer/merchant accounts.
- Gemini API key for AI scope generation, project copilot, AI dispute reports, and semantic chat-intent classification. Rule-based off-platform detection still works without Gemini.

## Backend setup

1. Open a terminal in `backend/`.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create a PostgreSQL database and copy the example environment file:

   ```bash
   cp .env.example .env
   ```

5. Set `DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`, and the PayPal Sandbox credentials in `backend/.env`. Keep this file private and never commit it.
6. Start Redis locally. For example, on macOS with Homebrew:

   ```bash
   brew services start redis
   ```

7. Apply the database migrations:

   ```bash
   alembic upgrade head
   ```

8. Start the API:

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

   API health: `http://127.0.0.1:8000/health`

   OpenAPI docs: `http://127.0.0.1:8000/docs`

9. In a second backend terminal, start a Celery worker:

   ```bash
   celery -A app.celery_app:celery_app worker --loglevel=info
   ```

10. In a third backend terminal, start Celery Beat:

    ```bash
    celery -A app.celery_app:celery_app beat --loglevel=info
    ```

The worker and Beat process must remain running for reminders and automatic milestone review/capture. Beat scans every five minutes so missed countdown tasks can be recovered after a Redis/worker interruption.

## Frontend setup

1. Open a terminal in `frontend/`.
2. Install dependencies:

   ```bash
   npm install
   ```

3. Copy `frontend/.env.example` to `frontend/.env` if you need a non-default API URL. The default points to `http://127.0.0.1:8000`.
4. Start Vite:

   ```bash
   npm run dev
   ```

5. Open the local Vite URL printed in the terminal (normally `http://localhost:5173`).

## PayPal Sandbox workflow

1. Create a Sandbox Business account and a Sandbox Personal account in the PayPal Developer Dashboard.
2. Create a Sandbox REST app and copy its Client ID and Secret into the backend `.env`.
3. Register a webhook that points to `/api/payments/webhooks/paypal`. For local development, expose the backend through a secure tunnel and register the public webhook URL. Save the Sandbox webhook ID in `PAYPAL_WEBHOOK_ID`.
4. The client creates/uses a milestone payment order. The backend creates an Orders v2 order with `intent=AUTHORIZE` and the PayPal buyer approves it.
5. The backend calls the Orders v2 authorize endpoint and stores the returned authorization ID and actual `expiration_time`.
6. After client approval, the client can capture the authorization. If the client does not respond to a submitted milestone before its configured deadline, the Celery worker can automatically approve and capture it, provided there is a valid, unexpired authorization and no active dispute/revision state.
7. PayPal webhook signatures are verified before an event is persisted. Events are idempotently recorded and amount/currency are checked before payment state changes.

**Important:** PayPal authorization/capture is not escrow. Aurevo does not hold funds in a regulated escrow account and does not guarantee PayPal approval, capture, refunds, or dispute outcomes. PayPal controls the actual authorization validity, risk checks, and capture result. The platform will not auto-capture if the authorization is missing/expired or if a dispute is active; it records the exception and notifies both parties. PayPal documents an initial three-day honor period and a time-limited authorization window; this implementation tracks the actual `expiration_time` and does not automatically reauthorize an older authorization. If your projects routinely take longer than the initial honor period before submission, add and test a reauthorization workflow before relying on automatic capture.

The implementation follows PayPal's current Orders v2 `AUTHORIZE` → buyer approval → order authorization → Payments v2 authorization capture sequence. The current PayPal order request uses `payment_source.paypal.experience_context` rather than the deprecated top-level `application_context`. See the official [Orders v2 API](https://developer.paypal.com/docs/api/orders/v2/), [Payments v2 API](https://developer.paypal.com/docs/api/payments/v2/), and [PayPal authorization and honor period guidance](https://developer.paypal.com/payment-methods/auth-honor/). PayPal currently documents a 3-day honor period within a generally 29-day authorization window; capture after the honor period is best-effort and is not guaranteed. Aurevo checks the returned authorization expiry and never assumes capture succeeded without PayPal confirmation.

### Currency conversion and quote integrity

- Frankfurter v2 provides the exchange rate when a non-USD milestone payment is created.
- The payment row stores the original milestone amount/currency, converted PayPal amount/currency, exchange rate, rate date, source, and fetch timestamp.
- The same saved quote is reused for order creation, authorization verification, capture, and webhook amount comparisons. A new rate is never fetched during authorization or capture.
- Legacy USD payment records without quote fields are treated as identity conversions. Legacy non-USD records with an existing PayPal order/authorization but no complete saved quote are moved to reconciliation instead of guessing the amount or currency.
- A milestone with a payment outcome requiring reconciliation cannot create a second PayPal order until the first outcome is resolved.

## 72-hour review automation

Production defaults:

```env
REDIS_URL=redis://localhost:6379/0
MILESTONE_REVIEW_HOURS=72
MILESTONE_REMINDER_HOURS=24,48
MILESTONE_REVIEW_MINUTES=0
MILESTONE_REMINDER_MINUTES=
CELERY_TASK_ALWAYS_EAGER=false
```

The timer starts when a freelancer submits a milestone, not when a project is created. Reminder delivery is deduplicated per milestone submission and offset. The periodic sweep recovers missed reminders and overdue reviews. A revision request or an open dispute stops automatic capture for that submission.

For a quick local test, use a short override in your private `.env`:

```env
MILESTONE_REVIEW_MINUTES=5
MILESTONE_REMINDER_MINUTES=1,2
```

Restart the API, worker, and Beat after changing these values. Remove the overrides to return to the 72-hour/24-hour/48-hour production defaults. Do not use the accelerated timer in production.

## AI behaviour and limits

- Scope generation and project copilot use the configured Gemini model.
- Chat off-platform detection uses explicit, context-sensitive patterns and never blocks or deletes messages. It intentionally ignores bare mentions of channel/provider names, dates, email addresses, or phone numbers unless the message indicates a move to external communication or payment.
- Gemini requests use a configured HTTP timeout and a bounded retry count. Temporary upstream failures return HTTP 503; invalid generated structured data returns HTTP 502 where applicable.
- Dispute AI reports summarize supplied text and evidence descriptions. Uploaded file contents are not parsed by the report generator; filenames are never treated as proof of file contents. AI does not decide who is at fault or make payment decisions.
- AI output is advisory and should be reviewed by the client/freelancer. Approved agreements and recorded project decisions remain the source of truth.

## File handling and production hardening

The API limits project chat and dispute evidence uploads to 10 MB and checks basic file signatures/extensions before storing randomized filenames. Participant-only download routes are enforced. This is not a malware scanner. Before production, add antivirus scanning, storage quotas, object storage with private signed URLs, retention controls, and operational backups.

The current authentication client stores access tokens in `sessionStorage`. For a production deployment, consider an HttpOnly/Secure/SameSite cookie-based session with CSRF protection, stronger rate limiting, audit monitoring, and a formal secret rotation process. These security architecture changes were not silently applied to the existing authentication flow.

## Database migrations

The migration chain after the Phase 5 schema is:

- `c91a4d72f103` — agreement, AI, PayPal, workspace, dispute, review, and reminder schema additions.
- `d4a9c81e7b20` — adds the `ADMIN` role to the PostgreSQL `user_role` enum.
- `e71c2a9b4f10` — adds immutable PayPal exchange-rate quote snapshot fields.
- `f6b2d8c41a90` — adds `users.token_version` for invalidating existing JWTs after password changes or administrator account activation changes.

Before upgrading an existing database, back it up and inspect `alembic current` and `alembic heads`. Do not reset the database or stamp a revision just to bypass a migration error. The historical baseline revision is intentionally empty; an existing database that was never tracked by Alembic needs a deliberate schema/revision reconciliation before running upgrades.

Run:

```bash
cd backend
alembic upgrade head
alembic current
```

Back up the database before applying migrations to an existing production database.

## Tests

Run backend tests with:

```bash
cd backend
python -m pytest -q
```

The test suite includes upload signature checks. For full end-to-end verification, test with PostgreSQL, a running Redis worker and Beat, real Gemini credentials, and PayPal Sandbox buyer/merchant accounts. The PayPal external payment flow cannot be considered live-verified until that environment is used.

## Important files

- `backend/app/main.py` — API route registration.
- `backend/app/services/paypal_service.py` — PayPal REST API client.
- `backend/app/api/routes/payments.py` — milestone order, authorization, and capture routes.
- `backend/app/api/routes/paypal_webhooks.py` — webhook verification and state reconciliation.
- `backend/app/celery_app.py` — Celery worker/Beat configuration.
- `backend/app/tasks/milestones.py` — review reminders and automatic approval/capture.
- `backend/app/api/routes/workspace.py` — project chat and off-platform warnings.
- `backend/app/api/routes/disputes.py` — evidence, AI report, and mutual resolution.
- `backend/app/api/routes/account.py` — profiles, notifications, password updates, and reviews.


## Aurevo administration

The Admin Panel is available at `/admin/login` and `/admin/dashboard`. Admin accounts are not publicly self-registered. After applying the Alembic migration, create the first administrator from the backend directory:

```bash
source .venv/bin/activate
alembic upgrade head
python -m app.scripts.create_admin
```

The bootstrap script prompts for the administrator email, name and password. Use a unique password of at least 12 characters. The Admin Panel provides platform monitoring and basic client/freelancer account activation controls. It does not provide payment capture or unilateral dispute-resolution controls.
