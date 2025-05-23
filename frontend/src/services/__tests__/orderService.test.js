import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import apiClient from '../api'; // The axios instance
import orderService from '../orderService';

describe('Order Service', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    mock.restore();
  });

  it('getOrders calls the correct endpoint', async () => {
    const mockResponseData = { results: [{ id: 1, amount: '100.00' }] };
    mock.onGet('/orders/orders/').reply(200, mockResponseData);

    const response = await orderService.getOrders();

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get.length).toBe(1);
    expect(mock.history.get[0].url).toBe('/orders/orders/');
  });

  it('getOrders calls with params', async () => {
    const params = { status: 'PENDING' };
    const mockResponseData = { results: [{ id: 2, amount: '50.00', status: 'PENDING' }] };
    // Vitest/axios-mock-adapter check for params might be exact or require specific config.
    // For this, ensuring the URL is called is primary.
    mock.onGet('/orders/orders/', { params }).reply(200, mockResponseData);

    const response = await orderService.getOrders(params);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get[0].params).toEqual(params);
  });

  it('getOrderDetails calls the correct endpoint with ID', async () => {
    const orderId = 123;
    const mockResponseData = { id: orderId, amount: '200.00', currency: 'USD' };
    mock.onGet(`/orders/orders/${orderId}/`).reply(200, mockResponseData);

    const response = await orderService.getOrderDetails(orderId);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get.length).toBe(1);
    expect(mock.history.get[0].url).toBe(`/orders/orders/${orderId}/`);
  });

  it('createOrder calls the correct endpoint with order data', async () => {
    const orderData = { amount: '75.50', currency: 'EUR', product_description: 'New Gadget' };
    const mockResponseData = { id: 1, ...orderData, status: 'PENDING' };
    mock.onPost('/orders/orders/', orderData).reply(201, mockResponseData);

    const response = await orderService.createOrder(orderData);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].data).toBe(JSON.stringify(orderData));
    expect(mock.history.post[0].url).toBe('/orders/orders/');
  });

  it('createOrder handles API error', async () => {
    const orderData = { amount: '0.00', currency: 'USD' }; // Potentially invalid amount
    const errorResponse = { amount: ['Amount must be greater than 0.'] };
    mock.onPost('/orders/orders/', orderData).reply(400, errorResponse);

    try {
      await orderService.createOrder(orderData);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data).toEqual(errorResponse);
    }
  });
});
