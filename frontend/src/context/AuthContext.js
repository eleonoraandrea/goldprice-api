import React, { createContext, useState, useContext, useEffect } from 'react';
import { API_BASE_URL } from '../config'; // Assuming config.js is one level up

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [token, setToken] = useState(localStorage.getItem('authToken'));
    const [user, setUser] = useState(null); // Store user info if needed
    const [loading, setLoading] = useState(true); // To check initial auth status

    // Function to fetch user data based on token (optional, but good practice)
    const fetchUser = async (currentToken) => {
        if (!currentToken) {
            setUser(null);
            setLoading(false);
            return;
        }
        try {
            const response = await fetch(`${API_BASE_URL}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${currentToken}`,
                },
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                // Token might be invalid or expired
                logout(); // Clear invalid token
            }
        } catch (error) {
            console.error("Failed to fetch user:", error);
            logout(); // Clear token on error
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUser(token);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]); // Re-fetch user if token changes

    const login = (newToken, userData) => {
        localStorage.setItem('authToken', newToken);
        setToken(newToken);
        setUser(userData); // Optionally set user data immediately
        // Or rely on useEffect to fetch user data based on the new token
    };

    const logout = () => {
        localStorage.removeItem('authToken');
        setToken(null);
        setUser(null);
    };

    const authValue = {
        token,
        user,
        loading, // Expose loading state
        login,
        logout,
        isAuthenticated: !!token, // Simple check for authentication
    };

    return (
        <AuthContext.Provider value={authValue}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
