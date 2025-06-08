class TShirtShop {
    constructor() {
        this.products = [];
        this.cart = JSON.parse(localStorage.getItem('cart')) || [];
        this.currentFilter = 'all';
        this.init();
    }

    init() {
        this.loadProducts();
        this.setupEventListeners();
        this.updateCartUI();
        this.hideLoadingOverlay();
        this.setupIntersectionObserver();
    }

    loadProducts() {
        // Sample products data
        this.products = [
            {
                id: 1,
                name: 'تيشيرت كلاسيكي أزرق',
                price: 75,
                image: 'images/tshirt1.jpg',
                category: 'men',
                description: 'تيشيرت رجالي مريح من القطن الخالص'
            },
            {
                id: 2,
                name: 'تيشيرت نسائي وردي',
                price: 65,
                image: 'images/tshirt2.jpg',
                category: 'women',
                description: 'تيشيرت نسائي أنيق بقصة مريحة'
            },
            {
                id: 3,
                name: 'تيشيرت أطفال ملون',
                price: 45,
                image: 'images/tshirt3.jpg',
                category: 'kids',
                description: 'تيشيرت للأطفال بألوان زاهية'
            },
            {
                id: 4,
                name: 'تيشيرت رياضي أسود',
                price: 80,
                image: 'images/tshirt4.jpg',
                category: 'men',
                description: 'تيشيرت رياضي مناسب للتمارين'
            },
            {
                id: 5,
                name: 'تيشيرت نسائي أبيض',
                price: 70,
                image: 'images/tshirt5.jpg',
                category: 'women',
                description: 'تيشيرت نسائي كلاسيكي أبيض'
            },
            {
                id: 6,
                name: 'تيشيرت أطفال كرتوني',
                price: 50,
                image: 'images/tshirt6.jpg',
                category: 'kids',
                description: 'تيشيرت للأطفال برسوم كرتونية'
            }
        ];

        this.renderProducts();
    }

    renderProducts() {
        const productsGrid = document.getElementById('productsGrid');
        const filteredProducts = this.currentFilter === 'all' 
            ? this.products 
            : this.products.filter(product => product.category === this.currentFilter);

        productsGrid.innerHTML = filteredProducts.map(product => `
            <div class="product-card fadeInUp" data-category="${product.category}">
                <div class="product-image">
                    <img src="${product.image}" alt="${product.name}" onerror="this.src='images/placeholder.jpg'">
                    <div class="product-overlay">
                        <button class="add-to-cart" onclick="shop.addToCart(${product.id})">
                            <i class="fas fa-cart-plus"></i> أضف للسلة
                        </button>
                    </div>
                </div>
                <div class="product-info">
                    <h3>${product.name}</h3>
                    <p class="product-description">${product.description}</p>
                    <div class="product-price">${product.price} ريال</div>
                </div>
            </div>
        `).join('');

        // Re-trigger animations
        setTimeout(() => {
            document.querySelectorAll('.product-card').forEach((el, index) => {
                el.style.animationDelay = `${index * 0.1}s`;
            });
        }, 100);
    }

    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.renderProducts();
            });
        });

        // Mobile menu toggle
        const menuToggle = document.querySelector('.menu-toggle');
        const navMenu = document.querySelector('.nav-menu');
        
        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Cart modal
        const cartIcon = document.querySelector('.cart-icon');
        const cartModal = document.getElementById('cartModal');
        const closeCart = document.querySelector('.close-cart');

        if (cartIcon) {
            cartIcon.addEventListener('click', (e) => {
                e.preventDefault();
                this.showCart();
            });
        }

        if (closeCart) {
            closeCart.addEventListener('click', () => {
                cartModal.style.display = 'none';
            });
        }

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === cartModal) {
                cartModal.style.display = 'none';
            }
        });

        // Contact form
        const contactForm = document.querySelector('.contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleContactForm(e);
            });
        }

        // CTA button
        const ctaBtn = document.querySelector('.cta-btn');
        if (ctaBtn) {
            ctaBtn.addEventListener('click', () => {
                document.getElementById('products').scrollIntoView({
                    behavior: 'smooth'
                });
            });
        }
    }

    addToCart(productId) {
        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const existingItem = this.cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                ...product,
                quantity: 1
            });
        }

        this.updateCartUI();
        this.saveCart();
        this.showNotification('تم إضافة المنتج للسلة بنجاح!', 'success');
    }

    removeFromCart(productId) {
        this.cart = this.cart.filter(item => item.id !== productId);
        this.updateCartUI();
        this.saveCart();
        this.renderCartItems();
    }

    updateQuantity(productId, newQuantity) {
        const item = this.cart.find(item => item.id === productId);
        if (item) {
            if (newQuantity <= 0) {
                this.removeFromCart(productId);
            } else {
                item.quantity = newQuantity;
                this.updateCartUI();
                this.saveCart();
                this.renderCartItems();
            }
        }
    }

    updateCartUI() {
        const cartCount = document.querySelector('.cart-count');
        const totalItems = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        
        if (cartCount) {
            cartCount.textContent = totalItems;
            cartCount.style.display = totalItems > 0 ? 'flex' : 'none';
        }
    }

    showCart() {
        const cartModal = document.getElementById('cartModal');
        this.renderCartItems();
        cartModal.style.display = 'block';
    }

    renderCartItems() {
        const cartItems = document.getElementById('cartItems');
        const cartTotal = document.getElementById('cartTotal');
        
        if (this.cart.length === 0) {
            cartItems.innerHTML = '<p style="text-align: center; color: #666;">السلة فارغة</p>';
            cartTotal.textContent = '0';
            return;
        }

        cartItems.innerHTML = this.cart.map(item => `
            <div class="cart-item">
                <div class="item-info">
                    <h4>${item.name}</h4>
                    <p>${item.price} ريال</p>
                </div>
                <div class="item-controls">
                    <button onclick="shop.updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="shop.updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    <button onclick="shop.removeFromCart(${item.id})" style="color: red; margin-right: 10px;">×</button>
                </div>
            </div>
        `).join('');

        const total = this.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        cartTotal.textContent = total;
    }

    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.cart));
    }

    handleContactForm(e) {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        // Simulate form submission
        this.showNotification('تم إرسال رسالتك بنجاح! سنتواصل معك قريباً.', 'success');
        e.target.reset();
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#007bff'};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 10001;
            animation: slideInRight 0.5s ease;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideInRight 0.5s ease reverse';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }

    hideLoadingOverlay() {
        setTimeout(() => {
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.classList.add('hidden');
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                }, 500);
            }
        }, 1500);
    }

    setupIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe elements that should animate on scroll
        document.querySelectorAll('.feature, .product-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(50px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });
    }
}

// Initialize the shop when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.shop = new TShirtShop();
});

// Service Worker for better performance (if needed)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
