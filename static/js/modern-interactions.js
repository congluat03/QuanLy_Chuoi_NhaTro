// Modern Interactions JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactions
    initScrollAnimations();
    initCardHoverEffects();
    initFormEnhancements();
    initNavbarInteractions();
    initLoadingStates();
    initNotifications();
    
    // Scroll Animations
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-visible');
                }
            });
        }, observerOptions);
        
        // Observe elements with animation classes
        document.querySelectorAll('.fade-in, .slide-up, .scale-in').forEach(el => {
            observer.observe(el);
        });
    }
    
    // Card Hover Effects
    function initCardHoverEffects() {
        document.querySelectorAll('.modern-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.02)';
                this.style.transition = 'all 0.3s ease';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        });
        
        // Feature highlight cards
        document.querySelectorAll('.feature-highlight').forEach(card => {
            card.addEventListener('mouseenter', function() {
                const icon = this.querySelector('.w-16');
                if (icon) {
                    icon.style.transform = 'scale(1.1) rotate(5deg)';
                }
            });
            
            card.addEventListener('mouseleave', function() {
                const icon = this.querySelector('.w-16');
                if (icon) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                }
            });
        });
    }
    
    // Form Enhancements
    function initFormEnhancements() {
        // Floating labels
        document.querySelectorAll('.form-input-modern').forEach(input => {
            const label = input.parentElement.parentElement.querySelector('.form-label-modern');
            
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('ring-2', 'ring-blue-500/20');
                if (label) {
                    label.style.color = 'var(--primary-600)';
                    label.style.transform = 'scale(0.95)';
                }
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('ring-2', 'ring-blue-500/20');
                if (label) {
                    label.style.color = 'var(--gray-700)';
                    label.style.transform = 'scale(1)';
                }
            });
            
            // Input validation visual feedback
            input.addEventListener('input', function() {
                if (this.value.length > 0) {
                    this.classList.add('has-value');
                } else {
                    this.classList.remove('has-value');
                }
            });
        });
        
        // Button loading states
        document.querySelectorAll('.btn-modern').forEach(btn => {
            btn.addEventListener('click', function(e) {
                if (this.type === 'submit') {
                    // Add loading state
                    const originalText = this.textContent;
                    const spinner = createSpinner();
                    
                    this.innerHTML = '';
                    this.appendChild(spinner);
                    this.appendChild(document.createTextNode(' Đang xử lý...'));
                    this.disabled = true;
                    
                    // Simulate loading (remove in production)
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.disabled = false;
                    }, 2000);
                }
            });
        });
    }
    
    // Navbar Interactions
    function initNavbarInteractions() {
        const navbar = document.querySelector('.nav-modern');
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 100) {
                navbar.classList.add('scrolled');
                navbar.style.backgroundColor = 'rgba(30, 64, 175, 0.95)';
                navbar.style.backdropFilter = 'blur(20px)';
            } else {
                navbar.classList.remove('scrolled');
                navbar.style.backgroundColor = '';
                navbar.style.backdropFilter = '';
            }
            
            // Hide/show navbar on scroll
            if (currentScrollY > lastScrollY && currentScrollY > 200) {
                navbar.style.transform = 'translateY(-100%)';
            } else {
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScrollY = currentScrollY;
        });
        
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
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
    }
    
    // Loading States
    function initLoadingStates() {
        // Page loading animation
        window.addEventListener('load', function() {
            document.body.classList.add('loaded');
            
            // Stagger animations
            const animatedElements = document.querySelectorAll('.fade-in, .slide-up, .scale-in');
            animatedElements.forEach((el, index) => {
                setTimeout(() => {
                    el.style.animationDelay = `${index * 0.1}s`;
                    el.classList.add('animate-visible');
                }, index * 100);
            });
        });
        
        // Form submission loading
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                }
            });
        });
    }
    
    // Notifications
    function initNotifications() {
        // Auto-hide alerts after 5 seconds
        document.querySelectorAll('.alert-modern').forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }, 5000);
            
            // Add close button
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.className = 'ml-auto text-lg font-bold opacity-70 hover:opacity-100';
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => alert.remove(), 300);
            });
            alert.appendChild(closeBtn);
        });
    }
    
    // Utility Functions
    function createSpinner() {
        const spinner = document.createElement('div');
        spinner.className = 'spinner inline-block mr-2';
        return spinner;
    }
    
    // Parallax effect for hero sections
    function initParallaxEffect() {
        const heroSections = document.querySelectorAll('.hero-modern');
        
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            heroSections.forEach(hero => {
                const rate = scrolled * -0.5;
                hero.style.transform = `translateY(${rate}px)`;
            });
        });
    }
    
    // Initialize parallax if hero sections exist
    if (document.querySelectorAll('.hero-modern').length > 0) {
        initParallaxEffect();
    }
    
    // Image lazy loading
    function initLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
    
    initLazyLoading();
    
    // Dark mode toggle (optional)
    function initDarkMode() {
        const darkModeToggle = document.querySelector('#dark-mode-toggle');
        if (darkModeToggle) {
            darkModeToggle.addEventListener('click', () => {
                document.documentElement.classList.toggle('dark');
                localStorage.setItem('darkMode', 
                    document.documentElement.classList.contains('dark')
                );
            });
            
            // Restore dark mode preference
            if (localStorage.getItem('darkMode') === 'true') {
                document.documentElement.classList.add('dark');
            }
        }
    }
    
    initDarkMode();
});

// CSS Animations via JavaScript
const styles = `
@keyframes animate-visible {
    from {
        opacity: 0;
        transform: translateY(30px) scale(0.95);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

.animate-visible {
    animation: animate-visible 0.6s ease-out forwards;
}

.btn-modern.loading {
    pointer-events: none;
    opacity: 0.7;
}

.form-input-modern.has-value {
    border-color: var(--primary-500);
}

.loaded .fade-in,
.loaded .slide-up,
.loaded .scale-in {
    opacity: 1;
    transform: translateY(0) scale(1);
}

/* Smooth transitions for all interactive elements */
.nav-modern {
    transition: all 0.3s ease;
}

.modern-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-modern {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-input-modern {
    transition: all 0.2s ease;
}

/* Glass morphism effect */
.glass-effect {
    backdrop-filter: blur(16px) saturate(180%);
    background-color: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.125);
}

/* Loading spinner animation */
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.spinner {
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

/* Hover effects */
.nav-item-modern {
    position: relative;
    overflow: hidden;
}

.nav-item-modern::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.nav-item-modern:hover::before {
    left: 100%;
}

/* Mobile responsive improvements */
@media (max-width: 768px) {
    .modern-card {
        margin: 0.5rem;
        border-radius: 1rem;
    }
    
    .hero-modern {
        padding: 3rem 0;
    }
    
    .btn-modern-lg {
        width: 100%;
        justify-content: center;
    }
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);