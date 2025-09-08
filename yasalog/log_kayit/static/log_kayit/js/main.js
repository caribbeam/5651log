// Main JavaScript file for 5651 Log Application

document.addEventListener('DOMContentLoaded', function() {
    
    // Form validation for TC Kimlik No
    const tcInput = document.querySelector('input[name="tc_no"]');
    if (tcInput) {
        tcInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 11) {
                value = value.substring(0, 11);
            }
            e.target.value = value;
            
            // TC Kimlik validation
            if (value.length === 11) {
                if (validateTCKN(value)) {
                    e.target.classList.remove('is-invalid');
                    e.target.classList.add('is-valid');
                } else {
                    e.target.classList.remove('is-valid');
                    e.target.classList.add('is-invalid');
                }
            } else {
                e.target.classList.remove('is-valid', 'is-invalid');
            }
        });
    }
    
    // Phone number formatting
    const phoneInput = document.querySelector('input[name="telefon"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) {
                value = value.substring(0, 10);
            }
            
            // Format: (5XX) XXX XX XX
            if (value.length >= 3) {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3);
            }
            if (value.length >= 9) {
                value = value.substring(0, 9) + ' ' + value.substring(9);
            }
            if (value.length >= 12) {
                value = value.substring(0, 12) + ' ' + value.substring(12);
            }
            
            e.target.value = value;
        });
    }
    
    // Auto-submit form on TC Kimlik No enter
    const tcForm = document.querySelector('form');
    if (tcForm && tcInput) {
        tcInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.value.length === 11) {
                tcForm.submit();
            }
        });
    }
    
    // Loading state for buttons
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="loading"></span> İşleniyor...';
                this.disabled = true;
            }
        });
    });
    
    // Auto-refresh dashboard data every 30 seconds
    const dashboard = document.querySelector('.dashboard-box');
    if (dashboard) {
        setInterval(function() {
            refreshDashboardData();
        }, 30000);
    }
    
    // Export buttons with loading state
    const exportButtons = document.querySelectorAll('a[href*="export"]');
    exportButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="loading"></span> Hazırlanıyor...';
            this.style.pointerEvents = 'none';
            
            // Re-enable after 3 seconds if still on page
            setTimeout(() => {
                this.innerHTML = originalText;
                this.style.pointerEvents = 'auto';
            }, 3000);
        });
    });
    
    // Table row highlighting
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Search functionality
    const searchInput = document.querySelector('input[name="ad_soyad"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2) {
                    performSearch(this.value);
                }
            }, 500);
        });
    }
});

// TC Kimlik No validation function
function validateTCKN(tcno) {
    if (tcno.length !== 11) return false;
    
    // All digits must be same
    if (tcno[0] === tcno[1] && tcno[1] === tcno[2] && tcno[2] === tcno[3] && 
        tcno[3] === tcno[4] && tcno[4] === tcno[5] && tcno[5] === tcno[6] && 
        tcno[6] === tcno[7] && tcno[7] === tcno[8] && tcno[8] === tcno[9] && 
        tcno[9] === tcno[10]) {
        return false;
    }
    
    // First digit cannot be 0
    if (tcno[0] === '0') return false;
    
    // Calculate check digits
    let oddSum = parseInt(tcno[0]) + parseInt(tcno[2]) + parseInt(tcno[4]) + 
                 parseInt(tcno[6]) + parseInt(tcno[8]);
    let evenSum = parseInt(tcno[1]) + parseInt(tcno[3]) + parseInt(tcno[5]) + 
                  parseInt(tcno[7]);
    
    let digit10 = (oddSum * 7 - evenSum) % 10;
    if (digit10 !== parseInt(tcno[9])) return false;
    
    let sum = 0;
    for (let i = 0; i < 10; i++) {
        sum += parseInt(tcno[i]);
    }
    let digit11 = sum % 10;
    if (digit11 !== parseInt(tcno[10])) return false;
    
    return true;
}

// Refresh dashboard data
function refreshDashboardData() {
    const currentUrl = window.location.href;
    fetch(currentUrl)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update statistics
            const newStats = doc.querySelectorAll('.stat-card .fs-2');
            const currentStats = document.querySelectorAll('.stat-card .fs-2');
            
            newStats.forEach((stat, index) => {
                if (currentStats[index] && stat.textContent !== currentStats[index].textContent) {
                    currentStats[index].textContent = stat.textContent;
                    currentStats[index].style.animation = 'pulse 0.5s';
                    setTimeout(() => {
                        currentStats[index].style.animation = '';
                    }, 500);
                }
            });
        })
        .catch(error => {
            console.log('Dashboard refresh failed:', error);
        });
}

// Perform search
function performSearch(query) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('ad_soyad', query);
    
    fetch(currentUrl)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTable = doc.querySelector('.table-responsive');
            const currentTable = document.querySelector('.table-responsive');
            
            if (newTable && currentTable) {
                currentTable.innerHTML = newTable.innerHTML;
            }
        })
        .catch(error => {
            console.log('Search failed:', error);
        });
}

// Add pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style); 