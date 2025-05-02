import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext'; // Import useAuth
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import ApiKeys from './pages/ApiKeys';
import LoginPage from './pages/Login'; // Import LoginPage
import RegisterPage from './pages/Register'; // Import RegisterPage
import Navbar from './components/Navbar'; // Import Navbar
import './App.css';

// Component to protect routes
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    // Optional: Show a loading spinner while checking auth status
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to when they were redirected. This allows us to send them
    // along to that page after they login, which is a nicer user experience
    // than dropping them off on the home page.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}


function App() {
  return (
    <BrowserRouter>
      <Navbar /> {/* Add Navbar here, outside Routes but inside BrowserRouter */}
      <div className="main-content"> {/* Optional: Add a container for page content */}
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/users" // Consider if this page is still needed or should be admin-only
          element={
            <ProtectedRoute>
              <Users />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <ApiKeys />
            </ProtectedRoute>
          }
        />

         {/* Optional: Redirect root to dashboard if logged in, or login if not */}
         {/* This might conflict with the protected route above, adjust as needed */}
         {/* <Route path="/" element={<Navigate to={useAuth().isAuthenticated ? "/dashboard" : "/login"} replace />} /> */}

         {/* Catch-all or 404 route */}
          <Route path="*" element={<div>404 Not Found</div>} />

        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
