import { setActivePinia, createPinia } from 'pinia';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../auth'; // Path to your auth store
import authService from '../../services/authService'; // Path to your auth service
import apiClient from '../../services/api'; // To check Authorization header

// Mock the authService
vi.mock('../../services/authService', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
  },
}));

// Mock apiClient to check Authorization header (optional, more for integration)
// vi.mock('../../services/api');

describe('Auth Store (useAuthStore)', () => {
  beforeEach(() => {
    // Create a new Pinia instance for each test to avoid state leakage
    setActivePinia(createPinia());
    // Clear localStorage and any other global state used by the store
    localStorage.clear();
    // Reset mocks
    vi.resetAllMocks();
    // Ensure apiClient default headers are clean if modified by tests
    delete apiClient.defaults.headers.common['Authorization'];
  });

  it('initial state is correct', () => {
    const store = useAuthStore();
    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.isAuthenticated).toBe(false);
    expect(store.loginError).toBeNull();
    expect(store.registrationError).toBeNull();
    expect(store.registrationSuccess).toBe(false);
  });

  describe('login action', () => {
    it('handles successful login', async () => {
      const store = useAuthStore();
      const mockToken = 'fake-jwt-token';
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' };
      authService.login.mockResolvedValue({ 
        data: { token: mockToken, user: mockUser } 
      });

      const credentials = { username: 'testuser', password: 'password' };
      const result = await store.login(credentials);

      expect(authService.login).toHaveBeenCalledWith(credentials);
      expect(store.token).toBe(mockToken);
      expect(store.user).toEqual(mockUser);
      expect(store.isAuthenticated).toBe(true);
      expect(store.loginError).toBeNull();
      expect(localStorage.getItem('token')).toBe(mockToken);
      expect(localStorage.getItem('user')).toBe(JSON.stringify(mockUser));
      expect(apiClient.defaults.headers.common['Authorization']).toBe(`Bearer ${mockToken}`);
      expect(result).toBe(true);
    });

    it('handles login failure - API error', async () => {
      const store = useAuthStore();
      const mockError = { response: { data: { detail: 'Invalid credentials' } } };
      authService.login.mockRejectedValue(mockError);

      const credentials = { username: 'testuser', password: 'wrongpassword' };
      const result = await store.login(credentials);

      expect(store.isAuthenticated).toBe(false);
      expect(store.token).toBeNull();
      expect(store.user).toBeNull();
      expect(store.loginError).toBe('Invalid credentials');
      expect(localStorage.getItem('token')).toBeNull();
      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
      expect(result).toBe(false);
    });
    
    it('handles login failure - no token in response', async () => {
      const store = useAuthStore();
       authService.login.mockResolvedValue({ 
        data: { user: {id: 1, username: 'test'} } // No token
      });
      const result = await store.login({ username: 'test', password: 'password' });
      expect(result).toBe(false);
      expect(store.isAuthenticated).toBe(false);
      expect(store.loginError).toContain('No token received');
    });
  });

  describe('logout action', () => {
    it('clears user, token, and localStorage', () => {
      const store = useAuthStore();
      // Simulate a logged-in state
      store.token = 'fake-token';
      store.user = { id: 1, username: 'testuser' };
      store.isAuthenticated = true;
      localStorage.setItem('token', 'fake-token');
      apiClient.defaults.headers.common['Authorization'] = 'Bearer fake-token';

      store.logout();

      expect(store.token).toBeNull();
      expect(store.user).toBeNull();
      expect(store.isAuthenticated).toBe(false);
      expect(localStorage.getItem('token')).toBeNull();
      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });

  describe('register action', () => {
    it('handles successful registration', async () => {
      const store = useAuthStore();
      const newUser = { username: 'newuser', email: 'new@example.com', password: 'password123' };
      const mockRegisteredUser = { id: 2, username: 'newuser', email: 'new@example.com' };
      authService.register.mockResolvedValue({ data: mockRegisteredUser });

      const result = await store.register(newUser);

      expect(authService.register).toHaveBeenCalledWith(newUser);
      expect(store.registrationSuccess).toBe(true);
      expect(store.registrationError).toBeNull();
      expect(result).toBe(true);
    });

    it('handles registration failure', async () => {
      const store = useAuthStore();
      const newUser = { username: 'newuser', email: 'new@example.com', password: 'password123' };
      const mockError = { response: { data: { email: ['Email already exists.'] } } };
      authService.register.mockRejectedValue(mockError);

      const result = await store.register(newUser);

      expect(store.registrationSuccess).toBe(false);
      expect(store.registrationError).toEqual({ email: ['Email already exists.'] });
      expect(result).toBe(false);
    });
  });

  describe('checkAuth action', () => {
    it('restores state from localStorage if token and user exist', () => {
      const mockToken = 'stored-token';
      const mockUser = { id: 1, username: 'storeduser' };
      localStorage.setItem('token', mockToken);
      localStorage.setItem('user', JSON.stringify(mockUser));
      
      const store = useAuthStore();
      // Store is re-initialized here, so initial state is default (nulls)
      // before checkAuth is called.
      expect(store.token).toBeNull(); // Pre-checkAuth

      store.checkAuth();

      expect(store.token).toBe(mockToken);
      expect(store.user).toEqual(mockUser);
      expect(store.isAuthenticated).toBe(true);
      expect(apiClient.defaults.headers.common['Authorization']).toBe(`Bearer ${mockToken}`);
    });

    it('does nothing and ensures logged out state if no token in localStorage', () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      const store = useAuthStore();
      // Simulate a potentially dirty state before checkAuth
      store.token = "old-token";
      store.isAuthenticated = true;

      store.checkAuth();

      expect(store.token).toBeNull();
      expect(store.user).toBeNull();
      expect(store.isAuthenticated).toBe(false);
      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined();
    });
  });
});
