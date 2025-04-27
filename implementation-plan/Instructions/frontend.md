## GoldPriceNow Frontend Implementation Guide

This guide details the frontend implementation for the GoldPriceNow application using React.js and Tailwind CSS.  We'll focus on the core features, omitting optional extras.

**1. Component Structure:**

The application will be structured using functional components and React hooks.  We'll leverage Tailwind CSS for styling.

* **App.js:** The main application component, responsible for routing and authentication context.
* **Layout.js:**  A reusable layout component wrapping all pages, containing header (logo, navigation), and footer (copyright, links).
* **Pages:**
    * **LandingPage.js:** Hero section, features, pricing table, signup/login CTA.
    * **AuthPages.js:**  Handles signup, login, password reset, and email verification.  This could be further broken down into individual components (SignupForm.js, LoginForm.js, etc.).
    * **Dashboard.js:** Displays gold price, last update, API key, API usage statistics, and plan information.  This could be broken down into smaller components (GoldPriceDisplay.js, ApiKeyDisplay.js, UsageChart.js, PlanDetails.js).
    * **AdminDashboard.js:** (Protected route) Displays user management, API usage overview, and account controls.  Components: UserList.js, ApiUsageTable.js, AccountControls.js.
* **UI Components:**
    * **Button.js:**  A reusable button component with variations for styles (primary, secondary, etc.).
    * **Input.js:** Reusable input field component for forms.
    * **Chart.js:**  Component to display API usage charts (bar chart for daily usage, line chart for monthly usage).  Could use a charting library like Recharts or Chart.js.
    * **LoadingIndicator.js:** Displays a loading spinner while fetching data.
    * **ErrorBoundary.js:**  Handles and displays errors gracefully.


**2. State Management:**

We'll use React's Context API for authentication and user data management.  For other data, we'll use the `useState` hook within the relevant components.

* **AuthContext:**  Manages user authentication status (logged in/out), API key, user plan, and potentially user profile data.  Provides methods for login, logout, and other authentication-related actions.
* **Dashboard Context:** Manages the gold price data, last update time, and API usage statistics fetched from the backend API.
* **Admin Context:** (Only for AdminDashboard.js)  Manages the list of users and their API usage data.

Data fetching will be handled using `useEffect` hooks in components requiring data updates, making API calls to the backend.  For example, the `Dashboard.js` component will use `useEffect` to fetch the latest gold price and API usage statistics when the component mounts and potentially at regular intervals (e.g., every minute).

**3. UI/UX Guidelines:**

* **Visual Style:** Clean, modern design using Tailwind CSS.  Consider a dark mode option.
* **Color Palette:**  Use a consistent color scheme, possibly incorporating gold accents.
* **Typography:** Choose a clear and legible font.
* **Responsiveness:**  All pages must be responsive and work seamlessly across different devices (desktops, tablets, and mobile).
* **Accessibility:** Adhere to WCAG guidelines for accessibility.
* **User Experience:**  Ensure a smooth and intuitive user flow for all features.  Provide clear feedback to the user during actions (e.g., loading indicators, success/error messages).

**4. Page Layouts:**

* **Landing Page:**  A hero section showcasing the app's main features and benefits, followed by a section detailing the key features with compelling visuals, and finally a pricing section with clear call-to-actions for signup and login.
* **Auth Pages:** Simple forms for signup and login with clear instructions and error handling. Password reset flow should be straightforward and include email verification.
* **User Dashboard:**  A clear and concise display of the current gold price, its source and last updated time, API key display (with copy button), API usage chart (daily and monthly), current subscription plan and options to upgrade if applicable.
* **Admin Dashboard:** A table showing a list of users with their details, including API usage statistics.  Options to ban/suspend users and manage subscriptions should be clearly presented.


This frontend implementation guide provides a solid foundation for building the GoldPriceNow application.  Remember to thoroughly test and optimize the application for performance and security.  Specific component implementations and detailed styling using Tailwind CSS will require further development.
