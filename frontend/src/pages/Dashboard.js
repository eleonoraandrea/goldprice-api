import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FaUsers, FaKey, FaChartLine, FaCog, FaCoins } from 'react-icons/fa'; // Added FaCoins
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuth();
  const [stats, setStats] = useState({ total_keys: 0, total_usage: 0 });
  const [prices, setPrices] = useState({ gold: null, silver: null, palladium: null }); // Combined price state
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingPrices, setLoadingPrices] = useState(false);
  const [error, setError] = useState(null);
  const [priceErrors, setPriceErrors] = useState({}); // State for specific price errors from API

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
    if (!token) return;

    setLoadingStats(true); // Use specific loading state
    setError(null);
    try {
      const response = await apiClient.get('/api-keys/stats');
      setStats(response.data);
    } catch (err) {
      if (err.response?.status !== 401) {
        setError('Failed to fetch statistics');
        console.error("Fetch stats error:", err);
      }
    } finally {
      setLoadingStats(false); // Use specific loading state
    }
  }, [token, apiClient]); // Removed logout dependency as interceptor handles it

  // Function to fetch prices from the new dashboard endpoint
  const fetchPrices = useCallback(async () => {
    if (!token) return;

    setLoadingPrices(true);
    setError(null); // Clear general errors
    setPriceErrors({}); // Clear specific price errors
    setPrices({ gold: null, silver: null, palladium: null }); // Reset prices

    try {
      const response = await apiClient.get('/dashboard/prices');
      console.log("API Response - Dashboard Prices:", response.data); // Log the combined response

      // Update state with fetched prices, checking for existence in the response
      setPrices({
          gold: response.data?.prices?.gold || null,
          silver: response.data?.prices?.silver || null,
          palladium: response.data?.prices?.palladium || null,
      });

      // Set specific errors if the API reported them
      if (response.data?.errors && Object.keys(response.data.errors).length > 0) {
          setPriceErrors(response.data.errors);
          // Optionally set a general error message too
          setError('Failed to fetch some commodity prices. See details below.');
      }

    } catch (err) {
       // Handle general fetch errors (like network issues or 5xx errors)
       if (err.response?.status !== 401) { // 401 is handled by interceptor
          setError('An unexpected error occurred while fetching prices.');
          console.error("Fetch dashboard prices error:", err);
       }
    } finally {
      setLoadingPrices(false); // Use specific loading state
    }
  }, [token, apiClient]); // Dependencies

  // useEffect to run fetches when the component mounts or dependencies change
  useEffect(() => {
    fetchStats();
    fetchPrices();
  }, [fetchStats, fetchPrices]); // Include both fetch functions

  return (
    <div className="dashboard">
      {/* Display username if available */}
      <h1>{user ? `${user.username}'s Dashboard` : 'API Management Dashboard'}</h1>

      <div className="quick-actions">
        {/* Navigation button to API Keys page */}
        <button onClick={() => navigate('/api-keys')}>
          <FaKey /> API Keys
        </button>
         {/* Button to manually refresh stats and prices */}
         <button onClick={() => { fetchStats(); fetchPrices(); }} disabled={loadingStats || loadingPrices}>
           <FaChartLine /> Refresh Data
         </button>
         {/* Other potential actions (commented out) */}
         {/* <button onClick={() => navigate('/settings')}><FaCog /> Settings</button> */}
         {/* <button onClick={() => navigate('/users')}><FaUsers /> Manage Users</button> */}
      </div>

       {/* Display loading indicators */}
       {(loadingStats || loadingPrices) && <p>Loading data...</p>}
       {/* Display error message if any */}
       {error && <div className="error" style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

       {/* Display stats grid */}
       <div className="stats-grid">
         {/* --- Stats Cards --- */}
         {!loadingStats && ( // Show stats cards only when stats are not loading
           <>
             <div className="stat-card">
               <h3>Your API Keys</h3>
               <p>{stats.total_keys !== undefined ? stats.total_keys : 'N/A'}</p>
             </div>
             <div className="stat-card">
               <h3>Total Usage (Your Keys)</h3>
               <p>{stats.total_usage !== undefined ? stats.total_usage : 'N/A'}</p>
             </div>
           </>
         )}
         {loadingStats && ( // Show placeholders while stats loading
            <>
              <div className="stat-card placeholder"><h3>Your API Keys</h3><p>Loading...</p></div>
              <div className="stat-card placeholder"><h3>Total Usage (Your Keys)</h3><p>Loading...</p></div>
            </>
         )}

         {/* --- Price Cards --- */}
         {!loadingPrices && ( // Show price cards only when prices are not loading
           <>
             {/* Gold Price Card */}
             <div className="stat-card">
               <h3><FaCoins /> Gold Price</h3>
               {priceErrors.gold ? <p className="error-text">{priceErrors.gold}</p> : <p>{(prices.gold && typeof prices.gold.price === 'number') ? `$${prices.gold.price.toFixed(2)} USD` : 'N/A'}</p>}
               <small>Unit: {prices.gold?.unit || 'N/A'}</small>
             </div>
             {/* Silver Price Card */}
             <div className="stat-card">
               <h3><FaCoins /> Silver Price</h3>
                {priceErrors.silver ? <p className="error-text">{priceErrors.silver}</p> : <p>{(prices.silver && typeof prices.silver.price === 'number') ? `$${prices.silver.price.toFixed(2)} USD` : 'N/A'}</p>}
               <small>Unit: {prices.silver?.unit || 'N/A'}</small>
             </div>
             {/* Palladium Price Card */}
             <div className="stat-card">
               <h3><FaCoins /> Palladium Price</h3>
               {priceErrors.palladium ? <p className="error-text">{priceErrors.palladium}</p> : <p>{(prices.palladium && typeof prices.palladium.price === 'number') ? `$${prices.palladium.price.toFixed(2)} USD` : 'N/A'}</p>}
               <small>Unit: {prices.palladium?.unit || 'N/A'}</small>
             </div>
           </>
         )}
         {loadingPrices && ( // Show placeholders while prices loading
            <>
              <div className="stat-card placeholder"><h3><FaCoins /> Gold Price</h3><p>Loading...</p></div>
              <div className="stat-card placeholder"><h3><FaCoins /> Silver Price</h3><p>Loading...</p></div>
              <div className="stat-card placeholder"><h3><FaCoins /> Palladium Price</h3><p>Loading...</p></div>
            </>
         )}
       </div>
     </div>
   );
}

export default Dashboard;
