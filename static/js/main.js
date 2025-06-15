/**
 * متجر البلايز المميزة - ملف سكريبت رئيسي
 * يحتوي على كافة التفاعلات والوظائف الخاصة بالموقع
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // تفعيل التلميحات
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // تنسيق أرقام الهاتف
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // إزالة أي أحرف غير رقمية
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // التحقق من الطول
            if (this.value.length > 11) {
                this.value = this.value.slice(0, 11);
            }
        });
    });
    
    // تأكيد كلمة المرور في صفحة التسجيل
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('password-confirm');
    
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (this.value !== passwordInput.value) {
                this.setCustomValidity('كلمات المرور غير متطابقة');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    // نموذج الاتصال - شكراً بعد الإرسال
    const contactForm = document.querySelector('form.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> جاري الإرسال...';
                submitButton.disabled = true;
            }
            // لا نمنع السلوك الافتراضي هنا لأننا نريد أن يتم إرسال النموذج بالفعل
        });
    }
    
    // نموذج إضافة منتج للسلة
    const addToCartForm = document.getElementById('addToCartForm');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            // نسمح بالسلوك الافتراضي للنموذج للتأكد من إرسال رمز CSRF
            
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> جاري الإضافة...';
                submitButton.disabled = true;
                
                // تحقق من وجود المعلومات المطلوبة
                const sizeInput = this.querySelector('select[name="size"]');
                const colorInput = this.querySelector('select[name="color"]');
                
                if (sizeInput && sizeInput.required && !sizeInput.value) {
                    e.preventDefault();
                    showNotification('الرجاء اختيار المقاس', 'error');
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                    return false;
                }
                
                if (colorInput && colorInput.required && !colorInput.value) {
                    e.preventDefault();
                    showNotification('الرجاء اختيار اللون', 'error');
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                    return false;
                }
                
                // نعيد تفعيل الزر بعد الانتقال للصفحة التالية
                setTimeout(() => {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 1000);
            }
        });
    }
    
    // تنسيق حقول النموذج
    const formInputs = document.querySelectorAll('.form-control, .form-select');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.closest('.form-group')?.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.closest('.form-group')?.classList.remove('focused');
            }
        });
    });
    
    // تحديث كمية المنتج في سلة التسوق
    const quantityInputs = document.querySelectorAll('.cart-quantity');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min || 1);
            const max = parseInt(this.max || 10);
            let value = parseInt(this.value);
            
            if (isNaN(value) || value < min) {
                value = min;
            } else if (value > max) {
                value = max;
            }
            
            this.value = value;
            
            // طلب AJAX لتحديث السلة
            const itemId = this.dataset.itemId;
            if (itemId && value) {
                updateCartQuantity(itemId, value);
            }
        });
    });
    
    // وظيفة تحديث كمية المنتج في السلة
    function updateCartQuantity(itemId, quantity) {
        // التأكد من وجود رمز CSRF
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }
        
        // إنشاء طلب
        const formData = new FormData();
        formData.append('item_id', itemId);
        formData.append('quantity', quantity);
        formData.append('csrf_token', csrfToken);
        
        // إرسال الطلب
        fetch('/cart/update_quantity', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // تحديث إجمالي المنتج
                const subtotalElement = document.querySelector(`#subtotal-${itemId}`);
                if (subtotalElement) {
                    subtotalElement.textContent = data.subtotal;
                }
                
                // تحديث إجمالي السلة
                const cartTotalElement = document.querySelector('#cart-total');
                if (cartTotalElement) {
                    cartTotalElement.textContent = data.total;
                }
            } else {
                showNotification(data.message || 'حدث خطأ أثناء تحديث السلة', 'error');
            }
        })
        .catch(error => {
            console.error('Error updating cart:', error);
            showNotification('حدث خطأ أثناء تحديث السلة', 'error');
        });
    }
    
    // صور المنتج المصغرة
    const productThumbnails = document.querySelectorAll('.product-thumbnail');
    productThumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            const mainImage = document.getElementById('product-main-image');
            if (mainImage) {
                mainImage.src = this.getAttribute('data-image');
                
                productThumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // طي القائمة الجانبية في الشاشات الصغيرة
    const toggler = document.querySelector('.sidebar-toggler');
    const sidebar = document.querySelector('.admin-sidebar .list-group');
    
    if (toggler && sidebar) {
        toggler.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // رجوع للأعلى
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        });
        
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // دالة لعرض الإشعارات
    window.showNotification = function(message, type) {
        const notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" aria-label="إغلاق">&times;</button>
        `;
        
        document.getElementById('notification-container').appendChild(notification);
        
        // إخفاء الإشعار بعد 5 ثوان
        setTimeout(() => {
            notification.classList.add('hide');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
        
        // إغلاق الإشعار عند الضغط على زر الإغلاق
        notification.querySelector('.notification-close').addEventListener('click', function() {
            notification.classList.add('hide');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    };
    
    // التعامل مع البحث
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    
    if (searchForm && searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (query.length < 2) {
                if (suggestionsContainer) {
                    suggestionsContainer.innerHTML = '';
                    suggestionsContainer.style.display = 'none';
                }
                return;
            }
            
            // طلب اقتراحات البحث
            fetch(`/api/search/suggestions?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(suggestions => {
                    if (suggestionsContainer) {
                        if (suggestions.length > 0) {
                            let html = '';
                            suggestions.forEach(suggestion => {
                                html += `<a href="${suggestion.url}" class="suggestion-item">${suggestion.name}</a>`;
                            });
                            suggestionsContainer.innerHTML = html;
                            suggestionsContainer.style.display = 'block';
                        } else {
                            suggestionsContainer.innerHTML = '';
                            suggestionsContainer.style.display = 'none';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching search suggestions:', error);
                });
        });
        
        // إخفاء الاقتراحات عند النقر خارجها
        document.addEventListener('click', function(e) {
            if (suggestionsContainer && !searchForm.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
        
        // التحقق من صحة البحث قبل الإرسال
        searchForm.addEventListener('submit', function(e) {
            const query = searchInput.value.trim();
            if (query.length < 2) {
                e.preventDefault();
                showNotification('الرجاء إدخال كلمة بحث لا تقل عن حرفين', 'error');
            }
        });
    }
});
