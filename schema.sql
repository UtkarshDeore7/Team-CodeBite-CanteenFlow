CREATE DATABASE IF NOT EXISTS canteenflow
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE canteenflow;

CREATE TABLE users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100)  NOT NULL,
    email          VARCHAR(150)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255)  NOT NULL,
    role           ENUM('STUDENT', 'STAFF', 'ADMIN') NOT NULL DEFAULT 'STUDENT',
    phone          VARCHAR(15)   NULL,
    is_active      BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

CREATE TABLE categories (
    category_id    INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(50)   NOT NULL UNIQUE,
    display_order  INT           NOT NULL DEFAULT 0
) ENGINE = InnoDB;

CREATE TABLE menu_items (
    item_id        INT AUTO_INCREMENT PRIMARY KEY,
    category_id    INT           NOT NULL,
    name           VARCHAR(100)  NOT NULL,
    description    VARCHAR(255)  NULL,
    price          DECIMAL(7,2)  NOT NULL,
    image_url      VARCHAR(255)  NULL,
    prep_minutes   INT           NOT NULL DEFAULT 5,
    is_available   BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_item_category FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE RESTRICT,
    CONSTRAINT chk_price_positive CHECK (price > 0),
    INDEX idx_item_available (is_available, category_id)
) ENGINE = InnoDB;

CREATE TABLE orders (
    order_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT           NOT NULL,
    order_date     DATE          NOT NULL,
    token_number   INT           NOT NULL,
    status         ENUM('PLACED', 'ACCEPTED', 'PREPARING', 'READY', 'COLLECTED', 'CANCELLED') NOT NULL DEFAULT 'PLACED',
    total_amount   DECIMAL(9,2)  NOT NULL DEFAULT 0.00,
    pickup_slot    TIME          NULL,
    placed_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ready_at       TIMESTAMP     NULL,
    collected_at   TIMESTAMP     NULL,
    notes          VARCHAR(255)  NULL,
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT uq_token_per_day UNIQUE (order_date, token_number),
    INDEX idx_queue (order_date, status, placed_at),
    INDEX idx_user_orders (user_id, placed_at)
) ENGINE = InnoDB;

CREATE TABLE order_items (
    order_item_id  INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT           NOT NULL,
    item_id        INT           NOT NULL,
    quantity       INT           NOT NULL,
    unit_price     DECIMAL(7,2)  NOT NULL,
    line_total     DECIMAL(9,2)  AS (quantity * unit_price) STORED,
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT fk_oi_item FOREIGN KEY (item_id) REFERENCES menu_items (item_id) ON DELETE RESTRICT,
    CONSTRAINT chk_qty_positive CHECK (quantity > 0),
    INDEX idx_oi_order (order_id)
) ENGINE = InnoDB;

CREATE TABLE order_status_history (
    history_id     INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT           NOT NULL,
    status         ENUM('PLACED', 'ACCEPTED', 'PREPARING', 'READY', 'COLLECTED', 'CANCELLED') NOT NULL,
    changed_by     INT           NULL,
    changed_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_order FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
    CONSTRAINT fk_hist_user FOREIGN KEY (changed_by) REFERENCES users (user_id) ON DELETE SET NULL,
    INDEX idx_hist_order (order_id, changed_at)
) ENGINE = InnoDB;

CREATE OR REPLACE VIEW v_live_queue AS
SELECT  o.order_id,
        o.token_number,
        u.full_name,
        o.status,
        o.total_amount,
        o.placed_at,
        TIMESTAMPDIFF(MINUTE, o.placed_at, NOW()) AS minutes_waiting
FROM    orders o
JOIN    users  u ON u.user_id = o.user_id
WHERE   o.order_date = CURDATE()
  AND   o.status IN ('PLACED', 'ACCEPTED', 'PREPARING', 'READY')
ORDER BY o.placed_at;

INSERT INTO categories (name, display_order) VALUES
    ('Snacks',    1),
    ('Meals',     2),
    ('Beverages', 3),
    ('Desserts',  4);

INSERT INTO menu_items (category_id, name, description, price, prep_minutes) VALUES
    (1, 'Veg Sandwich',   'Grilled sandwich with vegetables and cheese',  45.00,  6),
    (1, 'Samosa',         'Two pieces served with chutney',               25.00,  3),
    (1, 'French Fries',   'Salted, medium portion',                       60.00,  7),
    (2, 'Veg Thali',      'Rice, dal, two chapatis and a sabzi',         110.00, 12),
    (2, 'Pav Bhaji',      'Butter pav with spiced bhaji',                 80.00, 10),
    (2, 'Paneer Roll',    'Paneer tikka wrapped in a roti',               90.00,  9),
    (3, 'Masala Chai',    'Served hot',                                   15.00,  4),
    (3, 'Cold Coffee',    'Blended with ice cream',                       50.00,  5),
    (3, 'Fresh Lime Soda','Sweet or salted',                              35.00,  3),
    (4, 'Gulab Jamun',    'Two pieces',                                   30.00,  2);
