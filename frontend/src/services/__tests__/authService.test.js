import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import apiClient from '../api'; // The axios instance
import authService from '../authService';

describe('Auth Service', () => {
  let mock;

  beforeEach(() => {
    // Create a new mock adapter for each test
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    // Restore the original adapter after each test
    mock.restore();
  });

  it('login calls the correct endpoint with credentials', async () => {
    const credentials = { username: 'testuser', password: 'password123' };
    const mockResponseData = { token: 'fake-token', user: { id: 1, username: 'testuser' } };
    
    // Expect a POST request to '/users/login/' (as per authService.js)
    mock.onPost('/users/login/', credentials).reply(200, mockResponseData);

    const response = await authService.login(credentials);

    expect(response.data).toEqual(mockResponseData);
    // Check if the mock adapter received the request as expected
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].data).toBe(JSON.stringify(credentials));
    expect(mock.history.post[0].url).toBe('/users/login/');
  });

  it('login handles API error', async () => {
    const credentials = { username: 'testuser', password: 'wrongpassword' };
    const errorMessage = 'Invalid credentials';
    
    mock.onPost('/users/login/', credentials).reply(400, { detail: errorMessage });

    try {
      await authService.login(credentials);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.detail).toBe(errorMessage);
    }
  });

  it('register calls the correct endpoint with user data', async () => {
    const userData = { username: 'newuser', email: 'new@example.com', password: 'password123' };
    const mockResponseData = { id: 2, username: 'newuser', email: 'new@example.com' }; // No password in response

    // Expect a POST request to '/users/users/' (as per authService.js and DRF UserViewSet)
    mock.onPost('/users/users/', userData).reply(201, mockResponseData);

    const response = await authService.register(userData);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].data).toBe(JSON.stringify(userData));
    expect(mock.history.post[0].url).toBe('/users/users/');
  });

  it('register handles API error (e.g., email already exists)', async () => {
    const userData = { username: 'anotheruser', email: 'new@example.com', password: 'password123' };
    const errorResponse = { email: ['This email address is already in use.'] };
    
    mock.onPost('/users/users/', userData).reply(400, errorResponse);

    try {
      await authService.register(userData);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data).toEqual(errorResponse);
    }
  });
});
