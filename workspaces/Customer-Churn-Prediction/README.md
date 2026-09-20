# 🛡️ ChurnShield AI — Live MongoDB Customer Churn Prediction Platform

Full-stack customer churn prediction website for e-commerce using **React + Vite + Tailwind CSS**, **Flask API**, **JWT login**, **MongoDB Atlas**, and **XGBoost-compatible churn scoring**.

This corrected version removes demo/offline database behavior. Dashboard, upload, risk analysis, predictions, reports, settings, and login are connected to live MongoDB.

---

## ✅ Fixed in this ZIP

- Removed `demo-token` login access.
- Removed frontend demo fallback customer arrays.
- Removed backend static demo dashboard/risk datasets.
- Added required live MongoDB connection using `MONGO_URI`.
- Added real MongoDB collections: `users`, `customers`, `predictions`, `datasets`, `settings`.
- CSV/Excel upload now stores customer rows directly in MongoDB.
- Dashboard, Risk Analysis, Retention, Reports, Settings, and Prediction History read live MongoDB data.
- Report download now uses authenticated Axios blob download.
- Website UI/design is kept the same.
- Settings page sub-options now work with real backend APIs: Profile, Notifications, Model Config, Password Update, API Key Reveal, and API Key Regenerate.
- Frontend pages are lazy-loaded with React Suspense for faster initial loading.
- Backend dashboard/risk/report customer loading uses a short MongoDB cache and query limit for better speed on large customer collections.

---

## 📁 Project Structure

```text
churnshield_pro/
├── frontend/
│   ├── src/pages/
│   ├── src/components/
│   ├── src/services/api.js
│   ├── .env
│   ├── .env.example
│   └── package.json
└── backend/
    ├── app.py
    ├── auth.py
    ├── database.py
    ├── ml_service.py
    ├── train_model.py
    ├── import_customers.py
    ├── .env
    ├── .env.example
    ├── requirements.txt
    └── sample_data/customer_churn_sample.csv
```

---

## 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend starts at:

```text
http://localhost:5000
```

Check API health:

```text
http://localhost:5000/api/health
```

Expected MongoDB status:

```json
{"mongodb":"connected"}
```

---

## 2. MongoDB Atlas Environment

`backend/.env` is already configured with your provided database:

```env
MONGO_URI=mongodb+srv://avantikasundaram06_db_user:Shankar54321@churn-predection.4yahxul.mongodb.net/churnshield_db?retryWrites=true&w=majority&appName=Churn-Predection
MONGO_DB_NAME=churnshield_db
FRONTEND_URL=http://localhost:5173
ADMIN_EMAIL=admin@churnshield.ai
ADMIN_PASSWORD=Admin@123
```

Important MongoDB Atlas setup:

1. Go to MongoDB Atlas → **Network Access**.
2. Add your current IP address.
3. For testing only, you can add `0.0.0.0/0`.
4. Go to **Database Access** and confirm this user has read/write access.

---

## 3. Import 500 Indian Customers CSV to MongoDB

The included sample file has 500 Indian customer records:

```text
backend/sample_data/customer_churn_sample.csv
```

Import it directly into MongoDB:

```bash
cd backend
venv\Scripts\activate
python import_customers.py sample_data/customer_churn_sample.csv
```

MongoDB collection used:

```text
churnshield_db.customers
```

You can also upload the CSV from the website **Dataset Upload** page.

---

## 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at:

```text
http://localhost:5173
```

`frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:5000
```

---

## 5. Login

The backend creates these real MongoDB users automatically in the `users` collection during startup/login:

| Role | Email | Password |
|---|---|---|
| Admin | admin@churnshield.ai | Admin@123 |
| Data Analyst | analyst@churnshield.ai | Analyst@123 |

---

## 6. Required CSV Columns

