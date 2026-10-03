function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('canteen_theme', isDark ? 'dark' : 'light');
    const btn = document.getElementById('theme-btn');
    if (btn) btn.innerText = isDark ? '☀️ Light' : '🌙 Dark';
}

function getTimeGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
}

document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('canteen_theme') === 'dark') {
        document.body.classList.add('dark-mode');
        const btn = document.getElementById('theme-btn');
        if (btn) btn.innerText = '☀️ Light';
    }

    const greetingElem = document.getElementById('time-greeting');
    if (greetingElem) {
        greetingElem.innerText = getTimeGreeting();
    }

    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.food-card').forEach(card => {
                const title = card.querySelector('.food-title').innerText.toLowerCase();
                const desc = card.querySelector('.food-desc').innerText.toLowerCase();
                card.style.display = (title.includes(query) || desc.includes(query)) ? 'flex' : 'none';
            });
        });
    }

    renderAllCardButtons();
    initRippleEffects();
});

function initRippleEffects() {
    document.querySelectorAll('.btn-add-overlay, .pill-btn, .banner-card').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
}

function openImageModal(imgUrl, title, price, desc, prepTime, itemId) {
    document.getElementById('modal-img').src = imgUrl;
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-price').innerText = '₹' + parseFloat(price).toFixed(2);
    document.getElementById('modal-desc').innerText = desc;
    document.getElementById('modal-prep').innerText = '⏱ ' + prepTime + ' mins';
    
    const addBtn = document.getElementById('modal-add-btn');
    addBtn.onclick = function() {
        updateCartItem(itemId, 'add', title);
        closeImageModal();
    };

    document.getElementById('image-modal').style.display = 'flex';
}

function closeImageModal() {
    document.getElementById('image-modal').style.display = 'none';
}

function renderAllCardButtons() {
    document.querySelectorAll('.food-card').forEach(card => {
        const itemId = card.dataset.itemId;
        const itemName = card.dataset.itemName;
        const container = document.getElementById(`btn-container-${itemId}`);
        if (!container) return;

        const qty = (window.currentCart && window.currentCart[itemId]) ? window.currentCart[itemId] : 0;

        if (qty > 0) {
            container.innerHTML = `
                <div class="qty-counter-pill">
                    <button class="qty-btn" onclick="updateCartItem('${itemId}', 'remove', '${itemName}')">−</button>
                    <span>${qty}</span>
                    <button class="qty-btn" onclick="updateCartItem('${itemId}', 'add', '${itemName}')">+</button>
                </div>
            `;
        } else {
            container.innerHTML = `
                <button type="button" class="btn-add-overlay" onclick="updateCartItem('${itemId}', 'add', '${itemName}')">ADD +</button>
            `;
        }
    });
}

function updateCartItem(itemId, action, itemName) {
    fetch('/cart/update_ajax', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, action: action })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.currentCart = data.cart;
            renderAllCardButtons();
            
            // Spawn Animated Particle Badge
            const imgContainer = document.querySelector(`.food-card[data-item-id="${itemId}"] .img-container`);
            if (imgContainer) {
                const particle = document.createElement('div');
                particle.className = 'floating-particle';
                particle.innerText = action === 'add' ? '+1 🍱' : '-1 🗑️';
                imgContainer.appendChild(particle);
                setTimeout(() => particle.remove(), 750);
            }

            if (action === 'add') {
                showToast(`🍱 Added ${itemName} to cart! (${data.item_qty} in cart)`);
            } else if (action === 'remove' && data.item_qty === 0) {
                showToast(`🗑️ Removed ${itemName} from cart.`);
            }

            const cartBar = document.getElementById('floating-cart-bar');
            if (cartBar) {
                if (data.total_items > 0) {
                    cartBar.style.display = 'flex';
                    document.getElementById('cart-summary-title').innerText = `🛒 ${data.total_items} Items Selected`;
                    document.getElementById('cart-summary-total').innerText = data.total_price.toFixed(2);
                    cartBar.classList.remove('bump');
                    void cartBar.offsetWidth;
                    cartBar.classList.add('bump');
                } else {
                    cartBar.style.display = 'none';
                }
            }
        }
    })
    .catch(err => console.log('Cart update error:', err));
}

function showToast(text) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast-message';
    toast.innerHTML = `<span>✨</span> <span>${text}</span>`;
    
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

function filterCategory(catName, btn) {
    document.querySelectorAll('.pill-btn').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.category-section').forEach(section => {
        section.style.display = (catName === 'ALL' || section.dataset.category === catName) ? 'block' : 'none';
        
        // Trigger smooth staggered entrance on category switch
        if (catName === 'ALL' || section.dataset.category === catName) {
            section.querySelectorAll('.food-card').forEach((card, idx) => {
                card.style.animation = 'none';
                void card.offsetWidth; // force reflow
                card.style.animation = `fadeInUp 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) ${idx * 0.05}s both`;
            });
        }
    });
}

function printThermalReceipt() {
    window.print();
}

function startPollingOrder(orderId) {
    let lastStatus = null;
    setInterval(() => {
        fetch(`/order/${orderId}/status.json`)
            .then(res => res.json())
            .then(data => {
                if (data.status && lastStatus && lastStatus !== data.status) {
                    window.location.reload();
                }
                lastStatus = data.status;
            })
            .catch(err => console.log('Polling error:', err));
    }, 4000);
}
