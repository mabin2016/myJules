import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Will be created in a later step
import { createPinia } from 'pinia';
import './assets/css/main.css'; // Will be created

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

app.mount('#app');
