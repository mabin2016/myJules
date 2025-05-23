<template>
  <div class="batch-status-view">
    <div v-if="batchStore.loading" class="loading">Loading batch details...</div>
    <div v-if="batchStore.error" class="error-message card">
      Error fetching batch details: {{ batchStore.error.message || batchStore.error }}
    </div>
    
    <div v-if="batchDetails" class="card">
      <h2 class="card-header">Batch Status: {{ batchDetails.batch_uid }}</h2>
      <p><strong>Status:</strong> {{ batchDetails.status }}</p>
      <p><strong>Total Amount:</strong> {{ batchDetails.total_amount }}</p>
      <p><strong>Total Orders:</strong> {{ batchDetails.total_orders }}</p>
      <p><strong>Successful Orders:</strong> {{ batchDetails.successful_orders }}</p>
      <p><strong>Failed Orders:</strong> {{ batchDetails.failed_orders }}</p>
      <p><strong>Processed Orders:</strong> {{ batchDetails.processed_orders }}</p>
      <p><strong>Created At:</strong> {{ new Date(batchDetails.created_at).toLocaleString() }}</p>
      <p v-if="batchDetails.alipay_batch_no"><strong>Alipay Batch No:</strong> {{ batchDetails.alipay_batch_no }}</p>
      <p v-if="batchDetails.processing_started_at"><strong>Processing Started:</strong> {{ new Date(batchDetails.processing_started_at).toLocaleString() }}</p>
      <p v-if="batchDetails.completed_at"><strong>Completed At:</strong> {{ new Date(batchDetails.completed_at).toLocaleString() }}</p>

      <div class="actions mt-2">
        <button 
          @click="triggerPayment" 
          class="btn" 
          :disabled="batchStore.loading || !canTriggerPayment"
          v-if="canTriggerPayment">
          {{ batchStore.loading ? 'Processing...' : 'Trigger/Retry Payment for this Batch' }}
        </button>
         <div v.if="batchStore.triggerPaymentError" class="error-message mt-1">
            Error triggering payment: {{ batchStore.triggerPaymentError.message || batchStore.triggerPaymentError }}
        </div>
        <button @click="refreshDetails" class="btn btn-secondary ml-1" :disabled="batchStore.loading">
            Refresh Status
        </button>
      </div>

      <div v.if="batchDetails.orders && batchDetails.orders.length > 0" class="mt-2">
        <h3>Orders in this Batch:</h3>
        <OrderList :orders="batchDetails.orders" />
      </div>
    </div>
    <div v-else-if="!batchStore.loading && !batchStore.error">
      <p>No batch details found for this ID, or batch does not exist.</p>
    </div>
     <router-link to="/batches" class="btn btn-secondary mt-2">Back to Batch List</router-link>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useBatchStore } from '../store/batches';
import OrderList from '../components/OrderList.vue'; // Will be created

const route = useRoute();
const batchStore = useBatchStore();
const batchId = ref(route.params.id);

const batchDetails = computed(() => batchStore.currentBatchDetails);

const canTriggerPayment = computed(() => {
  if (!batchDetails.value) return false;
  return ['PENDING_PROCESSING', 'FAILED', 'PARTIALLY_COMPLETED', 'RETRY_PROCESSING'].includes(batchDetails.value.status);
});

const fetchDetails = async () => {
  if (batchId.value) {
    await batchStore.fetchBatchDetails(batchId.value);
  }
};

const refreshDetails = async () => {
    await fetchDetails();
};

const triggerPayment = async () => {
  if (!batchId.value) return;
  try {
    await batchStore.triggerBatchPayment(batchId.value);
    // After triggering, refresh details to show updated status/task ID
    await fetchDetails(); 
  } catch (error) {
    // Error is already set in the store
    console.error('Failed to trigger batch payment from view:', error);
  }
};

onMounted(() => {
  fetchDetails();
});

// Watch for route param changes if user navigates from one batch detail to another directly (less common)
watch(() => route.params.id, (newId) => {
  if (newId) {
    batchId.value = newId;
    fetchDetails();
  }
});
</script>

<style scoped>
.batch-status-view {
  max-width: 900px;
  margin: 20px auto;
}
.loading {
  text-align: center;
  padding: 20px;
}
.actions .btn {
    margin-right: 10px;
}
.ml-1 {
    margin-left: 0.5rem;
}
/* Using global styles for card, btn, error-message */
</style>
