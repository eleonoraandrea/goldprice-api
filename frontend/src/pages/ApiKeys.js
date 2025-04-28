import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

function ApiKeys() {
  const [apiKeys, setApiKeys] = useState([]);
  const [newKey, setNewKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api-keys`);
      setApiKeys(response.data);
    } catch (err) {
      setError('Failed to fetch API keys');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const generateKey = () => {
    const key = [...Array(32)].map(() => Math.random().toString(36)[2]).join('');
    setNewKey(key);
  };

  const saveKey = async () => {
    if (!newKey) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api-keys`, { 
        key: newKey, 
        is_active: true,
        created_at: Date.now() / 1000,
        last_used: 0,
        usage_count: 0
      });
      setApiKeys([...apiKeys, response.data]);
      setNewKey('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save API key');
    } finally {
      setLoading(false);
    }
  };

  const toggleKey = async (key) => {
    try {
      await axios.post(`${API_BASE_URL}/api-keys/${key}/toggle`);
      fetchKeys();
    } catch (err) {
      setError('Failed to toggle key status');
    }
  };

  const revokeKey = async (key) => {
    try {
      await axios.delete(`${API_BASE_URL}/api-keys/${key}`);
      fetchKeys();
    } catch (err) {
      setError('Failed to revoke key');
    }
  };

  return (
    <div className="api-keys">
      <h1>API Key Management</h1>
      {error && <div className="error">{error}</div>}
      <div className="key-generator">
        <button onClick={generateKey} disabled={loading}>
          {loading ? 'Generating...' : 'Generate New Key'}
        </button>
        {newKey && (
          <div className="new-key">
            <p>New API Key: {newKey}</p>
            <button onClick={saveKey} disabled={loading}>
              {loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        )}
      </div>
      {loading && apiKeys.length === 0 ? (
        <p>Loading API keys...</p>
      ) : (
        <table className="keys-table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Status</th>
              <th>Created</th>
              <th>Last Used</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {apiKeys.map(key => (
              <tr key={key.key}>
                <td>{key.key}</td>
                <td>{key.is_active ? 'Active' : 'Inactive'}</td>
                <td>{new Date(key.created_at * 1000).toLocaleString()}</td>
                <td>{key.last_used ? new Date(key.last_used * 1000).toLocaleString() : 'Never'}</td>
                <td>
                  <button onClick={() => toggleKey(key.key)}>Toggle</button>
                  <button onClick={() => revokeKey(key.key)}>Revoke</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default ApiKeys;
