# FinPay React Frontend

React.js web dashboard for the FinPay platform, built with Vite and React. Connects to the Django backend REST API (`http://127.0.0.1:8000/api/dashboard/`) to display live financial intelligence data.

---

## Setup & Run

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

The application will run locally at `http://localhost:5173`.

---

## Features

- **Fintech Dark Design**: Dark mode palette (`#0a0e17`) with Google Font Inter and card hover animations.
- **Dynamic API Integration**: Fetches total customer count, account count, transaction count, and Arjun Sharma's account balance dynamically from Django REST API (`http://127.0.0.1:8000/api/dashboard/`).
- **Proxy Configuration**: `vite.config.js` proxies `/api` requests to Django backend at `http://127.0.0.1:8000`.
