import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import apiClient from '../api'; // The axios instance
import batchService from '../batchService';

describe('Batch Service', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(apiClient);
  });

  afterEach(() => {
    mock.restore();
  });

  it('getBatches calls the correct endpoint', async () => {
    const mockResponseData = { results: [{ id: 1, total_amount: '100.00' }] };
    mock.onGet('/orders/batches/').reply(200, mockResponseData);

    const response = await batchService.getBatches();

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get.length).toBe(1);
    expect(mock.history.get[0].url).toBe('/orders/batches/');
  });
  
  it('getBatches calls with params', async () => {
    const params = { status: 'COMPLETED' };
    const mockResponseData = { results: [{ id: 2, status: 'COMPLETED' }] };
    mock.onGet('/orders/batches/', { params }).reply(200, mockResponseData);

    const response = await batchService.getBatches(params);
    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get[0].params).toEqual(params);
  });

  it('getBatchDetails calls the correct endpoint with ID', async () => {
    const batchId = 456;
    const mockResponseData = { id: batchId, total_amount: '500.00', status: 'PROCESSING' };
    mock.onGet(`/orders/batches/${batchId}/`).reply(200, mockResponseData);

    const response = await batchService.getBatchDetails(batchId);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.get.length).toBe(1);
    expect(mock.history.get[0].url).toBe(`/orders/batches/${batchId}/`);
  });

  it('createBatch calls the correct endpoint with batch data (order_ids)', async () => {
    const batchData = { order_ids: [1, 2, 3] };
    const mockResponseData = { id: 1, ...batchData, status: 'PENDING_PROCESSING' }; // Assuming single batch created
    mock.onPost('/orders/batches/', batchData).reply(201, mockResponseData);

    const response = await batchService.createBatch(batchData);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.post.length).toBe(1);
    expect(mock.history.post[0].data).toBe(JSON.stringify(batchData));
    expect(mock.history.post[0].url).toBe('/orders/batches/');
  });

  it('createBatch handles API error', async () => {
    const batchData = { order_ids: [999] }; // Potentially invalid order ID
    const errorResponse = { order_ids: ['Invalid order ID provided.'] };
    mock.onPost('/orders/batches/', batchData).reply(400, errorResponse);

    try {
      await batchService.createBatch(batchData);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data).toEqual(errorResponse);
    }
  });

  it('triggerPayment calls the correct endpoint with batch ID', async () => {
    const batchId = 789;
    const mockResponseData = { detail: 'Payment processing triggered for batch.', task_id: 'task-xyz' };
    // Endpoint is /api/v1/orders/batches/{id}/trigger-payment/
    mock.onPost(`/orders/batches/${batchId}/trigger-payment/`).reply(202, mockResponseData);

    const response = await batchService.triggerPayment(batchId);

    expect(response.data).toEqual(mockResponseData);
    expect(mock.history.post.length).toBe(1);
    // AxiosMockAdapter stores POST data as a string, ensure it's empty if no data sent
    expect(mock.history.post[0].data).toBeUndefined(); // Or check if it's null/empty string based on adapter
    expect(mock.history.post[0].url).toBe(`/orders/batches/${batchId}/trigger-payment/`);
  });

  it('triggerPayment handles API error', async () => {
    const batchId = 101;
    const errorResponse = { detail: 'Batch not in a triggerable state.' };
    mock.onPost(`/orders/batches/${batchId}/trigger-payment/`).reply(400, errorResponse);

    try {
      await batchService.triggerPayment(batchId);
    } catch (error) {
      expect(error.response.status).toBe(400);
      expect(error.response.data).toEqual(errorResponse);
    }
  });
});
