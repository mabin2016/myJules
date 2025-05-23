<template>
  <div class="dashboard-view card">
    <h2 class="card-header">Dashboard</h2>
    <div v-if="authStore.isAuthenticated && authStore.user">
      <p>Welcome, <strong>{{ authStore.user.username }}</strong>!</p>
      <p>Email: {{ authStore.user.email }}</p>
      <p>User ID: {{ authStore.user.id }}</p>
      <p>Token: <small>{{ authStore.token ? authStore.token.substring(0, 30) + '...' : 'N/A' }}</small></p>
    </div>
    <div v-else>
      <p>Loading user data or not logged in.</p>
    </div>

    <div class="dashboard-actions mt-2">
      <router-link to="/orders/create" class="btn">Create New Order</router-link>
      <router-link to="/batches" class="btn btn-secondary ml-1">View Payment Batches</router-link>
    </div>

    <div class="mt-2">
        <h3>Recent Activity (Placeholder)</h3>
        <p><em>This section will display recent orders or batch statuses.</em></p>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../store/auth';
import { onMounted } from 'vue';

const authStore = useAuthStore();

onMounted(() => {
  // Ensure user data is fresh if needed, or rely on initial checkAuth
  if (!authStore.user && authStore.isAuthenticated) {
    // Potentially call an action to fetch user details if not fully loaded during login/checkAuth
    // authStore.fetchCurrentUser(); // Example: if such an action exists
    console.log('Dashboard mounted, user data might be loading or is already present.');
  }
});
</script>

<style scoped>
.dashboard-view p {
  margin-bottom: 0.5rem;
}
.dashboard-actions .btn {
  margin-right: 10px;
}
.ml-1 {
    margin-left: 0.5rem;
}
</style>
