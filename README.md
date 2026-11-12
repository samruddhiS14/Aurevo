# Aurevo AI — Intelligent Freelance Project & Payment Platform

**Build What's Next with PayPal and AI**

Aurevo AI is an AI-powered freelance project management platform designed to make collaboration between clients and freelancers more structured, transparent, and secure.

By combining AI-powered project assistance with PayPal's payment infrastructure, Aurevo helps clients define projects, manage milestones, collaborate with freelancers, and handle milestone-based payments through a streamlined workflow.

---

## About the Project

Freelance projects often face challenges such as unclear requirements, communication gaps, scope changes, delayed payments, and a lack of transparency between clients and freelancers.

Aurevo AI aims to address these challenges by bringing project intelligence and payment management together in one platform.

The platform uses **Artificial Intelligence to assist with project understanding and workflow management**, while **PayPal provides the payment infrastructure for milestone-based transactions**.

Instead of treating project management and payments as separate activities, Aurevo connects them through a unified workflow.

## Key Features

### 1. AI-Powered Project Assistance

- AI-assisted project scope generation.
- Helps transform project ideas into more structured requirements.
- AI-powered project assistance for better project understanding.
- AI-supported review of submitted work.
- Helps identify potential scope and policy-related concerns.

### 2. Project & Freelancer Management

- Clients can create and manage projects.
- Freelancers can explore projects and submit applications.
- Clients can review applications and select freelancers.
- Dedicated project workspaces for collaboration.
- Structured project and milestone tracking.

### 3. PayPal-Powered Milestone Payments

- Integration with the PayPal Developer Platform.
- PayPal Sandbox support for testing transactions.
- Payment authorization and capture workflows.
- Milestone-based payment processing.
- Payment status tracking.
- Exchange-rate handling for supported currencies.
- PayPal webhook integration for payment event handling.

### 4. Transparent Project Workflow

- Track project progress through milestones.
- Monitor payment and milestone statuses.
- Maintain structured project records.
- Support communication and collaboration between project participants.

---

## How Aurevo AI Works

1. **Project Creation:** A client creates a project and provides the initial requirements.
2. **AI Assistance:** AI helps structure the project scope and clarify requirements.
3. **Freelancer Applications:** Freelancers explore available projects and apply.
4. **Freelancer Selection:** The client reviews applications and selects a freelancer.
5. **Project Agreement:** The project moves into a structured workflow with defined milestones.
6. **Work Submission:** The freelancer works on and submits milestone deliverables.
7. **AI-Assisted Review:** AI tools assist with reviewing submissions and identifying potential concerns.
8. **PayPal Payment:** PayPal handles the authorization and capture process for milestone payments.
9. **Progress Tracking:** Project and payment statuses are updated as milestones progress.

---

## AI Integration

Aurevo uses Google's Gemini AI to provide intelligent assistance throughout the project lifecycle.

**AI capabilities include:**

| AI Capability | Purpose |
|---|---|
| Scope Generation | Helps convert project descriptions into structured scopes. |
| Project Copilot | Provides AI-powered assistance for project-related tasks. |
| Submission Review | Supports AI-assisted evaluation of submitted work. |
| Policy Detection | Helps identify potential policy-related concerns. |
| Scope Validation | Helps validate generated project requirements. |

AI is incorporated into the platform's functionality rather than being used only as a conversational interface.

**AI Technology:** Google Gemini API

---

## PayPal Integration

PayPal is a core component of Aurevo's payment workflow.

The platform integrates the PayPal Developer Platform to support milestone-based payments between clients and freelancers.

**PayPal capabilities used:**

- PayPal REST APIs.
- Orders API for creating payment orders.
- Authorization flow for payment authorization.
- Capture API for capturing authorized payments.
- Webhooks for receiving payment-related events.
- PayPal Sandbox for development and testing.

### Payment Workflow

1. A payment is initiated for a project milestone.
2. Aurevo creates a PayPal order.
3. The client approves the payment through PayPal.
4. The backend processes the authorization.
5. Once the milestone is ready for payment capture, Aurevo initiates the capture process.
6. The backend verifies the returned payment details and updates the payment and milestone records.

**Note:** This project currently uses the PayPal Sandbox environment for testing. Sandbox transactions do not represent real-money payments.

