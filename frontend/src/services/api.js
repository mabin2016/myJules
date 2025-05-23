import axios from 'axios';
import { useAuthStore } from '../store/auth'; // Import Pinia store

// Get base URL from environment variable or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add the auth token to headers
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore(); // Access store inside interceptor
    const token = authStore.token;
    if (token) {
      // Assuming your Django backend uses Bearer token (e.g., with SimpleJWT)
      // If using DRF's default TokenAuthentication, it would be `Token ${token}`
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Response interceptor for handling global errors like 401
apiClient.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    const authStore = useAuthStore();

    if (error.response && error.response.status === 401) {
      // Handle unauthorized errors, e.g., token expired
      // Redirect to login or attempt token refresh
      console.error('Unauthorized request (401):', error.response.data);
      authStore.logout(); // Force logout on 401
      // Optionally, redirect to login page. This might be better handled in router navigation guards.
      // import router from '../router'; // Be careful with circular dependencies if router imports store
      // router.push('/login');
    }
    return Promise.reject(error);
  }
);

export default apiClient;
