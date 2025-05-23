import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { useRouter, RouterLink } from 'vue-router'; // To mock RouterLink and useRouter
import Navbar from '../Navbar.vue'; // Adjust path as needed
import { useAuthStore } from '../../store/auth'; // Adjust path

// Mock vue-router
vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
  })),
  RouterLink: { // Simple stub for RouterLink
    name: 'RouterLink',
    props: ['to'],
    template: '<a :href="to"><slot></slot></a>',
  }
}));

describe('Navbar.vue', () => {
  let pinia;
  let mockRouterPush;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    
    mockRouterPush = vi.fn();
    useRouter.mockReturnValue({ push: mockRouterPush });
  });

  it('renders brand and login button when not authenticated', () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = false; // Ensure not authenticated

    const wrapper = mount(Navbar, {
      global: {
        plugins: [pinia],
        // stubs: { RouterLink: true } // Use the mock from vi.mock instead
      },
    });

    expect(wrapper.find('.brand-text').text()).toBe('PaymentSys');
    expect(wrapper.find('.navbar-item[to="/dashboard"]').exists()).toBe(false); // No dashboard link
    expect(wrapper.find('.btn-logout').exists()).toBe(false); // No logout button
    expect(wrapper.find('.btn').text()).toBe('Login'); // Login button visible
    const loginLink = wrapper.findAllComponents(RouterLink).find(rl => rl.props().to === '/login');
    expect(loginLink.exists()).toBe(true);
  });

  it('renders dashboard, other links, user info, and logout button when authenticated', () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = true;
    authStore.user = { username: 'testuser', email: 'test@example.com' };

    const wrapper = mount(Navbar, {
      global: {
        plugins: [pinia],
      },
    });

    expect(wrapper.find('.navbar-item[to="/dashboard"]').exists()).toBe(true);
    expect(wrapper.find('.navbar-item[to="/orders/create"]').exists()).toBe(true);
    expect(wrapper.find('.navbar-item[to="/batches"]').exists()).toBe(true);
    
    expect(wrapper.find('.navbar-item span strong').text()).toBe('testuser');
    expect(wrapper.find('.btn-logout').exists()).toBe(true);
    expect(wrapper.find('.btn[to="/login"]').exists()).toBe(false); // No login button
  });

  it('calls authStore.logout and redirects to /login on logout button click', async () => {
    const authStore = useAuthStore();
    authStore.isAuthenticated = true;
    authStore.user = { username: 'testuser' };
    // Spy on the logout action
    vi.spyOn(authStore, 'logout');

    const wrapper = mount(Navbar, {
      global: {
        plugins: [pinia],
      },
    });

    const logoutButton = wrapper.find('.btn-logout');
    await logoutButton.trigger('click');

    expect(authStore.logout).toHaveBeenCalledTimes(1);
    expect(mockRouterPush).toHaveBeenCalledWith('/login');
  });
});
