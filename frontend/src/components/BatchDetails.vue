<template>
  <div class="batch-details-component card" v-if="batch">
    <h3 class="card-header">Batch Overview: {{ batch.batch_uid ? batch.batch_uid.substring(0,12) : 'N/A' }}...</h3>
    <div class="details-grid">
      <p><strong>Status:</strong> <span :class="`status-badge status-${batch.status.toLowerCase()}`">{{ batch.status }}</span></p>
      <p><strong>Total Amount:</strong> {{ batch.total_amount }}</p>
      <p><strong>Total Orders:</strong> {{ batch.total_orders }}</p>
      <p><strong>Successful Orders:</strong> {{ batch.successful_orders }}</p>
      <p><strong>Failed Orders:</strong> {{ batch.failed_orders }}</p>
      <p><strong>Processed Orders:</strong> {{ batch.processed_orders }}</p>
      <p><strong>Created By:</strong> {{ batch.created_by_user?.username || 'N/A' }}</p>
      <p><strong>Created At:</strong> {{ new Date(batch.created_at).toLocaleString() }}</p>
      <p v-if="batch.alipay_batch_no"><strong>Alipay Batch No:</strong> {{ batch.alipay_batch_no }}</p>
      <p v-if="batch.processing_started_at"><strong>Processing Started:</strong> {{ new Date(batch.processing_started_at).toLocaleString() }}</p>
      <p v-if="batch.completed_at"><strong>Completed At:</strong> {{ new Date(batch.completed_at).toLocaleString() }}</p>
    </div>

    <div v-if="batch.orders && batch.orders.length > 0" class="mt-2">
      <h4>Orders in this Batch:</h4>
      <!-- Re-using OrderList component -->
      <OrderList :orders="batch.orders" title="" emptyListMessage="No orders found in this batch." />
    </div>
     <div v-else class="mt-2">
        <p>No individual order details available for this batch in the current view.</p>
    </div>
  </div>
  <div v-else class="no-batch-data">
    <p>No batch data provided or batch is loading.</p>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import OrderList from './OrderList.vue'; // Assuming OrderList is in the same directory

const props = defineProps({
  batch: {
    type: Object,
    default: null, // Allow null if batch data is not yet loaded
  },
});
</script>

<style scoped>
.batch-details-component {
  /* Using global styles for card */
  margin-top: 20px;
}
.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}
.details-grid p {
  background-color: #f9f9f9;
  padding: 8px;
  border-radius: 4px;
  font-size: 0.9em;
  margin: 0;
}
.details-grid p strong {
  display: block;
  margin-bottom: 4px;
  color: #555;
}
.no-batch-data {
  padding: 20px;
  text-align: center;
  color: #777;
}

.status-badge {
  padding: 3px 6px;
  border-radius: 4px;
  color: white;
  font-size: 0.9em;
  text-transform: capitalize;
}
.status-pending_processing { background-color: #ffc107; color: #333; } /* Yellow */
.status-processing { background-color: #17a2b8; } /* Teal */
.status-completed { background-color: #28a745; } /* Green */
.status-partially_completed { background-color: #fd7e14; } /* Orange */
.status-failed { background-color: #dc3545; } /* Red */
.status-retry_processing { background-color: #6f42c1; } /* Indigo */
/* Add more status colors as needed */
</style>
