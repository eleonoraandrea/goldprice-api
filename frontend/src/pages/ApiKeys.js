import React, { useState, useEffect, useCallback, useMemo } from 'react'; // Import useMemo
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import './ApiKeys.css'; // Import CSS for styling

function ApiKeys() {
  const [apiKeys, setApiKeys] = useState([]);
  const [copiedKey, setCopiedKey] = useState(null); // State to track which key's snippet was copied
  const [copiedLang, setCopiedLang] = useState(null); // State to track which language was copied
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { token, logout } = useAuth(); // Get token and logout function

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

  // useCallback ensures fetchKeys function identity is stable unless dependencies change
  const fetchKeys = useCallback(async () => {
    if (!token) return; // Don't attempt fetch if there's no token

    setLoading(true);
    setError(null); // Clear previous errors before fetching
    try {
      // Use the memoized apiClient instance for the request
      const response = await apiClient.get('/api-keys');
      setApiKeys(response.data); // Update state with fetched keys
    } catch (err) {
      // Only set error if it's not a 401 (which is handled by the interceptor)
      if (err.response?.status !== 401) {
        setError('Failed to fetch API keys');
        console.error("Fetch keys error:", err); // Log the actual error
      }
    } finally {
      setLoading(false); // Ensure loading is set to false after fetch attempt
    }
  }, [token, apiClient, logout]); // Dependencies: Re-run if token, apiClient, or logout changes

  // useEffect to run fetchKeys when the component mounts or fetchKeys changes
  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]); // Dependency array includes fetchKeys

  // Function to create a new API key
  const createKey = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use the memoized apiClient instance for the POST request
      const response = await apiClient.post('/api-keys');
      // Add the newly created key to the local state
      setApiKeys(prevKeys => [...prevKeys, response.data]);
    } catch (err) {
      // Only set error if it's not a 401
       if (err.response?.status !== 401) {
         setError(err.response?.data?.detail || 'Failed to create API key');
         console.error("Create key error:", err);
       }
    } finally {
      setLoading(false);
    }
  };

  // Function to toggle the active status of a key
  const toggleKey = async (key) => {
    setError(null);
    try {
      // Use the memoized apiClient instance for the POST request
      await apiClient.post(`/api-keys/${key}/toggle`);
      // Update local state for immediate UI feedback
      setApiKeys(prevKeys =>
        prevKeys.map(k =>
          k.key === key ? { ...k, is_active: !k.is_active } : k
        )
      );
    } catch (err) {
      // Only set error if it's not a 401
       if (err.response?.status !== 401) {
         setError('Failed to toggle key status');
         console.error("Toggle key error:", err);
       }
    }
  };

  // Function to revoke (delete) a key
  const revokeKey = async (key) => {
    setError(null);
    // Optional: Add confirmation dialog
    // if (!window.confirm("Are you sure you want to revoke this key? This cannot be undone.")) {
    //   return;
    // }
    try {
      // Use the memoized apiClient instance for the DELETE request
      await apiClient.delete(`/api-keys/${key}`);
      // Remove the key from local state for immediate UI feedback
      setApiKeys(prevKeys => prevKeys.filter(k => k.key !== key));
    } catch (err) {
      // Only set error if it's not a 401
       if (err.response?.status !== 401) {
         setError('Failed to revoke key');
         console.error("Revoke key error:", err);
       }
     }
   };

  // Function to copy text to clipboard and provide feedback
  const copyToClipboard = (text, key, lang) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedKey(key); // Set the key that was copied
      setCopiedLang(lang); // Set the language that was copied
      // Reset the copied state after a short delay
      setTimeout(() => {
        setCopiedKey(null);
        setCopiedLang(null);
      }, 2000); // Reset after 2 seconds
    }).catch(err => {
      console.error('Failed to copy text: ', err);
      // Optionally, show an error message to the user
      setError('Failed to copy snippet.');
      setTimeout(() => setError(null), 3000); // Clear error after 3 seconds
    });
  };

  // Conditional rendering based on authentication and loading state
  if (!token) {
      return <div>Please log in to manage API keys.</div>;
  }
  if (loading && apiKeys.length === 0) {
      return <p>Loading API keys...</p>;
  }

  // Main component render
  return (
    <div className="api-keys">
      <h1>API Key Management</h1>
      {/* Display error message if any */}
      {error && <div className="error" style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      {/* Button to create a new key */}
      <div className="key-generator" style={{ marginBottom: '20px' }}>
        <button onClick={createKey} disabled={loading}>
          {loading ? 'Creating...' : 'Create New Key'}
        </button>
      </div>
      {/* Display message if no keys exist and not loading */}
      {apiKeys.length === 0 && !loading ? (
         <p>You don't have any API keys yet.</p>
      ) : (
        // Table to display API keys
        <table className="keys-table">
          <thead>
            <tr><th>Key</th><th>Status</th><th>Created</th><th>Last Used</th><th>Actions</th><th>Code Snippets</th></tr>
          </thead>
          <tbody>
            {/* Map over apiKeys array to render table rows */}
            {apiKeys.map(key => {
              // Define the code snippets for JS and Python
              // Corrected header to 'api-key'
              const jsSnippet = `fetch('${API_BASE_URL}/gold', { // Using /gold endpoint as example
  method: 'GET',
  headers: {
    'api-key': '${key.key}' // Corrected header name
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));`;

              // Corrected header to 'api-key'
              const pythonSnippet = `import requests

api_key = "${key.key}"
base_url = "${API_BASE_URL}"
endpoint = "/gold" # Using /gold endpoint as example

headers = {
    "api-key": api_key # Corrected header name
}

response = requests.get(f"{base_url}{endpoint}", headers=headers)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code}", response.text)`;

              // Define the curl command snippet
              const curlSnippet = `curl -X GET "${API_BASE_URL}/gold" -H "api-key: ${key.key}"`;

              return (
              <tr key={key.key}><td className="key-cell">{key.key}</td><td>{key.is_active ? 'Active' : 'Inactive'}</td><td>{new Date(key.created_at * 1000).toLocaleString()}</td>
                <td>{key.last_used ? new Date(key.last_used * 1000).toLocaleString() : 'Never'}</td>
                <td className="actions-cell"> {/* Added class for potential styling */}
                  {/* Buttons for toggling and revoking keys */}
                  <button onClick={() => toggleKey(key.key)} className="action-button">Toggle</button>
                  <button onClick={() => revokeKey(key.key)} className="action-button revoke-button">Revoke</button>
                </td>
                <td className="snippets-cell"> {/* New cell for snippets */}
                  <button
                    onClick={() => copyToClipboard(jsSnippet, key.key, 'js')}
                    className="copy-button js-copy-button"
                  >
                    {copiedKey === key.key && copiedLang === 'js' ? 'Copied JS!' : 'Copy JS'}
                  </button>
                  <button
                    onClick={() => copyToClipboard(pythonSnippet, key.key, 'py')}
                    className="copy-button py-copy-button"
                  >
                    {copiedKey === key.key && copiedLang === 'py' ? 'Copied Py!' : 'Copy Python'}
                  </button>
                  {/* Add Curl Button */}
                  <button
                    onClick={() => copyToClipboard(curlSnippet, key.key, 'curl')}
                    className="copy-button curl-copy-button" /* Added new class */
                  >
                    {copiedKey === key.key && copiedLang === 'curl' ? 'Copied Curl!' : 'Copy Curl'}
                  </button></td></tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ApiKeys;
