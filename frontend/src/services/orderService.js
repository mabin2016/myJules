import apiClient from './api';

const orderService = {
  getOrders(params = {}) {
    // GET /api/v1/orders/orders/
    return apiClient.get('/orders/orders/', { params });
  },

  getOrderDetails(orderId) {
    // GET /api/v1/orders/orders/{id}/
    return apiClient.get(`/orders/orders/${orderId}/`);
  },

  createOrder(orderData) {
    // POST /api/v1/orders/orders/
    // orderData should be like: { "amount": "100.00", "currency": "CNY", "product_description": "My Product" }
    // The backend OrderViewSet will set the user from request.user
    return apiClient.post('/orders/orders/', orderData);
  },

  // updateOrder(orderId, orderData) {
  //   // PUT /api/v1/orders/orders/{id}/
  //   return apiClient.put(`/orders/orders/${orderId}/`, orderData);
  // },

  // deleteOrder(orderId) {
  //   // DELETE /api/v1/orders/orders/{id}/
  //   return apiClient.delete(`/orders/orders/${orderId}/`);
  // }
};

export default orderService;
