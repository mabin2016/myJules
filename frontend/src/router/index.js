import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../store/auth'; // Assuming Pinia store is set up

// Import views (skeletons will be created later)
// For now, use dummy components or assume they will exist.
// To avoid import errors before views are created, we can define them as () => import(...)
const LoginView = () => import('../views/LoginView.vue');
const DashboardView = () => import('../views/DashboardView.vue');
const CreateOrderView = () => import('../views/CreateOrderView.vue');
const BatchPaymentView = () => import('../views/BatchPaymentView.vue');
const BatchStatusView = () => import('../views/BatchStatusView.vue');
// A generic NotFound component is good practice
const NotFoundView = () => import('../views/NotFoundView.vue'); // Create this view as well

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresGuest: true }, // Only accessible if not authenticated
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/orders/create',
    name: 'CreateOrder',
    component: CreateOrderView,
    meta: { requiresAuth: true },
  },
  {
    path: '/batches',
    name: 'BatchPayment',
    component: BatchPaymentView,
    meta: { requiresAuth: true },
  },
  {
    path: '/batches/:id', // Route parameter for batch ID
    name: 'BatchStatus',
    component: BatchStatusView,
    props: true, // Pass route params as props to the component
    meta: { requiresAuth: true },
  },
  {
    path: '/', // Redirect root to dashboard if logged in, else to login
    name: 'Home',
    redirect: () => {
      const authStore = useAuthStore();
      return authStore.isAuthenticated ? '/dashboard' : '/login';
    },
  },
  {
    path: '/:pathMatch(.*)*', // Catch-all for 404
    name: 'NotFound',
    component: NotFoundView,
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // Or just createWebHistory()
  routes,
});

// Navigation Guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  // Ensure auth state is checked (e.g., from localStorage) before processing routes
  // This might be redundant if checkAuth is called in App.vue on mount,
  // but good for direct route access.
  if (!authStore.token && localStorage.getItem('token')) {
     authStore.checkAuth(); // Initialize store from localStorage if available
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);

  if (requiresAuth && !authStore.isAuthenticated) {
    // If route requires auth and user is not authenticated, redirect to login
    next({ name: 'Login', query: { redirect: to.fullPath } }); // Save intended path
  } else if (requiresGuest && authStore.isAuthenticated) {
    // If route requires guest (like login page) and user is authenticated, redirect to dashboard
    next({ name: 'Dashboard' });
  } else {
    // Otherwise, proceed as normal
    next();
  }
});

export default router;
