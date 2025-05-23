<template>
  <div class="batch-payment-view">
    <div class="card">
      <h2 class="card-header">Create Payment Batch</h2>
      <div v-if="orderStore.loading">Loading pending orders...</div>
      <div v-if="orderStore.error" class="error-message">
        Error fetching orders: {{ orderStore.error.message || orderStore.error }}
      </div>
      <div v-if="pendingOrders.length > 0">
        <form @submit.prevent="handleCreateBatch">
          <h3>Select Orders for Batch:</h3>
          <div class="order-selection-list">
            <div v-for="order in pendingOrders" :key="order.id" class="order-item">
              <input type="checkbox" :id="`order-${order.id}`" :value="order.id" v-model="selectedOrderIds" />
              <label :for="`order-${order.id}`">
                Order #{{ order.id }} ({{ order.order_uid.substring(0,8) }}...) - Amount: {{ order.amount }} {{ order.currency }} - User: {{ order.user.username }}
              </label>
            </div>
          </div>
          <button type="submit" class="btn mt-2" :disabled="selectedOrderIds.length === 0 || batchStore.loading">
            {{ batchStore.loading ? 'Creating Batch...' : 'Create Batch from Selected Orders' }}
          </button>
          <div v.if="batchStore.createBatchError" class="error-message mt-1">
            Error creating batch: {{ batchStore.createBatchError.message || batchStore.createBatchError }}
          </div>
        </form>
      </div>
      <p v-else-if="!orderStore.loading">No pending orders available to batch.</p>
    </div>

    <div class="card mt-2">
      <h2 class="card-header">Existing Payment Batches</h2>
      <div v-if="batchStore.loading">Loading batches...</div>
      <div v.if="batchStore.error" class="error-message">
        Error fetching batches: {{ batchStore.error.message || batchStore.error }}
      </div>
      <ul v-if="batchStore.batchesList.length > 0" class="batch-list">
        <li v-for="batch in batchStore.batchesList" :key="batch.id" class="batch-item">
          <router-link :to="{ name: 'BatchStatus', params: { id: batch.id } }">
            Batch #{{ batch.id }} ({{ batch.batch_uid.substring(0,8) }}...) - Status: {{ batch.status }}
          </router-link>
          <br/>
          Total: {{ batch.total_amount }}, Orders: {{ batch.total_orders }}
          <small>(Created: {{ new Date(batch.created_at).toLocaleDateString() }})</small>
        </li>
      </ul>
      <p v-else-if="!batchStore.loading">No payment batches found.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useOrderStore } from '../store/orders';
import { useBatchStore } from '../store/batches';
import { useRouter } from 'vue-router';

const orderStore = useOrderStore();
const batchStore = useBatchStore();
const router = useRouter();

const selectedOrderIds = ref([]);

onMounted(async () => {
  // Fetch orders that are 'PENDING' and not yet in a batch
  await orderStore.fetchOrders({ status: 'PENDING', payment_batch__isnull: true });
  await batchStore.fetchBatches();
});

const pendingOrders = computed(() => {
    // Further filter if backend doesn't do it precisely or if additional client-side checks needed
    return orderStore.ordersList.filter(order => order.status === 'PENDING' && !order.payment_batch);
});

const handleCreateBatch = async () => {
  if (selectedOrderIds.value.length === 0) {
    alert('Please select at least one order to batch.');
    return;
  }
  try {
    const createdBatchData = await batchStore.createBatch(selectedOrderIds.value);
    selectedOrderIds.value = []; // Clear selection
    // The store action already adds to batchesList, so UI should update.
    // Optionally, navigate to the newly created batch details page
    // This depends on whether createBatch returns one batch or potentially multiple.
    // Assuming it returns an array of created batches (as per backend logic for splitting)
    if (createdBatchData && createdBatchData.length > 0) {
        // For simplicity, navigate to the first created batch if multiple were made
        router.push({ name: 'BatchStatus', params: { id: createdBatchData[0].id } });
    } else if (createdBatchData) { // Single object returned
         router.push({ name: 'BatchStatus', params: { id: createdBatchData.id } });
    }
    // Re-fetch orders to update the list of pending orders
    await orderStore.fetchOrders({ status: 'PENDING', payment_batch__isnull: true });

  } catch (error) {
    // Error is already set in the store, or display a notification
    console.error('Failed to create batch from view:', error);
  }
};
</script>

<style scoped>
.batch-payment-view {
  max-width: 800px;
  margin: 20px auto;
}
.order-selection-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
  padding: 10px;
  margin-bottom: 10px;
}
.order-item {
  padding: 5px 0;
  border-bottom: 1px dashed #f0f0f0;
}
.order-item:last-child {
  border-bottom: none;
}
.order-item label {
  margin-left: 8px;
  font-size: 0.9em;
}
.batch-list {
  list-style-type: none;
  padding: 0;
}
.batch-item {
  background-color: #f9f9f9;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}
.batch-item small {
    display: block;
    color: #666;
    font-size: 0.8em;
}
/* Using global styles for card, btn, error-message */
</style>
