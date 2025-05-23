import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import OrderList from '../OrderList.vue'; // Adjust path as needed
import { RouterLink } from 'vue-router'; // To properly stub RouterLink

describe('OrderList.vue', () => {
  const mockOrders = [
    { id: 1, order_uid: 'uid1', amount: '100.00', currency: 'USD', status: 'PENDING', product_description: 'Item 1', created_at: new Date().toISOString(), payment_batch: null },
    { id: 2, order_uid: 'uid2', amount: '150.50', currency: 'EUR', status: 'SUCCESS', product_description: 'Item 2', created_at: new Date().toISOString(), payment_batch: 101 },
  ];

  it('renders a list of orders correctly', () => {
    const wrapper = mount(OrderList, {
      props: {
        orders: mockOrders,
        title: 'My Orders',
      },
      global: {
        stubs: { // Stub RouterLink to avoid warnings/errors related to router context
          RouterLink: RouterLink, // Use the actual RouterLink but it won't navigate in test
          // Or a simpler stub: 'router-link': { template: '<a><slot /></a>' }
        },
      },
    });

    expect(wrapper.find('h3').text()).toBe('My Orders');
    const rows = wrapper.findAll('.orders-table tbody tr');
    expect(rows.length).toBe(mockOrders.length);

    // Check data in the first row
    const firstRowCells = rows[0].findAll('td');
    expect(firstRowCells[0].text()).toContain(mockOrders[0].order_uid.substring(0, 8));
    expect(firstRowCells[1].text()).toBe(mockOrders[0].amount);
    expect(firstRowCells[2].text()).toBe(mockOrders[0].currency);
    expect(firstRowCells[3].find('.status-badge').text()).toBe(mockOrders[0].status);
    expect(firstRowCells[3].find('.status-badge').classes()).toContain(`status-${mockOrders[0].status.toLowerCase()}`);
    expect(firstRowCells[4].text()).toBe(mockOrders[0].product_description);
    expect(firstRowCells[5].text()).toBe(new Date(mockOrders[0].created_at).toLocaleDateString());
  });

  it('renders "no orders" message when orders prop is empty', () => {
    const wrapper = mount(OrderList, {
      props: {
        orders: [],
        emptyListMessage: 'No items to display.',
      },
      global: {
        stubs: { RouterLink: true },
      },
    });

    expect(wrapper.find('.no-orders-message').exists()).toBe(true);
    expect(wrapper.find('.no-orders-message p').text()).toBe('No items to display.');
    expect(wrapper.find('.orders-table').exists()).toBe(false);
  });

  it('shows batch information when showBatchInfo is true', () => {
    const wrapper = mount(OrderList, {
      props: {
        orders: [mockOrders[1]], // Order with a payment_batch ID
        showBatchInfo: true,
      },
      global: {
        stubs: { RouterLink: RouterLink }, // Use actual or more functional stub for RouterLink if checking `to` prop
      },
    });
    const batchCell = wrapper.find('.orders-table tbody tr td:last-child');
    expect(batchCell.exists()).toBe(true);
    // Check if RouterLink for batch is present and has correct `to` prop
    const batchLink = batchCell.findComponent(RouterLink);
    expect(batchLink.exists()).toBe(true);
    expect(batchLink.props().to).toEqual({ name: 'BatchStatus', params: { id: mockOrders[1].payment_batch } });
    expect(batchLink.text()).toContain(`Batch #${mockOrders[1].payment_batch}`);
  });
  
  it('does not show batch information when showBatchInfo is false or order has no batch', () => {
    const wrapper = mount(OrderList, {
      props: {
        orders: [mockOrders[0]], // Order without a payment_batch ID
        showBatchInfo: true, // Even if true, should show N/A
      },
       global: {
        stubs: { RouterLink: true },
      },
    });
    const batchCell = wrapper.find('.orders-table tbody tr td:last-child');
    expect(batchCell.exists()).toBe(true); // Column still exists
    expect(batchCell.text()).toBe('N/A'); // Content is N/A
    expect(batchCell.findComponent(RouterLink).exists()).toBe(false); // No link
  });

  it('renders links to order details if linkToDetails is true', () => {
    const wrapper = mount(OrderList, {
        props: {
            orders: [mockOrders[0]],
            linkToDetails: true,
            orderDetailsRouteName: 'TestOrderDetailsPage'
        },
        global: {
            stubs: { RouterLink: RouterLink }
        }
    });
    const orderUidCell = wrapper.find('.orders-table tbody tr td:first-child');
    const link = orderUidCell.findComponent(RouterLink);
    expect(link.exists()).toBe(true);
    expect(link.props().to).toEqual({ name: 'TestOrderDetailsPage', params: { id: mockOrders[0].id } });
  });
});
