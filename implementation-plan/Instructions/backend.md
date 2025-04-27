# GoldPriceNow Backend Implementation Guide

This document details the backend implementation for the GoldPriceNow application.  We'll use Python with FastAPI and SQLAlchemy for this implementation.

## 1. API Design

The backend will expose the following REST API endpoints:

**Authentication & User Management:**

* `/register`:  POST - Registers a new user. Requires `email` and `password`. Returns a success message or error details.
* `/login`: POST - Authenticates a user. Requires `email` and `password`. Returns a JWT token upon successful authentication.
* `/forgot-password`: POST - Initiates password reset. Requires `email`. Sends a password reset link via email.
* `/reset-password`: POST - Resets the password. Requires `token` (from password reset email) and `new_password`.
* `/dashboard`: GET - Protected endpoint for user dashboard data. Requires valid JWT. Returns user data, API key, and usage statistics.


**Gold Price Data:**

* `/api/v1/goldprice`: GET - Returns the latest gold price in JSON format. Requires API key in the `X-API-Key` header.


**Admin Panel (requires admin authentication, separate endpoint not specified):**

* Endpoints for managing users, viewing API usage statistics, banning/suspending users, and managing subscriptions.  These will likely be accessed via a separate admin interface and not via REST API calls directly.


**Payment Integration (Stripe):**

* `/create-checkout-session`: POST - Creates a Stripe checkout session for premium subscription.  Returns Stripe session ID.  This is not publicly accessible, likely hidden behind an internal route for interaction with the frontend.
* Webhook endpoint (not directly exposed as a public API endpoint but rather configured within Stripe): Receives subscription updates (created, cancelled, updated) from Stripe.

## 2. Data Models

The PostgreSQL database schema will consist of the following tables:

* **`users`**:
    * `id` (SERIAL PRIMARY KEY): User ID.
    * `email` (VARCHAR UNIQUE NOT NULL): User email.
    * `password_hash` (VARCHAR NOT NULL):  Hashed password using bcrypt.
    * `api_key` (UUID NOT NULL):  Unique API key for each user.
    * `plan` (VARCHAR NOT NULL DEFAULT 'free'): User's subscription plan ('free' or 'premium').
    * `is_verified` (BOOLEAN DEFAULT FALSE): Email verification status.
    * `is_active` (BOOLEAN DEFAULT TRUE): Account activation status.
    * `created_at` (TIMESTAMP WITH TIME ZONE DEFAULT NOW()): Account creation timestamp.
    * `updated_at` (TIMESTAMP WITH TIME ZONE DEFAULT NOW()): Account last update timestamp.

* **`gold_prices`**:
    * `id` (SERIAL PRIMARY KEY): Gold price entry ID.
    * `price` (NUMERIC NOT NULL): Gold price.
    * `timestamp` (TIMESTAMP WITH TIME ZONE NOT NULL): Timestamp of the price.
    * `source` (VARCHAR NOT NULL): Source of the gold price (e.g., "Yahoo Finance", "Kitco").

* **`api_usage`**:
    * `id` (SERIAL PRIMARY KEY): API usage record ID.
    * `user_id` (INTEGER NOT NULL REFERENCES users(id)): User who made the request.
    * `request_count` (INTEGER NOT NULL): Number of requests made.
    * `date` (DATE NOT NULL): Date of the requests.


* **`subscriptions`**:
    * `id` (SERIAL PRIMARY KEY): Subscription ID.
    * `user_id` (INTEGER NOT NULL REFERENCES users(id)): User associated with the subscription.
    * `stripe_subscription_id` (VARCHAR NOT NULL): Stripe subscription ID.
    * `status` (VARCHAR NOT NULL): Subscription status (e.g., "active", "cancelled", "trialing").
    * `started_at` (TIMESTAMP WITH TIME ZONE): Subscription start timestamp.
    * `ends_at` (TIMESTAMP WITH TIME ZONE): Subscription end timestamp (if applicable).


## 3. Business Logic

* **User Registration and Authentication:**  Standard user registration and login with email verification and bcrypt password hashing. JWT will be used for API authentication and session cookies for the dashboard.

* **Gold Price Fetcher:** This will be a background task (Celery or similar) running periodically (e.g., every 5 minutes). It will attempt to fetch data from Yahoo Finance's API first. If that fails, it will fall back to web scraping Kitco.com.  The result will be stored in the `gold_prices` table only if the price has changed since the last update.

* **API Key Authentication:** A middleware function will validate the API key passed in the `X-API-Key` header for each request to `/api/v1/goldprice`.  It will check the key's validity, the user's plan, and enforce rate limits.

* **Rate Limiting:**  The rate limit manager will track API requests per user per day using the `api_usage` table.  If the limit is exceeded, a 429 Too Many Requests response will be returned.

* **Payment Processing (Stripe):**  Integration with Stripe API for handling premium subscription creation, updates, and cancellations.  Webhooks will manage subscription status changes.

* **Admin Panel Logic:** The admin panel will provide functions to manage users, subscriptions, and API usage data.  This will involve database queries and potentially additional security checks.


## 4. Security Considerations

* **Password Security:**  Passwords will be securely hashed using bcrypt before storage.

* **API Key Security:** API keys will be generated using UUIDs and stored securely.  Regular rotation of API keys should be considered.

* **SQL Injection:** SQLAlchemy's ORM will be used to prevent SQL injection vulnerabilities.  All database interactions will be parameterized queries.

* **Cross-Site Request Forgery (CSRF):** CSRF protection will be implemented for forms (e.g., using double submit cookies).

* **HTTPS:**  HTTPS will be enforced across the entire application.  Let's Encrypt will be used for free SSL certificates.

* **Input Validation:** All user inputs will be validated to prevent invalid data from being processed.

* **Authentication:** JWT will be used for API authentication and sessions for the dashboard.  JWTs should have short expiration times and be properly secured.

* **Authorization:**  Access control will be implemented to restrict access to certain endpoints based on user roles (e.g., only admins can access the admin panel).


This backend implementation guide provides a solid foundation for developing the GoldPriceNow application.  Further details, such as error handling, logging, and comprehensive testing, will be incorporated during the development process.
