import React, { useState, useEffect, useCallback, useMemo } from 'react'; // Import useMemo
import { FaUsers, FaKey, FaChartLine, FaCog } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuth(); // Get user info and token
  const [stats, setStats] = useState({ total_keys: 0, total_usage: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Memoize the Axios instance to prevent it from changing on every render
  const apiClient = useMemo(() => {
    // Create the base client configuration
    const client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        // Set Authorization header only if token exists
        ...(token && { Authorization: `Bearer ${token}` })
      }
    });

    // Add an interceptor to handle 401 Unauthorized errors (e.g., token expired)
    client.interceptors.response.use(
      response => response, // Pass through successful responses
      error => {
        // Check if the error is a 401 response
        if (error.response && error.response.status === 401) {
          setError("Session expired. Please log in again.");
          logout(); // Call the logout function from AuthContext
        }
        // Important: Return the rejected promise so downstream catches work
        return Promise.reject(error);
      }
    );

    return client; // Return the configured Axios client instance
  }, [token, logout]); // Dependencies: Recreate client if token or logout function changes

  // useCallback ensures fetchStats function identity is stable unless dependencies change
  const fetchStats = useCallback(async () => {
    if (!token) return; // Don't attempt fetch if there's no token

    setLoading(true);
    setError(null); // Clear previous errors before fetching
    try {
      // Use the memoized apiClient instance for the request
      const response = await apiClient.get('/api-keys/stats');
      setStats(response.data); // Update state with fetched stats
    } catch (err) {
      // Only set error if it's not a 401 (which is handled by the interceptor)
      if (err.response?.status !== 401) {
        setError('Failed to fetch statistics');
        console.error("Fetch stats error:", err); // Log the actual error
      }
    } finally {
      setLoading(false); // Ensure loading is set to false after fetch attempt
    }
  }, [token, apiClient, logout]); // Dependencies: Re-run if token, apiClient, or logout changes

  // useEffect to run fetchStats when the component mounts or fetchStats changes
  useEffect(() => {
    fetchStats();
  }, [fetchStats]); // Dependency array includes fetchStats

  return (
    <div className="dashboard">
      {/* Display username if available */}
      <h1>{user ? `${user.username}'s Dashboard` : 'API Management Dashboard'}</h1>

      <div className="quick-actions">
        {/* Navigation button to API Keys page */}
        <button onClick={() => navigate('/api-keys')}>
          <FaKey /> API Keys
        </button>
        {/* Button to manually refresh stats */}
         <button onClick={fetchStats} disabled={loading}>
           <FaChartLine /> Refresh Stats
         </button>
         {/* Other potential actions (commented out) */}
         {/* <button onClick={() => navigate('/settings')}><FaCog /> Settings</button> */}
         {/* <button onClick={() => navigate('/users')}><FaUsers /> Manage Users</button> */}
      </div>

      {/* Display loading indicator */}
      {loading && <p>Loading statistics...</p>}
      {/* Display error message if any */}
      {error && <div className="error" style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

      {/* Display stats grid only when not loading and no error */}
      {!loading && !error && (
        <div className="stats-grid">
          {/* Card for total API keys */}
          <div className="stat-card">
            <h3>Your API Keys</h3>
            <p>{stats.total_keys !== undefined ? stats.total_keys : 'N/A'}</p>
          </div>
          {/* Card for total API usage */}
          <div className="stat-card">
            <h3>Total Usage (Your Keys)</h3>
            <p>{stats.total_usage !== undefined ? stats.total_usage : 'N/A'}</p>
          </div>
          {/* Placeholder for other potential stats */}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
