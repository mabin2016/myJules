<template>
  <div class="order-list">
    <h3 v.if="title">{{ title }}</h3>
    <div v.if="!orders || orders.length === 0" class="no-orders-message">
      <p>{{ emptyListMessage }}</p>
    </div>
    <table v.else class="orders-table">
      <thead>
        <tr>
          <th>Order UID</th>
          <th>Amount</th>
          <th>Currency</th>
          <th>Status</th>
          <th>Description</th>
          <th>Created At</th>
          <th v.if="showBatchInfo">Batch UID</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="order in orders" :key="order.id" class="order-row">
          <td>
            <router-link v-if="linkToDetails" :to="getOrderDetailsLink(order)">
              {{ order.order_uid ? order.order_uid.substring(0, 8) : 'N/A' }}...
            </router-link>
            <span v-else>{{ order.order_uid ? order.order_uid.substring(0, 8) : 'N/A' }}...</span>
          </td>
          <td>{{ order.amount }}</td>
          <td>{{ order.currency }}</td>
          <td><span :class="['status-badge', `status-${order.status.toLowerCase()}`]">{{ order.status }}</span></td>
          <td>{{ order.product_description || 'N/A' }}</td>
          <td>{{ new Date(order.created_at).toLocaleDateString() }}</td>
          <td v-if="showBatchInfo">
            <router-link v-if="order.payment_batch" :to="{ name: 'BatchStatus', params: { id: order.payment_batch } }">
              Batch #{{ order.payment_batch }}
            </router-link>
            <span v-else>N/A</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  orders: {
    type: Array,
    required: true,
    default: () => [],
  },
  title: {
    type: String,
    default: 'Orders',
  },
  emptyListMessage: {
    type: String,
    default: 'No orders found.',
  },
  linkToDetails: { // Whether to link order UIDs to a details page (if one exists)
    type: Boolean,
    default: false, // Assuming no separate order detail view for now
  },
  orderDetailsRouteName: { // Name of the route for order details
      type: String,
      default: 'OrderDetails' // Placeholder, adjust if you have such a route
  },
  showBatchInfo: {
      type: Boolean,
      default: false,
  }
});

const getOrderDetailsLink = (order) => {
  if (!props.orderDetailsRouteName) return {};
  return { name: props.orderDetailsRouteName, params: { id: order.id } };
};
</script>

<style scoped>
.order-list {
  margin-top: 20px;
}
.orders-table {
  width: 100%;
  border-collapse: collapse;
}
.orders-table th, .orders-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
  font-size: 0.9em;
}
.orders-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}
.order-row:nth-child(even) {
  background-color: #f9f9f9;
}
.order-row:hover {
  background-color: #f1f1f1;
}
.no-orders-message {
  text-align: center;
  padding: 20px;
  color: #777;
}
.status-badge {
  padding: 3px 6px;
  border-radius: 4px;
  color: white;
  font-size: 0.85em;
  text-transform: capitalize;
}
.status-pending { background-color: #ffc107; color: #333; } /* Yellow */
.status-processing { background-color: #17a2b8; } /* Teal */
.status-success { background-color: #28a745; } /* Green */
.status-failed { background-color: #dc3545; } /* Red */
.status-refunded { background-color: #6c757d; } /* Gray */
/* Add more status colors as needed */
</style>
