# GoldPriceNow Requirements Document

## 1. Project Overview

This document outlines the requirements for the development of "GoldPriceNow," a full-stack web application providing real-time gold price data via an API and a user dashboard.  The application will fetch live gold prices from Yahoo Finance API (primary) or Kitco.com (fallback), store this data in a PostgreSQL database, and offer a freemium subscription model with API key access.  A robust user management system, including registration, login, password reset, and email verification, will be implemented.  The backend will be built using either Python (FastAPI or Flask) or Node.js (Express), while the frontend will leverage React.js with Tailwind CSS or Next.js.  Stripe will be integrated for payment processing.

## 2. Functional Requirements

**2.1.  Live Gold Price Fetching:**

*   Fetch live gold prices every X seconds/minutes (the specific interval, X, needs to be defined).
*   Utilize the Yahoo Finance API as the primary source.
*   Implement a fallback mechanism to scrape and parse Kitco.com if the Yahoo Finance API fails.
*   Store the price, timestamp, and source (Yahoo Finance or Kitco.com) in the PostgreSQL database.
*   Only insert a new price into the database if the price has changed.

**2.2. User Management:**

*   Secure user registration with email verification (optional but recommended).
*   Secure user login with bcrypt password hashing.  Authentication method using JWT for the API and sessions for the dashboard.
*   Forgotten/reset password functionality.
*   API key generation and management for each user.

**2.3. Dashboard (User):**

*   Display the current gold price.
*   Display the last update timestamp.
*   Display the user's API key with a copy button.
*   Display API usage statistics (requests today/this month).
*   Display the user's current subscription plan (Free or Premium).  Allow upgrade to premium plan.


**2.4. API Endpoint (`/api/v1/goldprice`):**

*   Require API key authentication via headers.
*   Return JSON data in the following format:
    ```json
    {
      "price": 2365.45,
      "currency": "USD",
      "timestamp": "2025-04-27T14:55:00Z",
      "source": "Yahoo Finance"
    }
    ```
*   Implement rate limiting based on the user's subscription plan (e.g., 100 requests/day for free users).

**2.5. Premium Plans:**

*   Integration with Stripe for payment processing.
*   At least two subscription plans:
    *   Free Plan (default, with usage limits)
    *   Premium Plan (unlimited or higher rate limits; potential additional features like historical data access).

**2.6. Admin Panel:**

*   View all users and their details.
*   View API usage statistics for all users.
*   Ability to ban/suspend user accounts.
*   Manage premium subscriptions.


## 3. Non-Functional Requirements

*   **Performance:** The application should provide real-time gold prices with minimal latency.  The price fetching service should run reliably and efficiently.
*   **Scalability:** The application should be designed to handle a growing number of users and API requests.  Background worker processes (e.g., Celery or cronjobs) are recommended for price fetching.  Caching (e.g., Redis) is a desirable enhancement for faster API responses.
*   **Security:**  The application must protect against SQL injection, CSRF attacks, and unauthorized access.  Password hashing using bcrypt is required. HTTPS must be used. API keys must be securely generated and managed.
*   **Reliability:** The application should be highly available and fault-tolerant.  Robust error handling and logging mechanisms are required.  A fallback mechanism for price fetching is a requirement.
*   **Usability:** The application should have a user-friendly interface that is easy to navigate and use. Responsive design across multiple devices is required.


## 4. Dependencies and Constraints

*   **Backend Technologies:** Python (FastAPI or Flask) or Node.js (Express).
*   **Frontend Technologies:** React.js with Tailwind CSS or Next.js.
*   **Database:** PostgreSQL.
*   **Payment Gateway:** Stripe API.
*   **Data Sources:** Yahoo Finance API (primary), Kitco.com (fallback).  Use of the `yfinance` library is recommended for Yahoo Finance data. `requests` and `BeautifulSoup` are to be used for Kitco scraping.
*   **Authentication:** JWT for API, sessions for the dashboard.
*   **Hosting:** VPS or cloud provider (AWS, Linode, Hetzner).
*   **SSL:** Let's Encrypt (or equivalent).  HTTPS is mandatory.
