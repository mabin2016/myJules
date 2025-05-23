import { defineStore } from 'pinia';
import orderService from '../services/orderService'; // Will be created

export const useOrderStore = defineStore('orders', {
  state: () => ({
    ordersList: [],
    currentOrder: null,
    loading: false,
    error: null,
  }),
  actions: {
    async fetchOrders(params = {}) {
      this.loading = true;
      this.error = null;
      try {
        const response = await orderService.getOrders(params);
        // Assuming orderService.getOrders() returns the data array directly
        // or an object with a 'results' property like DRF pagination
        this.ordersList = response.data.results || response.data; 
        console.log('Orders fetched:', this.ordersList);
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Failed to fetch orders.';
        this.ordersList = [];
        console.error('Error fetching orders:', this.error);
      } finally {
        this.loading = false;
      }
    },
    async fetchOrderDetails(orderId) {
      this.loading = true;
      this.error = null;
      try {
        const response = await orderService.getOrderDetails(orderId);
        this.currentOrder = response.data;
        console.log('Order details fetched:', this.currentOrder);
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Failed to fetch order details.';
        this.currentOrder = null;
        console.error('Error fetching order details:', this.error);
      } finally {
        this.loading = false;
      }
    },
    async createOrder(orderData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await orderService.createOrder(orderData);
        // Optionally add to ordersList or refetch the list
        // this.ordersList.unshift(response.data); // Add to the beginning
        console.log('Order created:', response.data);
        return response.data; // Return created order
      } catch (err) {
        this.error = err.response?.data || { message: 'Failed to create order.' };
        console.error('Error creating order:', this.error);
        throw this.error; // Re-throw to be caught by component
      } finally {
        this.loading = false;
      }
    },
    // Action to clear current order selection or list
    clearCurrentOrder() {
        this.currentOrder = null;
    },
    clearOrdersList() {
        this.ordersList = [];
    }
  },
});
