# GoldPriceNow: Product Requirements Document

**1. Introduction**

This document outlines the requirements for GoldPriceNow, a full-stack web application providing real-time gold price data via an API and a user dashboard.  The application will fetch live gold prices from Yahoo Finance API (primary) and Kitco.com (fallback), store them in a PostgreSQL database, and offer a freemium model with API key access for users.  The application will include user authentication, a dashboard displaying gold price and API usage, and an admin panel for managing users and subscriptions.


**2. Product Specifications**

**2.1 Features:**

* **Real-time Gold Price Fetching:** The application will fetch the current gold price every X seconds/minutes (specific interval to be determined). It will prioritize the Yahoo Finance API; if unavailable, it will scrape Kitco.com.  The price, timestamp, and source will be stored in the PostgreSQL database.  Only updated prices will be saved.

* **User Management:** Users can register and log in securely using bcrypt password hashing and JWT for API authentication, and session cookies for dashboard access. Email verification is recommended but optional.  A forgotten/reset password feature is required.

* **Dashboard:**  Registered users will have access to a dashboard displaying:
    * Current gold price.
    * Last update time.
    * API key (with copy functionality).
    * API usage statistics (requests today/this month).
    * Current subscription plan.

* **API Endpoint (`/api/v1/goldprice`):** This endpoint returns the latest gold price in JSON format: `{"price": 2365.45, "currency": "USD", "timestamp": "2025-04-27T14:55:00Z", "source": "Yahoo Finance"}`.  Authentication requires an API key in the request headers.  Rate limits are applied based on the user's subscription plan.

* **Premium Plans:** A freemium model will be implemented with Stripe for payment processing.
    * **Free Plan:**  Limited API requests per day (quantity to be determined).
    * **Premium Plan:** Unlimited or higher rate limits (quantity to be determined).  (Potential future addition: historical data access).

* **Admin Panel:**  An admin panel will provide functionalities for:
    * Viewing all users.
    * Viewing API usage statistics.
    * Banning/suspending accounts.
    * Managing premium subscriptions.


**2.2 Data Model (PostgreSQL):**

* `users`: (id, email, password_hash, api_key, plan, is_verified, is_active, created_at, updated_at)
* `gold_prices`: (id, price, timestamp, source)
* `api_usage`: (id, user_id, request_count, date)
* `subscriptions`: (id, user_id, stripe_subscription_id, status, started_at, ends_at)


**3. User Experience**

* **Registration/Login:**  Clear and intuitive registration and login forms.
* **Dashboard:** User-friendly dashboard displaying key information clearly and concisely.  API key should be easily copied.
* **API Usage:**  Dashboard displays API usage statistics in a readily understandable format.
* **Admin Panel:** Admin panel will be intuitive and provide clear controls for managing users and subscriptions.
* **Landing Page:**  Attractive landing page encouraging user signup.
* **Responsive Design:**  The application will be responsive across all devices (mobile, tablet, desktop).


**4. Implementation Requirements**

**4.1 Technology Stack:**

* **Backend:** Python (FastAPI or Flask) / Node.js (Express)
* **Frontend:** React.js with Tailwind CSS / Next.js
* **Database:** PostgreSQL
* **Authentication:** JWT (for API) + session (for dashboard)
* **Scraper/Fetcher:** `requests` + `BeautifulSoup` (Kitco), Yahoo Finance API or `yfinance` library.
* **Payment:** Stripe API
* **Hosting:** VPS or cloud provider (AWS, Linode, Hetzner)
* **SSL:** Let's Encrypt

**4.2 Backend Specifics:**

* REST API endpoints: `/register`, `/login`, `/forgot-password`, `/reset-password`, `/dashboard`, `/api/v1/goldprice`.
* Background service for gold price fetching (Celery, cronjobs).
* API key authentication middleware and rate limit manager.
* Stripe integration for handling payments and subscription webhooks.

**4.3 Frontend Specifics:**

* Landing page with sign-up/login call to actions.
* Authentication pages (sign up, login, password reset).
* User dashboard displaying gold price, API key, and usage statistics.
* Admin dashboard (access controlled).

**4.4 Security Requirements:**

* Password hashing (bcrypt or Argon2).
* SQL injection protection (using an ORM).
* CSRF protection.
* Secure API key generation.
* HTTPS enforcement.


This PRD outlines the core features and requirements.  Further details, such as specific API request limits and design specifications, will be addressed in subsequent documentation.
