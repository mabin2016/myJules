<template>
  <div class="login-view card">
    <h2 class="card-header">Login</h2>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="username">Username (or Email):</label>
        <input type="text" id="username" v-model="username" required />
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="password" required />
      </div>
      <button type="submit" class="btn" :disabled="authStore.loading">
        {{ authStore.loading ? 'Logging in...' : 'Login' }}
      </button>
      <p v.if="authStore.loginError" class="error-message">
        {{ authStore.loginError }}
      </p>
    </form>
    <p class="mt-2">
      Don't have an account? <router-link to="/register">Register here</router-link>
      <!-- Registration view/route would need to be added if not present -->
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../store/auth';

const username = ref(''); // Can be username or email depending on backend
const password = ref('');
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const handleLogin = async () => {
  const success = await authStore.login({ username: username.value, password: password.value });
  if (success) {
    // Redirect to dashboard or intended page after login
    const redirectPath = route.query.redirect || '/dashboard';
    router.push(redirectPath);
  }
};
</script>

<style scoped>
.login-view {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
}
</style>
