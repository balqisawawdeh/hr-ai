// HR-Max JavaScript Functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation enhancements
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Search functionality
    initializeSearch();
    
    // Table enhancements
    initializeTableFeatures();
    
    // Form enhancements
    initializeFormFeatures();
});

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const searchForm = document.getElementById('search-form');
    
    if (searchInput && searchForm) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function() {
                if (searchInput.value.length >= 2 || searchInput.value.length === 0) {
                    searchForm.submit();
                }
            }, 500);
        });
    }

    // Live employee search for manager selection
    const managerSelect = document.getElementById('id_manager');
    if (managerSelect) {
        initializeEmployeeSearch();
    }
}

// Employee search for AJAX requests
function initializeEmployeeSearch() {
    const searchInput = document.getElementById('employee-search');
    const resultsContainer = document.getElementById('search-results');
    
    if (!searchInput || !resultsContainer) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultsContainer.innerHTML = '';
            resultsContainer.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(function() {
            fetch(`/api/employees/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data.employees, resultsContainer);
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', function(event) {
        if (!searchInput.contains(event.target) && !resultsContainer.contains(event.target)) {
            resultsContainer.style.display = 'none';
        }
    });
}

function displaySearchResults(employees, container) {
    if (employees.length === 0) {
        container.innerHTML = '<div class="p-3 text-muted">No employees found</div>';
    } else {
        const html = employees.map(emp => `
            <div class="search-result-item p-3 border-bottom" data-employee-id="${emp.id}">
                <div class="fw-bold">${emp.name}</div>
                <div class="text-muted small">${emp.employee_id} - ${emp.department} - ${emp.position}</div>
            </div>
        `).join('');
        container.innerHTML = html;
        
        // Add click handlers
        container.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', function() {
                const employeeId = this.dataset.employeeId;
                const employeeName = this.querySelector('.fw-bold').textContent;
                selectEmployee(employeeId, employeeName);
                container.style.display = 'none';
            });
        });
    }
    
    container.style.display = 'block';
}

function selectEmployee(employeeId, employeeName) {
    const hiddenInput = document.getElementById('selected-employee-id');
    const displayInput = document.getElementById('employee-search');
    
    if (hiddenInput && displayInput) {
        hiddenInput.value = employeeId;
        displayInput.value = employeeName;
    }
}

// Table enhancements
function initializeTableFeatures() {
    // Sortable table headers
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
    
    // Row selection
    const selectAllCheckbox = document.getElementById('select-all');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    
    if (selectAllCheckbox && rowCheckboxes.length > 0) {
        selectAllCheckbox.addEventListener('change', function() {
            rowCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                toggleRowSelection(checkbox.closest('tr'), this.checked);
            });
            updateBulkActions();
        });
        
        rowCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                toggleRowSelection(this.closest('tr'), this.checked);
                updateSelectAllState();
                updateBulkActions();
            });
        });
    }
}

function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Remove existing sort classes
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add new sort class
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        if (isAscending) {
            return bValue.localeCompare(aValue, undefined, { numeric: true });
        } else {
            return aValue.localeCompare(bValue, undefined, { numeric: true });
        }
    });
    
    // Reorder rows
    rows.forEach(row => tbody.appendChild(row));
}

function toggleRowSelection(row, selected) {
    if (selected) {
        row.classList.add('table-active');
    } else {
        row.classList.remove('table-active');
    }
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('select-all');
    const rowCheckboxes = document.querySelectorAll('.row-checkbox');
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.indeterminate = checkedBoxes.length > 0 && checkedBoxes.length < rowCheckboxes.length;
        selectAllCheckbox.checked = checkedBoxes.length === rowCheckboxes.length && rowCheckboxes.length > 0;
    }
}

function updateBulkActions() {
    const checkedBoxes = document.querySelectorAll('.row-checkbox:checked');
    const bulkActions = document.getElementById('bulk-actions');
    
    if (bulkActions) {
        bulkActions.style.display = checkedBoxes.length > 0 ? 'block' : 'none';
    }
}

// Form enhancements
function initializeFormFeatures() {
    // Auto-save draft functionality
    const forms = document.querySelectorAll('form[data-auto-save]');
    forms.forEach(form => {
        const formId = form.id || 'default-form';
        loadFormDraft(form, formId);
        
        form.addEventListener('input', function() {
            saveFormDraft(form, formId);
        });
        
        form.addEventListener('submit', function() {
            clearFormDraft(formId);
        });
    });
    
    // Character counters
    const textareas = document.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.dataset.maxLength);
        const counter = document.createElement('div');
        counter.className = 'text-muted small mt-1';
        textarea.parentNode.appendChild(counter);
        
        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} characters remaining`;
            counter.className = remaining < 50 ? 'text-danger small mt-1' : 'text-muted small mt-1';
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const message = this.dataset.confirmDelete || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
}

// Form draft functionality
function saveFormDraft(form, formId) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`form-draft-${formId}`, JSON.stringify(data));
}

function loadFormDraft(form, formId) {
    const draftData = localStorage.getItem(`form-draft-${formId}`);
    
    if (draftData) {
        try {
            const data = JSON.parse(draftData);
            
            for (let [key, value] of Object.entries(data)) {
                const field = form.querySelector(`[name="${key}"]`);
                if (field && field.type !== 'hidden') {
                    field.value = value;
                }
            }
        } catch (error) {
            console.error('Error loading form draft:', error);
        }
    }
}

function clearFormDraft(formId) {
    localStorage.removeItem(`form-draft-${formId}`);
}

// Utility functions
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<span class="loading"></span> Loading...';
    element.disabled = true;
    
    return function hideLoading() {
        element.innerHTML = originalContent;
        element.disabled = false;
    };
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }).catch(function(error) {
        console.error('Copy failed:', error);
        showToast('Failed to copy to clipboard', 'error');
    });
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Export functions for global use
window.HRMax = {
    showLoading,
    copyToClipboard,
    showToast,
    selectEmployee
};

