## 🚀 Deployment

### Cloud provider

The API is deployed on **Fly.io**, using a containerized FastAPI application and a managed PostgreSQL database (Neon).

Fly.io was chosen because it provides:

* Simple Docker-based deployments
* Built-in HTTPS (Let’s Encrypt)
* Secure secret management

---

## 🔗 Accessing the deployment

**Base URL**

```
https://inbound-carrier-sales-demo.fly.dev
```

**Dashboard UI**

```
https://inbound-carrier-sales-demo.fly.dev/dashboard
```

**Health check**

```
GET /health
```

**Metrics API (examples)**

```
GET /v1/metrics/dashboard/overview
GET /v1/metrics/dashboard/calls
GET /v1/metrics/dashboard/calls/{call_id}
```

**Webhook endpoint**

```
POST /webhooks/happyrobot/call-ended
```

All secured endpoints require an API key via header:

```
x-api-key: demo-key
```

---

## ♻️ Reproducing the deployment (manual steps)

### Prerequisites

* Docker
* Fly.io CLI (`flyctl`)
* PostgreSQL database (Neon or equivalent)
* Python 3.12+
* FMCSA API key (free registration at https://www.fmcsa.dot.gov/registration)

---

### 1. Clone the repository

```bash
git clone <repository-url>
cd inbound-carrier-sales-demo
```

---

### 2. Create a PostgreSQL database

Create a PostgreSQL database using **Neon** (or any managed Postgres provider) and copy the connection string:

```
postgresql://USER:PASSWORD@HOST/DB?sslmode=require
```

---

### 3. Deploy to Fly.io

Authenticate:

```bash
fly auth login
```

Initialize the app (first time only):

```bash
fly launch
```

Set secrets:

```bash
fly secrets set \
  API_KEYS=demo-key \
  DATABASE_URL="postgresql://USER:PASSWORD@HOST/DB?sslmode=require" \
  FMCSA_API_KEY="your-fmcsa-api-key"
```

Deploy:

```bash
fly deploy
```

---

### 4. Verify deployment

```bash
curl https://inbound-carrier-sales-demo.fly.dev/health
```

Expected response:

```json
{"status":"ok"}
```

---

## 🔐 HTTPS & Security

* HTTPS is automatically provided by Fly.io using Let’s Encrypt
* API access is protected via API key authentication
* Database credentials are stored as encrypted Fly.io secrets
* No sensitive values are committed to the repository
