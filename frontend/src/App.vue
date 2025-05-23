<template>
  <div id="app-container">
    <Navbar v-if="showNavbar" />
    <main class="container">
      <router-view />
    </main>
    <footer class="footer">
      <p>&copy; 2024 Payment System App</p>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import Navbar from './components/Navbar.vue'; // Will be created

const route = useRoute();

// Only show Navbar if not on the login page (or other specific routes)
// This assumes your login route will have the name 'Login'.
const showNavbar = computed(() => route.name !== 'Login'); 
</script>

<style scoped>
#app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f4f7f6; /* Light background for the whole page */
}

.container {
  flex: 1;
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto; /* Center content */
  width: 100%;
}

.footer {
  text-align: center;
  padding: 10px 0;
  background-color: #333;
  color: white;
  font-size: 0.9em;
  margin-top: auto; /* Push footer to the bottom */
}
</style>
