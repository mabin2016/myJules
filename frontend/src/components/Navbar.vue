<template>
  <nav class="navbar">
    <div class="navbar-brand">
      <router-link to="/" class="navbar-item brand-text">PaymentSys</router-link>
    </div>
    <div class="navbar-menu">
      <div class="navbar-start">
        <router-link to="/dashboard" class="navbar-item" v-if="authStore.isAuthenticated">Dashboard</router-link>
        <router-link to="/orders/create" class="navbar-item" v-if="authStore.isAuthenticated">Create Order</router-link>
        <router-link to="/batches" class="navbar-item" v-if="authStore.isAuthenticated">Payment Batches</router-link>
      </div>
      <div class="navbar-end">
        <div class="navbar-item" v-if="authStore.isAuthenticated">
          <span>Logged in as: <strong>{{ authStore.user?.username }}</strong></span>
        </div>
        <div class="navbar-item">
          <button v-if="authStore.isAuthenticated" @click="handleLogout" class="btn btn-logout">Logout</button>
          <router-link v-else to="/login" class="btn">Login</router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const handleLogout = () => {
  authStore.logout();
  router.push('/login'); // Redirect to login page after logout
};
</script>

<style scoped>
.navbar {
  background-color: #333; /* Dark background for navbar */
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}
.navbar-brand .brand-text {
  font-size: 1.5em;
  font-weight: bold;
  color: white;
}
.navbar-menu {
  display: flex;
  align-items: center;
}
.navbar-start, .navbar-end {
  display: flex;
  align-items: center;
}
.navbar-item {
  color: #ddd; /* Lighter text for items */
  padding: 0.5rem 0.75rem;
  text-decoration: none;
  transition: color 0.3s ease, background-color 0.3s ease;
}
.navbar-item:hover,
.navbar-item.router-link-active, /* Active link styling */
.navbar-item.router-link-exact-active {
  color: white;
  background-color: #555; /* Slightly darker background on hover/active */
}
.navbar-item span {
    margin-right: 15px;
    font-size: 0.9em;
}
.btn-logout {
  background-color: #dc3545; /* Red for logout */
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}
.btn-logout:hover {
  background-color: #c82333;
}
</style>
