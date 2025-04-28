import React from 'react';
import { FaUsers, FaKey, FaChartLine, FaCog } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="dashboard">
      <h1>API Management Dashboard</h1>
      
      <div className="quick-actions">
        <button onClick={() => navigate('/users')}>
          <FaUsers /> Manage Users
        </button>
        <button onClick={() => navigate('/api-keys')}>
          <FaKey /> API Keys
        </button>
        <button>
          <FaChartLine /> Analytics
        </button>
        <button>
          <FaCog /> Settings
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Active Users</h3>
          <p>24</p>
        </div>
        <div className="stat-card">
          <h3>API Keys</h3>
          <p>8</p>
        </div>
        <div className="stat-card">
          <h3>Requests Today</h3>
          <p>1,245</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
