import apiClient from './api';

const batchService = {
  getBatches(params = {}) {
    // GET /api/v1/orders/batches/
    return apiClient.get('/orders/batches/', { params });
  },

  getBatchDetails(batchId) {
    // GET /api/v1/orders/batches/{id}/
    return apiClient.get(`/orders/batches/${batchId}/`);
  },

  createBatch(batchData) {
    // POST /api/v1/orders/batches/
    // batchData should be like: { "order_ids": [1, 2, 3] }
    return apiClient.post('/orders/batches/', batchData);
  },

  triggerPayment(batchId) {
    // POST /api/v1/orders/batches/{id}/trigger-payment/
    return apiClient.post(`/orders/batches/${batchId}/trigger-payment/`);
  },
};

export default batchService;