```text
Customer ID, Age, Gender, Location, Total Orders, Last Purchase Date,
Average Order Value, Cart Abandonment Rate (%), Website Visits,
Customer Rating, Payment Method, Return Count, Support Tickets, Churn Status
```

---

## 7. API Endpoints

| Method | Endpoint | Live MongoDB Process |
|---|---|---|
| GET | `/api/health` | Checks API + MongoDB status |
| POST | `/api/auth/login` | Reads/creates users in MongoDB |
| GET | `/api/dashboard` | Reads customers + predictions |
| POST | `/api/upload` | Saves CSV/Excel rows to customers collection |
| POST | `/api/predict` | Saves prediction result to predictions collection |
| GET | `/api/predict/history` | Reads prediction history |
| GET | `/api/risk-analysis` | Reads customer risk list |
| GET | `/api/model-performance` | Reads model metrics/feature importance |
| GET | `/api/retention` | Builds retention plan from customers |
| GET | `/api/reports/{type}` | Exports live customer/report CSV |
| GET | `/api/settings` | Reads settings/user profile |
| PUT | `/api/settings` | Saves profile/notification/model settings in MongoDB |
| POST | `/api/settings/password` | Verifies current password and saves new password hash |
| GET | `/api/settings/api-key` | Reveals saved API key for the logged-in user |
| POST | `/api/settings/api-key/regenerate` | Generates and saves a new API key |

---

## 8. Vercel / Deployment Environment

### Backend Environment Variables

Add these in Vercel backend project:

```env
MONGO_URI=mongodb+srv://avantikasundaram06_db_user:Shankar54321@churn-predection.4yahxul.mongodb.net/churnshield_db?retryWrites=true&w=majority&appName=Churn-Predection
MONGO_DB_NAME=churnshield_db
JWT_SECRET_KEY=your-production-secret
FRONTEND_URL=https://your-frontend-url.vercel.app
ADMIN_EMAIL=admin@churnshield.ai
ADMIN_PASSWORD=Admin@123
```

### Frontend Environment Variable

Add this in Vercel frontend project:

```env
VITE_API_BASE_URL=https://your-backend-url.vercel.app
```

Then redeploy frontend and backend.

---

## 9. Common Fixes

### MongoDB URI error

Correct format must start with:

```text
mongodb+srv://
```

### Login not working

Check:

- Backend is running.
- `/api/health` shows `mongodb: connected`.
- Atlas Network Access allows your IP.
- `FRONTEND_URL` matches frontend URL.
- Frontend `VITE_API_BASE_URL` matches backend URL.

### Dashboard showing zero customers

Import CSV:

```bash
python import_customers.py sample_data/customer_churn_sample.csv
```

or upload the CSV in the website.


---

## 10. Speed / Loading Improvements Added

### Frontend

- `src/App.jsx` now uses `React.lazy()` and `Suspense`, so pages load only when opened.
- Invalid-login `401` no longer reloads the page immediately; only expired logged-in sessions are cleared.
- API timeout is reduced to 20 seconds to fail faster on network/backend issues.

### Backend

- Customer-heavy pages use `CUSTOMER_QUERY_LIMIT` and `CUSTOMER_CACHE_TTL_SECONDS`.
- Default: latest 5,000 customer records with a 15-second cache window.
- Upload/upsert invalidates the customer cache automatically.

Optional backend `.env` speed values:

```env
CUSTOMER_QUERY_LIMIT=5000
CUSTOMER_CACHE_TTL_SECONDS=15
```

---

## 11. Settings Page Working Process

1. Login first.
2. Open **Settings**.
3. Profile / Notifications / Model Config tabs use `GET /api/settings` and `PUT /api/settings`.
4. Security → **Update Password** uses `POST /api/settings/password`.
5. Security → **Reveal** uses `GET /api/settings/api-key`.
6. Security → **Regenerate** uses `POST /api/settings/api-key/regenerate`.

All saved settings are stored in the MongoDB `settings` collection with key `app_settings`.
