## Database Schema for Payment System

This document outlines the database schema for the payment system.

### Relationships:

*   **`users` to `orders`**: One-to-Many (One user can have multiple orders)
*   **`users` to `payment_batches`**: One-to-Many (One user can create multiple payment batches)
*   **`payment_batches` to `orders`**: One-to-Many (One payment batch can contain multiple orders)
*   **`orders` to `payment_transactions`**: One-to-Many (One order can have multiple payment transaction attempts)
*   **`payment_batches` to `payment_transactions`**: One-to-Many (Transactions within a batch can be linked back to the batch)

---

### Table: `users`

Stores information about users.

| Column Name     | Data Type          | Constraints                                                                 | Description                     |
|-----------------|--------------------|-----------------------------------------------------------------------------|---------------------------------|
| `id`            | INT AUTO_INCREMENT | PRIMARY KEY                                                                 | Unique identifier for the user. |
| `username`      | VARCHAR(255)       | NOT NULL, UNIQUE                                                            | User's chosen username.         |
| `password_hash` | VARCHAR(255)       | NOT NULL                                                                    | Hashed password for security.   |
| `email`         | VARCHAR(255)       | NOT NULL, UNIQUE                                                            | User's email address.           |
| `created_at`    | TIMESTAMP          | NOT NULL, DEFAULT CURRENT_TIMESTAMP                                         | Timestamp of user creation.     |
| `updated_at`    | TIMESTAMP          | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP             | Timestamp of last user update.  |

**Indexes:**
*   `idx_users_email` ON `email`
*   `idx_users_username` ON `username`

---

### Table: `payment_batches`

Stores information about payment batches, which group multiple orders for processing.

| Column Name             | Data Type                             | Constraints                                                                 | Description                                            |
|-------------------------|---------------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------|
| `id`                    | INT AUTO_INCREMENT                    | PRIMARY KEY                                                                 | Unique identifier for the payment batch.               |
| `batch_uid`             | UUID                                  | NOT NULL, UNIQUE                                                            | Unique identifier for external reference.              |
| `status`                | VARCHAR(50)                           | NOT NULL, DEFAULT 'PENDING_PROCESSING'                                      | Current status of the batch (e.g., 'PENDING_PROCESSING', 'PROCESSING', 'PARTIALLY_COMPLETED', 'COMPLETED', 'FAILED'). |
| `total_amount`          | DECIMAL(15, 2)                        | NOT NULL                                                                    | Sum of amounts of all orders in the batch.             |
| `total_orders`          | INT                                   | NOT NULL                                                                    | Total number of orders in this batch.                  |
| `processed_orders`      | INT                                   | NOT NULL, DEFAULT 0                                                         | Number of orders processed so far.                     |
| `successful_orders`     | INT                                   | NOT NULL, DEFAULT 0                                                         | Number of successfully paid orders.                    |
| `failed_orders`         | INT                                   | NOT NULL, DEFAULT 0                                                         | Number of failed orders.                               |
| `alipay_batch_no`       | VARCHAR(255)                          | NULL, UNIQUE                                                                | Alipay's transaction ID for the batch payment.         |
| `alipay_notify_data`    | JSON                                  | NULL                                                                        | Raw notification data from Alipay for the batch.       |
| `created_by_user_id`    | INT                                   | NOT NULL, FOREIGN KEY (`created_by_user_id`) REFERENCES `users`(`id`)       | User who created this batch.                           |
| `created_at`            | TIMESTAMP                             | NOT NULL, DEFAULT CURRENT_TIMESTAMP                                         | Timestamp of batch creation.                           |
| `updated_at`            | TIMESTAMP                             | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP             | Timestamp of last batch update.                        |
| `processing_started_at` | TIMESTAMP                             | NULL                                                                        | Timestamp when batch processing began.                 |
| `completed_at`          | TIMESTAMP                             | NULL                                                                        | Timestamp when batch processing completed.             |

**Indexes:**
*   `idx_payment_batches_batch_uid` ON `batch_uid`
*   `idx_payment_batches_status` ON `status`
*   `idx_payment_batches_alipay_batch_no` ON `alipay_batch_no`
*   `idx_payment_batches_created_by_user_id` ON `created_by_user_id`

---

### Table: `orders`

Stores information about individual payment orders.

| Column Name           | Data Type        | Constraints                                                                 | Description                                                                  |
|-----------------------|------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `id`                  | INT AUTO_INCREMENT | PRIMARY KEY                                                                 | Unique identifier for the order.                                             |
| `order_uid`           | UUID             | NOT NULL, UNIQUE                                                            | Unique identifier for external reference.                                    |
| `user_id`             | INT              | NOT NULL, FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)                  | User who placed the order.                                                   |
| `amount`              | DECIMAL(10, 2)   | NOT NULL                                                                    | Payment amount for this order.                                               |
| `currency`            | VARCHAR(3)       | NOT NULL, DEFAULT 'CNY'                                                     | Currency code (e.g., 'CNY', 'USD').                                          |
| `status`              | VARCHAR(50)      | NOT NULL, DEFAULT 'PENDING'                                                 | Status of the order (e.g., 'PENDING', 'PROCESSING', 'SUCCESS', 'FAILED', 'REFUNDED'). |
| `product_description` | TEXT             | NULL                                                                        | Description of the product or service.                                       |
| `payment_batch_id`    | INT              | NULL, FOREIGN KEY (`payment_batch_id`) REFERENCES `payment_batches`(`id`)   | Links the order to a payment batch, if applicable.                           |
| `alipay_trade_no`     | VARCHAR(255)     | NULL, UNIQUE                                                                | Alipay's transaction ID for this specific order (if paid individually).    |
| `error_message`       | TEXT             | NULL                                                                        | Stores error message if payment for this order failed.                       |
| `created_at`          | TIMESTAMP        | NOT NULL, DEFAULT CURRENT_TIMESTAMP                                         | Timestamp of order creation.                                                 |
| `updated_at`          | TIMESTAMP        | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP             | Timestamp of last order update.                                              |

