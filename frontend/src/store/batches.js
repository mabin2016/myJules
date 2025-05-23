import { defineStore } from 'pinia';
import batchService from '../services/batchService'; // Will be created

export const useBatchStore = defineStore('batches', {
  state: () => ({
    batchesList: [],
    currentBatchDetails: null,
    loading: false,
    error: null,
    createBatchError: null,
    triggerPaymentError: null,
  }),
  actions: {
    async fetchBatches(params = {}) {
      this.loading = true;
      this.error = null;
      try {
        const response = await batchService.getBatches(params);
        // Assuming response.data is an array or an object with a 'results' property
        this.batchesList = response.data.results || response.data;
        console.log('Batches fetched:', this.batchesList);
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Failed to fetch batches.';
        this.batchesList = [];
        console.error('Error fetching batches:', this.error);
      } finally {
        this.loading = false;
      }
    },
    async fetchBatchDetails(batchId) {
      this.loading = true;
      this.error = null;
      try {
        const response = await batchService.getBatchDetails(batchId);
        this.currentBatchDetails = response.data;
        console.log('Batch details fetched:', this.currentBatchDetails);
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'Failed to fetch batch details.';
        this.currentBatchDetails = null;
        console.error('Error fetching batch details:', this.error);
      } finally {
        this.loading = false;
      }
    },
    async createBatch(orderIds) {
      this.loading = true;
      this.createBatchError = null;
      try {
        // The batchService.createBatch expects an object like { order_ids: [...] }
        const response = await batchService.createBatch({ order_ids: orderIds });
        // Response might be a list of created batches if multiple are made due to size limit
        // Or a single batch object. Adjust based on actual API.
        // For now, assume it returns the created batch(es) and we might want to add to list or refetch.
        console.log('Batch created/triggered:', response.data);
        // Example: If response.data is an array of batches
        if (Array.isArray(response.data)) {
            response.data.forEach(batch => this.batchesList.unshift(batch));
        } else {
            this.batchesList.unshift(response.data); // Add new batch to the beginning
        }
        return response.data; 
      } catch (err) {
        this.createBatchError = err.response?.data || { message: 'Failed to create batch.' };
        console.error('Error creating batch:', this.createBatchError);
        throw this.createBatchError; // Re-throw to be caught by component
      } finally {
        this.loading = false;
      }
    },
    async triggerBatchPayment(batchId) {
      this.loading = true;
      this.triggerPaymentError = null;
      try {
        const response = await batchService.triggerPayment(batchId);
        console.log('Batch payment triggered:', response.data);
        // Update the status of the batch in currentBatchDetails or batchesList if needed
        // This might require fetching batch details again or updating manually from response.
        if (this.currentBatchDetails && this.currentBatchDetails.id === batchId) {
            // Example: response.data might contain updated batch status or a task ID
            this.currentBatchDetails.status = response.data.status || 'PROCESSING'; 
            this.currentBatchDetails.task_id = response.data.task_id; // If API returns it
        }
        // Find and update in list (simplified)
        const batchInList = this.batchesList.find(b => b.id === batchId);
        if (batchInList) {
            batchInList.status = response.data.status || 'PROCESSING';
        }
        return response.data;
      } catch (err) {
        this.triggerPaymentError = err.response?.data?.detail || err.message || 'Failed to trigger batch payment.';
        console.error('Error triggering batch payment:', this.triggerPaymentError);
        throw this.triggerPaymentError; // Re-throw
      } finally {
        this.loading = false;
      }
    },
    clearCurrentBatchDetails() {
        this.currentBatchDetails = null;
    }
  },
});
