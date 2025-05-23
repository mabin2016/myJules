import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useRouter } from 'vue-router'; // To mock
import LoginView from '../LoginView.vue'; // Adjust path as needed
import { useAuthStore } from '../../store/auth'; // Adjust path

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(), // Mock push method
  })),
  useRoute: vi.fn(() => ({ // Mock useRoute for route.query.redirect
    query: {}, 
  })),
  RouterLink: { template: '<a><slot /></a>' } // Stub RouterLink
}));

describe('LoginView.vue', () => {
  let pinia;
  let mockRouter;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    
    // Setup mock router for each test
    mockRouter = {
      push: vi.fn(),
    };
    useRouter.mockReturnValue(mockRouter); // Ensure useRouter returns the fresh mock
  });

  it('renders the login form correctly', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [pinia],
        stubs: { // Stubbing router-link if it causes issues without full router setup
            'router-link': { template: '<a><slot></slot></a>' }
        }
      },
    });

    expect(wrapper.find('h2').text()).toBe('Login');
    expect(wrapper.find('label[for="username"]').exists()).toBe(true);
    expect(wrapper.find('input#username').exists()).toBe(true);
    expect(wrapper.find('label[for="password"]').exists()).toBe(true);
    expect(wrapper.find('input#password').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').text()).toBe('Login');
  });

  it('updates username and password fields on input', async () => {
    const wrapper = mount(LoginView, { global: { plugins: [pinia], stubs: {'router-link': true} } });
    const usernameInput = wrapper.find('input#username');
    const passwordInput = wrapper.find('input#password');

    await usernameInput.setValue('testuser');
    await passwordInput.setValue('password123');

    // In Vue 3 with <script setup>, accessing component instance for data is not direct.
    // We test by checking if the store action is called with these values.
    // For this unit test, we confirm input values are set.
    expect(usernameInput.element.value).toBe('testuser');
    expect(passwordInput.element.value).toBe('password123');
  });

  it('calls authStore.login on form submission and redirects on success', async () => {
    const authStore = useAuthStore();
    // Spy on the login action, and mock its implementation
    vi.spyOn(authStore, 'login').mockResolvedValue(true); 

    const wrapper = mount(LoginView, { global: { plugins: [pinia], stubs: {'router-link': true} } });

    await wrapper.find('input#username').setValue('testuser');
    await wrapper.find('input#password').setValue('password123');
    await wrapper.find('form').trigger('submit.prevent');

    expect(authStore.login).toHaveBeenCalledWith({ username: 'testuser', password: 'password123' });
    // Ensure that the router.push was called, e.g., to redirect to dashboard
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard'); // Default redirect
  });
  
  it('calls authStore.login and redirects to query param on success', async () => {
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'login').mockResolvedValue(true);
    
    // Mock useRoute to return a specific redirect query
    useRoute.mockReturnValueOnce({ query: { redirect: '/intended-page' } });

    const wrapper = mount(LoginView, { global: { plugins: [pinia], stubs: {'router-link': true} } });

    await wrapper.find('input#username').setValue('testuser');
    await wrapper.find('input#password').setValue('password123');
    await wrapper.find('form').trigger('submit.prevent');
    
    expect(authStore.login).toHaveBeenCalledTimes(1);
    expect(mockRouter.push).toHaveBeenCalledWith('/intended-page');
  });


  it('displays error message from authStore on login failure', async () => {
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'login').mockResolvedValue(false); // Simulate login failure
    authStore.loginError = 'Invalid credentials provided.'; // Manually set error for this test

    const wrapper = mount(LoginView, { global: { plugins: [pinia], stubs: {'router-link': true} } });

    await wrapper.find('input#username').setValue('testuser');
    await wrapper.find('input#password').setValue('wrongpassword');
    await wrapper.find('form').trigger('submit.prevent');

    // Wait for DOM update if error message rendering is conditional
    await wrapper.vm.$nextTick(); 

    const errorMessageElement = wrapper.find('.error-message');
    expect(errorMessageElement.exists()).toBe(true);
    expect(errorMessageElement.text()).toContain('Invalid credentials provided.');
    expect(mockRouter.push).not.toHaveBeenCalled();
  });

  it('disables login button when authStore.loading is true', async () => {
    const authStore = useAuthStore();
    authStore.loading = true; // Simulate loading state

    const wrapper = mount(LoginView, { global: { plugins: [pinia], stubs: {'router-link': true} } });
    
    const loginButton = wrapper.find('button[type="submit"]');
    expect(loginButton.attributes('disabled')).toBeDefined();
    expect(loginButton.text()).toBe('Logging in...');

    authStore.loading = false; // Reset for other tests
  });
});
