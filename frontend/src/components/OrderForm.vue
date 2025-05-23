<template>
  <form @submit.prevent="handleSubmit" class="order-form card">
    <h3 v.if="formTitle" class="card-header">{{ formTitle }}</h3>
    
    <div class="form-group">
      <label for="order-amount">Amount:</label>
      <input 
        type="number" 
        id="order-amount" 
        v-model.number="formData.amount" 
        required 
        step="0.01" 
        min="0.01" 
        placeholder="Enter amount" 
      />
    </div>
    
    <div class="form-group">
      <label for="order-currency">Currency:</label>
      <input 
        type="text" 
        id="order-currency" 
        v-model.trim="formData.currency" 
        required 
        maxlength="3" 
        placeholder="e.g., CNY, USD" 
      />
    </div>
    
    <div class="form-group">
      <label for="order-description">Product Description:</label>
      <textarea 
        id="order-description" 
        v-model.trim="formData.product_description" 
        rows="3"
        placeholder="Describe the product or service"
      ></textarea>
    </div>
    
    <button type="submit" class="btn" :disabled="isLoading">
      {{ isLoading ? 'Submitting...' : submitButtonText }}
    </button>
    
    <div v.if="error" class="error-message mt-2">
      <p>Error: {{ error.message || error }}</p>
    </div>
  </form>
</template>

<script setup>
import { ref, reactive, watch } from 'vue';

const props = defineProps({
  initialData: {
    type: Object,
    default: () => ({
      amount: null,
      currency: 'CNY',
      product_description: '',
    }),
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: [Object, String],
    default: null,
  },
  submitButtonText: {
    type: String,
    default: 'Submit Order',
  },
  formTitle: {
    type: String,
    default: 'Order Details'
  }
});

const emit = defineEmits(['submit']);

const formData = reactive({ ...props.initialData });

// Watch for changes in initialData if the form needs to be reset or updated from parent
watch(() => props.initialData, (newData) => {
  Object.assign(formData, newData);
}, { deep: true });

const handleSubmit = () => {
  if (!formData.amount || !formData.currency) {
    // Basic local validation, more robust validation can be added
    alert('Amount and Currency are required.');
    return;
  }
  emit('submit', { ...formData });
};
</script>

<style scoped>
.order-form {
  /* Using global styles for card, form-group, btn, error-message */
  /* Add specific styles for OrderForm if needed */
  padding: 20px;
}
</style>
