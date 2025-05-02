import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css'; // Optional: Add styles for the navbar

function Navbar() {
    const { isAuthenticated, user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login'); // Redirect to login after logout
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/">API Gold Portal</Link>
            </div>
            <div className="navbar-links">
                {isAuthenticated ? (
                    <>
                        {user && <span className="navbar-user">Welcome, {user.username}!</span>}
                        <Link to="/">Dashboard</Link>
                        <Link to="/api-keys">API Keys</Link>
                        {/* Add other authenticated links here */}
                        <button onClick={handleLogout} className="logout-button">Logout</button>
                    </>
                ) : (
                    <>
                        <Link to="/login">Login</Link>
                        <Link to="/register">Register</Link>
                    </>
                )}
            </div>
        </nav>
    );
}

export default Navbar;
