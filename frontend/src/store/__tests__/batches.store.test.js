import { setActivePinia, createPinia } from 'pinia';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useBatchStore } from '../batches'; // Path to your batches store
import batchService from '../../services/batchService'; // Path to your batch service

// Mock the batchService
vi.mock('../../services/batchService', () => ({
  default: {
    getBatches: vi.fn(),
    getBatchDetails: vi.fn(),
    createBatch: vi.fn(),
    triggerPayment: vi.fn(),
  },
}));

describe('Batch Store (useBatchStore)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.resetAllMocks();
  });

  it('initial state is correct', () => {
    const store = useBatchStore();
    expect(store.batchesList).toEqual([]);
    expect(store.currentBatchDetails).toBeNull();
    expect(store.loading).toBe(false);
    expect(store.error).toBeNull();
    expect(store.createBatchError).toBeNull();
    expect(store.triggerPaymentError).toBeNull();
  });

  describe('fetchBatches action', () => {
    it('fetches batches successfully', async () => {
      const store = useBatchStore();
      const mockBatches = [{ id: 1, total_amount: '1000.00' }, { id: 2, total_amount: '500.00' }];
      batchService.getBatches.mockResolvedValue({ data: { results: mockBatches } }); // DRF-like

      await store.fetchBatches();

      expect(batchService.getBatches).toHaveBeenCalledWith({});
      expect(store.loading).toBe(false);
      expect(store.batchesList).toEqual(mockBatches);
      expect(store.error).toBeNull();
    });

    it('handles errors during fetchBatches', async () => {
      const store = useBatchStore();
      const mockError = { response: { data: { detail: 'Batch fetch failed' } } };
      batchService.getBatches.mockRejectedValue(mockError);

      await store.fetchBatches();

      expect(store.loading).toBe(false);
      expect(store.batchesList).toEqual([]);
      expect(store.error).toBe('Batch fetch failed');
    });
  });

  describe('fetchBatchDetails action', () => {
    it('fetches batch details successfully', async () => {
      const store = useBatchStore();
      const mockBatchDetails = { id: 1, total_amount: '1000.00', status: 'PENDING_PROCESSING' };
      batchService.getBatchDetails.mockResolvedValue({ data: mockBatchDetails });

      await store.fetchBatchDetails(1);

      expect(batchService.getBatchDetails).toHaveBeenCalledWith(1);
      expect(store.loading).toBe(false);
      expect(store.currentBatchDetails).toEqual(mockBatchDetails);
      expect(store.error).toBeNull();
    });

    it('handles errors during fetchBatchDetails', async () => {
      const store = useBatchStore();
      const mockError = { message: 'Details fetch error' };
      batchService.getBatchDetails.mockRejectedValue(mockError);

      await store.fetchBatchDetails(1);

      expect(store.loading).toBe(false);
      expect(store.currentBatchDetails).toBeNull();
      expect(store.error).toBe('Details fetch error');
    });
  });

  describe('createBatch action', () => {
    it('creates a batch successfully', async () => {
      const store = useBatchStore();
      const orderIds = [1, 2, 3];
      const mockCreatedBatch = { id: 3, order_ids: orderIds, status: 'PENDING_PROCESSING' };
      // Assuming createBatch API in service expects { order_ids: [...] }
      batchService.createBatch.mockResolvedValue({ data: mockCreatedBatch }); 

      const result = await store.createBatch(orderIds);

      expect(batchService.createBatch).toHaveBeenCalledWith({ order_ids: orderIds });
      expect(store.loading).toBe(false);
      expect(store.batchesList).toContainEqual(mockCreatedBatch); // Assumes unshift
      expect(result).toEqual(mockCreatedBatch);
      expect(store.createBatchError).toBeNull();
    });
    
    it('handles array response when creating a batch', async () => {
      const store = useBatchStore();
      const orderIds = [1, 2, 3, 4, 5];
      const mockCreatedBatches = [
        { id: 3, order_ids: [1,2], status: 'PENDING_PROCESSING' },
        { id: 4, order_ids: [3,4,5], status: 'PENDING_PROCESSING' }
      ];
      batchService.createBatch.mockResolvedValue({ data: mockCreatedBatches });

      const result = await store.createBatch(orderIds);
      expect(batchService.createBatch).toHaveBeenCalledWith({ order_ids: orderIds });
      expect(store.loading).toBe(false);
      expect(store.batchesList).toEqual(expect.arrayContaining(mockCreatedBatches));
      expect(result).toEqual(mockCreatedBatches);
    });


    it('handles errors during createBatch', async () => {
      const store = useBatchStore();
      const orderIds = [1, 2];
      const mockError = { response: { data: { order_ids: ['Invalid order ID.'] } } };
      batchService.createBatch.mockRejectedValue(mockError);

      try {
        await store.createBatch(orderIds);
      } catch (e) {
        expect(e).toEqual(mockError.response.data);
      }

      expect(store.loading).toBe(false);
      expect(store.createBatchError).toEqual(mockError.response.data);
    });
  });

  describe('triggerBatchPayment action', () => {
    it('triggers batch payment successfully', async () => {
      const store = useBatchStore();
      const batchId = 1;
      const mockResponse = { detail: 'Payment triggered', task_id: 'task123', status: 'PROCESSING' };
      batchService.triggerPayment.mockResolvedValue({ data: mockResponse });
      
      // Optionally pre-populate currentBatchDetails or batchesList to test updates
      store.currentBatchDetails = { id: batchId, status: 'PENDING_PROCESSING' };
      store.batchesList = [{ id: batchId, status: 'PENDING_PROCESSING' }];

      const result = await store.triggerBatchPayment(batchId);

      expect(batchService.triggerPayment).toHaveBeenCalledWith(batchId);
      expect(store.loading).toBe(false);
      expect(store.triggerPaymentError).toBeNull();
      expect(result).toEqual(mockResponse);
      // Check if store state was updated (e.g., status of the batch)
      expect(store.currentBatchDetails.status).toBe('PROCESSING');
      expect(store.batchesList.find(b => b.id === batchId).status).toBe('PROCESSING');
    });

    it('handles errors during triggerBatchPayment', async () => {
      const store = useBatchStore();
      const batchId = 1;
      const mockError = { response: { data: { detail: 'Cannot trigger payment.' } } };
      batchService.triggerPayment.mockRejectedValue(mockError);

      try {
        await store.triggerBatchPayment(batchId);
      } catch (e) {
        expect(e).toEqual(mockError.response.data.detail);
      }
      
      expect(store.loading).toBe(false);
      expect(store.triggerPaymentError).toBe('Cannot trigger payment.');
    });
  });
  
  it('clearCurrentBatchDetails action resets currentBatchDetails', () => {
    const store = useBatchStore();
    store.currentBatchDetails = { id: 1, status: 'COMPLETED' };
    store.clearCurrentBatchDetails();
    expect(store.currentBatchDetails).toBeNull();
  });
});
