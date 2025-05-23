<template>
  <div class="create-order-view card">
    <h2 class="card-header">Create New Order</h2>
    <form @submit.prevent="submitOrder">
      <div class="form-group">
        <label for="amount">Amount:</label>
        <input type="number" id="amount" v-model.number="orderData.amount" required step="0.01" min="0.01" />
      </div>
      <div class="form-group">
        <label for="currency">Currency:</label>
        <input type="text" id="currency" v-model="orderData.currency" required maxlength="3" placeholder="e.g., CNY, USD" />
      </div>
      <div class="form-group">
        <label for="product_description">Product Description:</label>
        <textarea id="product_description" v-model="orderData.product_description" rows="3"></textarea>
      </div>
      
      <button type="submit" class="btn" :disabled="orderStore.loading">
        {{ orderStore.loading ? 'Creating...' : 'Create Order' }}
      </button>
      
      <div v.if="orderStore.error" class="error-message mt-2">
        <p>Error creating order:</p>
        <pre>{{ orderStore.error }}</pre>
      </div>
       <div v.if="creationSuccess" class="alert alert-success mt-2">
        Order created successfully! Order ID: {{ createdOrderId }}
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useOrderStore } from '../store/orders';
import { useRouter } from 'vue-router';

const orderStore = useOrderStore();
const router = useRouter();

const orderData = reactive({
  amount: null,
  currency: 'CNY', // Default currency
  product_description: '',
});

const creationSuccess = ref(false);
const createdOrderId = ref(null);

const submitOrder = async () => {
  creationSuccess.value = false;
  createdOrderId.value = null;
  if (!orderData.amount || !orderData.currency) {
    orderStore.error = { message: "Amount and Currency are required." }; // Temporary error display
    return;
  }
  try {
    const newOrder = await orderStore.createOrder(orderData);
    creationSuccess.value = true;
    createdOrderId.value = newOrder.id; // Assuming API returns the created order with its ID
    // Reset form or redirect
    orderData.amount = null;
    orderData.currency = 'CNY';
    orderData.product_description = '';
    // Optionally redirect to order details page or dashboard
    // router.push({ name: 'Dashboard' }); 
    // Or router.push({ name: 'OrderDetails', params: { id: newOrder.id } }); // If such route exists
  } catch (error) {
    // Error is already set in the store, or can be handled here
    console.error('Failed to create order:', error);
    creationSuccess.value = false;
  }
};
</script>

<style scoped>
.create-order-view {
  max-width: 600px;
  margin: 20px auto;
}
/* Using global styles for form-group, btn, error-message, card */
</style>
