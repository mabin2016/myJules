<template>
  <div class="not-found-view card text-center">
    <h1 class="card-header">404 - Page Not Found</h1>
    <p>Oops! The page you are looking for does not exist.</p>
    <p>You can <router-link to="/">go back to the homepage</router-link>.</p>
  </div>
</template>

<script setup>
// No specific script setup needed for this simple component
</script>

<style scoped>
.not-found-view {
  max-width: 500px;
  margin: 50px auto;
  padding: 30px;
}
.not-found-view h1 {
  font-size: 2.5em;
  color: #dc3545; /* Bootstrap danger color for emphasis */
}
.not-found-view p {
  font-size: 1.1em;
  margin-bottom: 20px;
}
/* Using global styles for card, text-center */
</style>