**Indexes:**
*   `idx_orders_order_uid` ON `order_uid`
*   `idx_orders_user_id` ON `user_id`
*   `idx_orders_status` ON `status`
*   `idx_orders_payment_batch_id` ON `payment_batch_id`
*   `idx_orders_alipay_trade_no` ON `alipay_trade_no`

---

### Table: `payment_transactions`

Stores detailed logs of each payment attempt. Recommended for traceability and debugging.

| Column Name         | Data Type        | Constraints                                                                    | Description                                                               |
|---------------------|------------------|--------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `id`                | INT AUTO_INCREMENT | PRIMARY KEY                                                                    | Unique identifier for the transaction log.                                |
| `order_id`          | INT              | NOT NULL, FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`)                   | The order associated with this transaction attempt.                       |
| `payment_batch_id`  | INT              | NULL, FOREIGN KEY (`payment_batch_id`) REFERENCES `payment_batches`(`id`)      | The batch this transaction belongs to, if applicable.                     |
| `transaction_uid`   | UUID             | NOT NULL, UNIQUE                                                               | Unique identifier for this transaction log entry.                         |
| `alipay_trade_no`   | VARCHAR(255)     | NULL                                                                           | Alipay's transaction ID for this specific attempt.                        |
| `amount`            | DECIMAL(10, 2)   | NOT NULL                                                                       | Amount of this transaction attempt.                                       |
| `currency`          | VARCHAR(3)       | NOT NULL                                                                       | Currency code for this attempt.                                           |
| `status`            | VARCHAR(50)      | NOT NULL                                                                       | Status of this attempt (e.g., 'INITIATED', 'SUCCESS', 'FAILED').          |
| `request_payload`   | JSON             | NULL                                                                           | Data sent to Alipay for this attempt.                                     |
| `response_payload`  | JSON             | NULL                                                                           | Data received from Alipay for this attempt (excluding sensitive info).    |
| `error_code`        | VARCHAR(255)     | NULL                                                                           | Error code received from Alipay, if any.                                  |
| `error_message`     | TEXT             | NULL                                                                           | Error message received, if any.                                           |
| `created_at`        | TIMESTAMP        | NOT NULL, DEFAULT CURRENT_TIMESTAMP                                            | Timestamp of transaction log creation.                                    |
| `updated_at`        | TIMESTAMP        | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP                | Timestamp of last transaction log update.                                 |

**Indexes:**
*   `idx_payment_transactions_transaction_uid` ON `transaction_uid`
*   `idx_payment_transactions_order_id` ON `order_id`
*   `idx_payment_transactions_payment_batch_id` ON `payment_batch_id`
*   `idx_payment_transactions_alipay_trade_no` ON `alipay_trade_no`
*   `idx_payment_transactions_status` ON `status`

---
**Notes on Data Types and Constraints:**

*   **UUID:** Using `UUID` (or `VARCHAR(36)` if native UUID is not available) for `*_uid` fields provides globally unique identifiers, useful for external systems or distributed environments.
*   **ENUM vs VARCHAR for Status:** While `ENUM` can be more storage-efficient, `VARCHAR` offers more flexibility for adding new states without schema alterations. The choice depends on the specific RDBMS and operational preferences. I've used `VARCHAR(50)` here.
*   **Decimal Precision:** `DECIMAL(10, 2)` for order amounts and `DECIMAL(15, 2)` for batch total amounts are examples; adjust precision as needed based on expected values.
*   **Timestamps:** `ON UPDATE CURRENT_TIMESTAMP` is a MySQL-specific feature. For other databases, this logic might need to be handled at the application level or via triggers.
*   **JSON Data Type:** Support for JSON types varies by RDBMS. If not available, `TEXT` can be used, but querying JSON content will be less efficient.
*   **Foreign Key Actions:** `ON DELETE` and `ON UPDATE` actions for foreign keys (e.g., `CASCADE`, `SET NULL`, `RESTRICT`) should be considered based on business logic (not explicitly defined here for brevity, default is usually `RESTRICT`).
*   **`alipay_trade_no` in `orders` vs `payment_transactions`:**
    *   `orders.alipay_trade_no`: Stores the final Alipay transaction ID if an order is processed individually or if a batch payment still returns per-order transaction IDs that are relevant at the order level.
    *   `payment_transactions.alipay_trade_no`: Stores the Alipay transaction ID for each specific attempt, which is crucial if there are retries or if multiple interactions occur for a single order.
    *   `payment_batches.alipay_batch_no`: Stores Alipay's identifier for the entire batch if Alipay processes it as a single transaction.

This schema provides a comprehensive structure for the payment system, covering users, orders, batch payments, and detailed transaction logging.
