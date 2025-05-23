import { defineStore } from 'pinia';
import authService from '../services/authService';
import api from '../services/api'; // To set/unset Authorization header

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    loginError: null,
    registrationError: null,
    registrationSuccess: false,
  }),
  getters: {
    // No specific getters needed yet, can access state directly
  },
  actions: {
    async login(credentials) {
      this.loginError = null;
      try {
        const response = await authService.login(credentials);
        // Assuming login response returns an object with 'access' (token) and 'user' details
        // This depends on your DRF backend (e.g. djangorestframework-simplejwt)
        // For now, let's assume a simple token and user object if not using SimpleJWT directly.
        // If using SimpleJWT, response.data might be { access: "...", refresh: "..." }
        // And user details might need a separate fetch or be included in token claims (decoded).

        // Placeholder: Adapt based on actual API response.
        // If your custom /api/v1/users/login/ endpoint returns { token: "...", user: {...} }
        const token = response.data.token; // Adjust if using SimpleJWT's 'access'
        const userData = response.data.user; // Adjust based on your API

        if (!token) {
            throw new Error(response.data.detail || "Login failed: No token received.");
        }
        
        this.token = token;
        this.user = userData; // Or decode token for user info if that's your setup
        this.isAuthenticated = true;

        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData)); // Store user info if available
        
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`; // Or 'Token ' for DRF TokenAuthentication

        // Optionally, redirect to dashboard or intended page
        // This should be handled by the router after successful login in the component.
        return true;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.response?.data?.error || error.message || 'Login failed. Please check your credentials.';
        this.loginError = errorMessage;
        this.isAuthenticated = false;
        this.user = null;
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        delete api.defaults.headers.common['Authorization'];
        console.error('Login error:', error);
        return false;
      }
    },
    logout() {
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
      this.loginError = null;
      this.registrationError = null;
      
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete api.defaults.headers.common['Authorization'];
      
      // Router navigation to /login should be handled in the component or router.
    },
    async register(userData) {
      this.registrationError = null;
      this.registrationSuccess = false;
      try {
        // Assuming your authService.register makes the API call
        // and your backend returns the created user data (excluding password)
        const response = await authService.register(userData); 
        // For a successful registration, you might want to log the user in
        // or just indicate success and let them log in manually.
        // This example assumes registration does not auto-login.
        this.registrationSuccess = true; 
        console.log('Registration successful:', response.data);
        return true;
      } catch (error) {
        this.registrationError = error.response?.data || { message: 'Registration failed.' };
        console.error('Registration error:', error.response?.data || error.message);
        this.registrationSuccess = false;
        return false;
      }
    },
    checkAuth() {
      // This action can be called when the app loads to re-initialize state
      // and potentially verify token with backend if needed.
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      if (token && user) {
        this.token = token;
        this.user = JSON.parse(user);
        this.isAuthenticated = true;
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`; // Or 'Token '
      } else {
        this.logout(); // Ensure clean state if no token/user
      }
    },
    // Example: Action to refresh token if using JWT with refresh tokens
    // async refreshToken() { /* ... */ }
  },
});
