document.addEventListener('DOMContentLoaded', function() {
    // Search functionality for fee tables
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('.fee-table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
    
    // Filter functionality
    const semesterFilter = document.getElementById('semesterFilter');
    const yearFilter = document.getElementById('yearFilter');
    
    if (semesterFilter || yearFilter) {
        const applyFilters = () => {
            const semesterValue = semesterFilter ? semesterFilter.value.toLowerCase() : '';
            const yearValue = yearFilter ? yearFilter.value : '';
            const rows = document.querySelectorAll('.fee-table tbody tr');
            
            rows.forEach(row => {
                const semesterCell = row.querySelector('td:nth-child(3)');
                const dateCell = row.querySelector('td:nth-child(7)');
                
                const semesterMatch = !semesterValue || semesterCell.textContent.toLowerCase().includes(semesterValue);
                const yearMatch = !yearValue || (dateCell.textContent && dateCell.textContent.includes(yearValue));
                
                row.style.display = semesterMatch && yearMatch ? '' : 'none';
            });
        };
        
        if (semesterFilter) {
            semesterFilter.addEventListener('change', applyFilters);
        }
        
        if (yearFilter) {
            yearFilter.addEventListener('change', applyFilters);
        }
    }
    
    // Calculate balance amount when editing
    const totalAmountInput = document.getElementById('total_amount');
    const discountInput = document.getElementById('discount');
    const paidAmountInput = document.getElementById('paid_amount');
    const balanceAmountInput = document.getElementById('balance_amount');
    
    if (totalAmountInput && discountInput && paidAmountInput && balanceAmountInput) {
        const calculateBalance = () => {
            const total = parseFloat(totalAmountInput.value) || 0;
            const discount = parseFloat(discountInput.value) || 0;
            const paid = parseFloat(paidAmountInput.value) || 0;
            
            const balance = (total - discount) - paid;
            balanceAmountInput.value = balance.toFixed(2);
        };
        
        totalAmountInput.addEventListener('input', calculateBalance);
        discountInput.addEventListener('input', calculateBalance);
        paidAmountInput.addEventListener('input', calculateBalance);
    }
    
    // Button hover animations
    const buttons = document.querySelectorAll('.btn, .class-btn, .group-btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
        
        button.addEventListener('mousedown', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        });
        
        button.addEventListener('mouseup', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
        });
    });
    
    // Form input focus effects
    const formInputs = document.querySelectorAll('.form-input');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.borderColor = 'var(--primary-color)';
            this.style.boxShadow = '0 0 0 3px rgba(255, 123, 0, 0.2)';
        });
        
        input.addEventListener('blur', function() {
            this.style.borderColor = '#ddd';
            this.style.boxShadow = '';
        });
    });
});