---

## Technology Stack

### Frontend

- React.js
- Vite
- JavaScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic

### Artificial Intelligence

- Google Gemini API

### Payment Infrastructure

- PayPal Developer Platform
- PayPal REST APIs
- PayPal Webhooks

### Supporting Technologies

- PostgreSQL (database configuration)
- Redis and Celery (background task infrastructure)
- Git and GitHub

---

## Project Architecture

```text
Aurevo_AI/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tasks/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── services/
│   ├── package.json
│   └── .env.example
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Getting Started

Follow these instructions to run Aurevo AI locally.

### Prerequisites

Install the following:

- Python 3.10 or later
- Node.js and npm
- PostgreSQL
- Redis (if running background task workers)
- PayPal Developer Sandbox account
- Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/samruddhiS14/Aurevo.git
cd Aurevo
```

### 2. Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Configure the required environment variables in `backend/.env`.

### 3. Configure Backend Environment Variables

The backend environment configuration includes:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Database connection string |
| `JWT_SECRET_KEY` | Secret used for authentication tokens |
| `JWT_ALGORITHM` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Gemini model configuration |
| `PAYPAL_CLIENT_ID` | PayPal Sandbox client ID |
| `PAYPAL_CLIENT_SECRET` | PayPal Sandbox client secret |
| `PAYPAL_BASE_URL` | PayPal API base URL |
| `PAYPAL_WEBHOOK_ID` | PayPal webhook identifier |
| `PAYPAL_RETURN_URL` | Frontend payment success URL |
| `PAYPAL_CANCEL_URL` | Frontend payment cancellation URL |
| `REDIS_URL` | Redis connection URL |

Additional configuration options are documented in `.env.example`.

**Never commit your actual `.env` file, API keys, PayPal credentials, or database passwords.**

### 4. Run Database Migrations

From the backend directory:

```bash
alembic upgrade head
```

### 5. Start the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

Backend API:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open a new terminal and navigate to the frontend:

```bash
cd Aurevo/frontend
```

Install dependencies:

```bash
npm install
```

Create the frontend environment file:

```bash
cp .env.example .env
```

Configure the API URL in the frontend environment file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the local development URL displayed in your terminal, typically:

```text
http://localhost:5173
```

---

## Security & Configuration

Aurevo follows an environment-based configuration approach.

- API credentials are stored in environment variables.
- Sensitive environment files are excluded through `.gitignore`.
- Authentication uses JWT-based tokens.
- PayPal credentials are configured on the backend.
- Payment processing is handled through backend services.
- Sandbox credentials should be used for development and testing.

Do not publish real credentials or private transaction information.

---

## Testing

The backend includes tests for core platform functionality and file validation.

Run the tests from the backend directory:

```bash
pytest
```

For payment testing, configure PayPal Sandbox credentials and use separate Sandbox buyer and seller accounts.

---

## Hackathon Alignment

Aurevo AI was developed in alignment with the **Build What's Next with PayPal and AI** hackathon challenge.

The project combines two central technologies:

**Artificial Intelligence**

- Google Gemini-powered project assistance.
- AI-supported project scope generation and validation.
- AI-assisted submission review and policy detection.

**PayPal**

- PayPal Developer Platform integration.
- Payment order creation.
- Authorization and capture workflows.
- Webhook-based payment event handling.

Together, these technologies create a more intelligent and structured approach to freelance project collaboration and milestone-based payments.

---

## Future Scope

Potential future enhancements include:

- More advanced AI agents for project workflow automation.
- Improved AI-powered deliverable evaluation.
- Predictive project risk and delay detection.
- Automated milestone recommendations.
- Expanded payment options and currency support.
- Production deployment with live PayPal integration.
- Enhanced analytics and reporting.

---

## Project Demo

**Demo Video:** [Add your public YouTube demo link here]

**Live Demo:** [Add your hosted application URL here, if available]

**GitHub Repository:** [https://github.com/samruddhiS14/Aurevo](https://github.com/samruddhiS14/Aurevo)

---

## Team

**Project:** Aurevo AI

**Hackathon:** Build What's Next with PayPal and AI

**Contributors:** Add your team members and their GitHub profiles here.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Aurevo AI — Bringing Intelligence and Trust to Freelance Collaboration.**