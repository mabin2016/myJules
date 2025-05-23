import { setActivePinia, createPinia } from 'pinia';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useOrderStore } from '../orders'; // Path to your orders store
import orderService from '../../services/orderService'; // Path to your order service

// Mock the orderService
vi.mock('../../services/orderService', () => ({
  default: {
    getOrders: vi.fn(),
    getOrderDetails: vi.fn(),
    createOrder: vi.fn(),
  },
}));

describe('Order Store (useOrderStore)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.resetAllMocks();
  });

  it('initial state is correct', () => {
    const store = useOrderStore();
    expect(store.ordersList).toEqual([]);
    expect(store.currentOrder).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
  });

  describe('fetchOrders action', () => {
    it('fetches orders successfully and updates state', async () => {
      const store = useOrderStore();
      const mockOrders = [{ id: 1, amount: '100.00' }, { id: 2, amount: '150.00' }];
      orderService.getOrders.mockResolvedValue({ data: { results: mockOrders } }); // DRF like response

      await store.fetchOrders();

      expect(orderService.getOrders).toHaveBeenCalledWith({});
      expect(store.loading).toBe(false);
      expect(store.ordersList).toEqual(mockOrders);
      expect(store.error).toBeNull();
    });

    it('handles errors during fetchOrders', async () => {
      const store = useOrderStore();
      const mockError = { response: { data: { detail: 'Failed to fetch' } } };
      orderService.getOrders.mockRejectedValue(mockError);

      await store.fetchOrders();

      expect(store.loading).toBe(false);
      expect(store.ordersList).toEqual([]);
      expect(store.error).toBe('Failed to fetch');
    });
     it('fetches orders with params successfully', async () => {
      const store = useOrderStore();
      const params = { status: 'PENDING' };
      const mockOrders = [{ id: 3, amount: '200.00', status: 'PENDING' }];
      orderService.getOrders.mockResolvedValue({ data: mockOrders }); // Direct array response

      await store.fetchOrders(params);

      expect(orderService.getOrders).toHaveBeenCalledWith(params);
      expect(store.ordersList).toEqual(mockOrders);
    });
  });

  describe('fetchOrderDetails action', () => {
    it('fetches order details successfully', async () => {
      const store = useOrderStore();
      const mockOrderDetails = { id: 1, amount: '100.00', currency: 'USD' };
      orderService.getOrderDetails.mockResolvedValue({ data: mockOrderDetails });

      await store.fetchOrderDetails(1);

      expect(orderService.getOrderDetails).toHaveBeenCalledWith(1);
      expect(store.loading).toBe(false);
      expect(store.currentOrder).toEqual(mockOrderDetails);
      expect(store.error).toBeNull();
    });

    it('handles errors during fetchOrderDetails', async () => {
      const store = useOrderStore();
      const mockError = { message: 'Network Error' };
      orderService.getOrderDetails.mockRejectedValue(mockError);

      await store.fetchOrderDetails(1);

      expect(store.loading).toBe(false);
      expect(store.currentOrder).toBeNull();
      expect(store.error).toBe('Network Error');
    });
  });

  describe('createOrder action', () => {
    it('creates an order successfully', async () => {
      const store = useOrderStore();
      const orderData = { amount: '50.00', currency: 'EUR', product_description: 'Test Item' };
      const mockCreatedOrder = { id: 3, ...orderData, status: 'PENDING' };
      orderService.createOrder.mockResolvedValue({ data: mockCreatedOrder });

      const result = await store.createOrder(orderData);

      expect(orderService.createOrder).toHaveBeenCalledWith(orderData);
      expect(store.loading).toBe(false);
      // Optional: check if ordersList is updated or rely on component to refetch/update
      // expect(store.ordersList).toContainEqual(mockCreatedOrder); // If unshift is used
      expect(result).toEqual(mockCreatedOrder);
      expect(store.error).toBeNull();
    });

    it('handles errors during createOrder', async () => {
      const store = useOrderStore();
      const orderData = { amount: '50.00', currency: 'EUR' };
      const mockError = { response: { data: { amount: ['Amount is required.'] } } };
      orderService.createOrder.mockRejectedValue(mockError);

      try {
        await store.createOrder(orderData);
      } catch (e) {
        expect(e).toEqual(mockError.response.data);
      }

      expect(store.loading).toBe(false);
      expect(store.error).toEqual(mockError.response.data);
    });
  });
  
  it('clearCurrentOrder action resets currentOrder', () => {
    const store = useOrderStore();
    store.currentOrder = { id: 1, amount: '10.00' };
    store.clearCurrentOrder();
    expect(store.currentOrder).toBeNull();
  });

  it('clearOrdersList action resets ordersList', () => {
    const store = useOrderStore();
    store.ordersList = [{ id: 1, amount: '10.00' }];
    store.clearOrdersList();
    expect(store.ordersList).toEqual([]);
  });
});
