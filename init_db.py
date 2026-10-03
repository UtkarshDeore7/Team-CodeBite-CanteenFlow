import pymysql
from werkzeug.security import generate_password_hash

conn = pymysql.connect(host='127.0.0.1', user='root', password='', autocommit=True)
cur = conn.cursor()

cur.execute("CREATE DATABASE IF NOT EXISTS canteenflow;")
cur.execute("USE canteenflow;")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('STUDENT', 'STAFF') DEFAULT 'STUDENT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    display_order INT DEFAULT 0
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    prep_minutes INT DEFAULT 5,
    image_url TEXT,
    is_veg BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    order_date DATE NOT NULL,
    token_number INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('PLACED', 'ACCEPTED', 'PREPARING', 'READY', 'COLLECTED', 'CANCELLED') DEFAULT 'PLACED',
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY (order_date, token_number)
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    item_id INT,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id) ON DELETE CASCADE
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT UNIQUE,
    user_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

# Create Live Queue View
cur.execute("""
CREATE OR REPLACE VIEW v_live_queue AS
SELECT 
    o.order_id,
    o.user_id,
    o.order_date,
    o.token_number,
    o.status,
    o.total_amount,
    o.placed_at,
    u.full_name
FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.order_date = CURDATE() 
  AND o.status IN ('PLACED', 'ACCEPTED', 'PREPARING', 'READY');
""")

# Insert Categories
cur.execute("DELETE FROM categories;")
cur.execute("INSERT INTO categories (category_id, name, display_order) VALUES (1, 'Snacks', 1), (2, 'Main Course', 2), (3, 'Beverages', 3), (4, 'Desserts', 4);")

# Insert Menu Items
cur.execute("DELETE FROM menu_items;")
items = [
    (1, 'Veg Sandwich', 'Grilled Mumbai vegetable sandwich with cheese & green chutney.', 60.00, 5, 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=600&q=80', True),
    (1, 'Samosa (2 pcs)', 'Golden crispy Punjabi samosas served with sweet & mint chutney.', 30.00, 3, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80', True),
    (1, 'French Fries', 'Crispy golden salted Peri-Peri french fries.', 70.00, 5, 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=600&q=80', True),
    (1, 'Chole Bhature', 'Fluffy fried bhaturas served with spicy Punjabi chole & pickled onions.', 90.00, 10, 'https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&q=80', True),
    (1, 'Masala Dosa', 'Crispy rice crepe stuffed with potato masala, coconut chutney & sambar.', 80.00, 8, 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=600&q=80', True),
    (1, 'Special Misal Pav', 'Spicy Kolhapuri sprout curry topped with farsan, onions & buttered pav.', 65.00, 5, 'https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=600&q=80', True),
    (2, 'Veg Thali', 'Complete meal with 2 sabzi, dal fry, rice, 3 chapati & sweet.', 120.00, 10, 'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=600&q=80', True),
    (2, 'Pav Bhaji', 'Special butter-loaded Mumbai bhaji with 2 soft pavs.', 90.00, 8, 'https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=600&q=80', True),
    (2, 'Paneer Tikka Roll', 'Spiced cottage cheese Kathi roll with mint Mayo.', 95.00, 7, 'https://images.unsplash.com/photo-1606471191009-63994c53433b?w=600&q=80', True),
    (2, 'Veg Dum Biryani Bowl', 'Aromatic Basmati rice dum-cooked with fresh veggies, paneer & spices.', 130.00, 10, 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80', True),
    (2, 'Paneer Butter Masala Bowl', 'Rich creamy tomato gravy with soft paneer cubes served over Jeera rice.', 140.00, 10, 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&q=80', True),
    (2, 'Veg Cheese Frankie Roll', 'Mumbai-style spiced potato & cheese wrap with tangy chutney.', 80.00, 6, 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&q=80', True),
    (2, 'Dal Makhani Rice Bowl', 'Slow-cooked black dal makhani with butter served with steamed rice.', 110.00, 8, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&q=80', True),
    (3, 'Masala Chai', 'Steaming hot Indian kulhad masala tea.', 20.00, 3, 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=600&q=80', True),
    (3, 'Cold Coffee', 'Chilled thick espresso coffee.', 50.00, 4, 'https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&q=80', True),
    (3, 'Iced Cold Coffee w/ Ice Cream', 'Espresso blended with milk & topped with vanilla ice cream.', 70.00, 5, 'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&q=80', True),
    (3, 'Fresh Lime Soda', 'Sparkling sweet & salted mint lime soda.', 40.00, 3, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&q=80', True),
    (3, 'Mango Lassi', 'Thick creamy yogurt smoothie with Alphonso mango pulp.', 60.00, 4, 'https://images.unsplash.com/photo-1553787499-6f9133860278?w=600&q=80', True),
    (4, 'Gulab Jamun (2 pcs)', 'Warm brown gulab jamuns in sweet cardamom sugar syrup.', 40.00, 2, 'https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&q=80', True),
    (4, 'Sizzling Brownie w/ Ice Cream', 'Hot fudgy chocolate brownie with vanilla ice cream.', 110.00, 6, 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&q=80', True)
]
cur.executemany("INSERT INTO menu_items (category_id, name, description, price, prep_minutes, image_url, is_veg) VALUES (%s, %s, %s, %s, %s, %s, %s);", items)

pw_hash = generate_password_hash('password123')
cur.execute("DELETE FROM users;")
cur.execute("INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)", ('Demo Student', 'student@mitmumbai.edu', pw_hash, 'STUDENT'))
cur.execute("INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)", ('Demo Staff', 'staff@college.edu', pw_hash, 'STAFF'))

print("✅ init_db.py updated with v_live_queue view!")
