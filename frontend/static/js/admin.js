// Medical Price Comparator - Admin Panel Logic

// Configuration
const API_BASE_URL = '/api/v1';
let csvPreviewData = null;
let isPreviewLoading = false;

// CSV Preview and Import Functions
async function previewCSV() {
    const fileInput = document.getElementById('csvFile');
    const previewContainer = document.getElementById('csvPreview');
    
    if (isPreviewLoading) {
        console.log('Preview already loading, skipping');
        return;
    }
    
    if (!fileInput.files[0]) {
        previewContainer.classList.add('hidden');
        return;
    }
    
    isPreviewLoading = true;
    const previewContent = document.getElementById('previewContent');
    previewContent.innerHTML = '<div class="text-center"><div class="loading-spinner inline-block mr-2"></div>Loading CSV preview...</div>';
    previewContainer.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/csv-preview`, {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(30000)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to preview CSV');
        }
        
        csvPreviewData = await response.json();
        displayCSVPreview(csvPreviewData);
        previewContainer.classList.remove('hidden');
    } catch (error) {
        console.error('CSV preview error:', error);
        previewContent.innerHTML = `<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">Error previewing CSV: ${error.message}</div>`;
    } finally {
        isPreviewLoading = false;
    }
}

function displayCSVPreview(data) {
    const previewContent = document.getElementById('previewContent');
    const mappingFields = document.getElementById('mappingFields');
    
    // Display sample rows
    let html = '<h5 class="font-semibold mb-3">Sample Data:</h5>';
    html += '<div class="overflow-x-auto">';
    html += '<table class="table-modern"><thead><tr>';
    
    data.fieldnames.forEach(field => {
        html += `<th>${field}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    data.sample_rows.forEach(row => {
        html += '<tr>';
        data.fieldnames.forEach(field => {
            html += `<td>${row[field] || ''}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    
    previewContent.innerHTML = html;
    
    // Create field mapping
    const mapping = data.suggested_mapping;
    let mappingHTML = '<h5 class="font-semibold mb-3">Field Mapping:</h5>';
    mappingHTML += '<div class="grid md:grid-cols-2 gap-4">';
    
    const requiredFields = [
        {key: 'name', label: 'Analysis Name', required: true},
        {key: 'price', label: 'Price (Normal)', required: true},
        {key: 'currency', label: 'Currency', required: false},
        {key: 'category', label: 'Category', required: false},
        {key: 'price_type', label: 'Price Type', required: false},
        {key: 'alternative_names', label: 'Alternative Names', required: false},
        {key: 'description', label: 'Description', required: false}
    ];
    
    requiredFields.forEach(field => {
        mappingHTML += `
            <div class="form-group">
                <label class="form-label">${field.label}${field.required ? ' *' : ''}:</label>
                <select id="mapping_${field.key}" class="form-select">
                    <option value="">-- Select Field --</option>
        `;
        
        data.fieldnames.forEach(csvField => {
            const selected = mapping[field.key] === csvField ? 'selected' : '';
            mappingHTML += `<option value="${csvField}" ${selected}>${csvField}</option>`;
        });
        
        mappingHTML += '</select></div>';
    });
    
    mappingHTML += '</div>';
    mappingFields.innerHTML = mappingHTML;
}

async function importCSV() {
    const fileInput = document.getElementById('csvFile');
    const providerSelect = document.getElementById('provider');
    const loading = document.getElementById('importLoading');
    const result = document.getElementById('importResult');
    
    if (!fileInput.files[0]) {
        showNotification('Please select a CSV file', 'error');
        return;
    }
    
    if (!providerSelect.value) {
        showNotification('Please select a provider', 'error');
        return;
    }
    
    // Collect field mapping
    const mapping = {};
    const requiredFields = ['name', 'price'];
    
    for (let field of requiredFields) {
        const selectElement = document.getElementById(`mapping_${field}`);
        if (!selectElement.value) {
            showNotification(`Please map the required field: ${field}`, 'error');
            return;
        }
        mapping[field] = selectElement.value;
    }
    
    // Optional fields
    const optionalFields = ['currency', 'category', 'price_type', 'alternative_names', 'description'];
    for (let field of optionalFields) {
        const selectElement = document.getElementById(`mapping_${field}`);
        if (selectElement.value) {
            mapping[field] = selectElement.value;
        }
    }
    
    loading.classList.remove('hidden');
    result.innerHTML = '';
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('provider', providerSelect.value);
    formData.append('field_mapping', JSON.stringify(mapping));
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/import-csv`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            result.innerHTML = `
                <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h4 class="font-semibold text-green-800 mb-2">✅ Import Successful!</h4>
                    <div class="text-sm text-green-700">
                        <p><strong>Total records:</strong> ${data.total_records}</p>
                        <p><strong>Successful imports:</strong> ${data.successful_imports}</p>
                        <p><strong>Errors:</strong> ${data.errors}</p>
                        ${data.error_details && data.error_details.length > 0 ? 
                            `<details class="mt-2">
                                <summary class="cursor-pointer font-medium">Error Details</summary>
                                <ul class="mt-2 ml-4 list-disc">
                                    ${data.error_details.map(e => `<li>${e}</li>`).join('')}
                                </ul>
                            </details>` 
                            : ''}
                    </div>
                </div>
            `;
            showNotification('CSV import completed successfully', 'success');
        } else {
            result.innerHTML = `
                <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 class="font-semibold text-red-800 mb-2">❌ Import Failed</h4>
                    <p class="text-red-700">${data.detail}</p>
                </div>
            `;
            showNotification('CSV import failed', 'error');
        }
    } catch (error) {
        result.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 class="font-semibold text-red-800 mb-2">❌ Import Failed</h4>
                <p class="text-red-700">${error.message}</p>
            </div>
        `;
        showNotification('CSV import failed: ' + error.message, 'error');
    } finally {
        loading.classList.add('hidden');
    }
}

// Import History Functions
async function loadImportHistory() {
    const loading = document.getElementById('historyLoading');
    const history = document.getElementById('importHistory');
    
    loading.classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/import-history`);
        const data = await response.json();
        
        let html = '<h4 class="font-semibold mb-4">Recent Imports</h4>';
        
        if (data.imports && data.imports.length > 0) {
            html += '<div class="overflow-x-auto">';
            html += '<table class="table-modern">';
            html += '<thead><tr><th>Date</th><th>File</th><th>Provider</th><th>Total</th><th>Success</th><th>Errors</th></tr></thead>';
            html += '<tbody>';
            
            data.imports.forEach(imp => {
                html += `
                    <tr>
                        <td>${new Date(imp.import_date).toLocaleString()}</td>
                        <td>${imp.filename}</td>
                        <td class="capitalize">${imp.provider}</td>
                        <td>${imp.total_records}</td>
                        <td class="text-green-600 font-semibold">${imp.successful_imports}</td>
                        <td class="text-red-600 font-semibold">${imp.errors ? imp.errors.length : 0}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table></div>';
        } else {
            html += '<div class="text-center py-8 text-gray-600">';
            html += '<span class="icon icon-file text-4xl text-gray-300 mb-2"></span>';
            html += '<p>No import history found.</p>';
            html += '</div>';
        }
        
        history.innerHTML = html;
    } catch (error) {
        history.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 class="font-semibold text-red-800 mb-2">❌ Failed to Load History</h4>
                <p class="text-red-700">${error.message}</p>
            </div>
        `;
    } finally {
        loading.classList.add('hidden');
    }
}

// Sample Data Functions
async function loadSampleData(provider) {
    const loading = document.getElementById('sampleLoading');
    const result = document.getElementById('sampleResult');
    
    loading.classList.remove('hidden');
    result.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/load-sample-data/${provider}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            result.innerHTML = `
                <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h4 class="font-semibold text-green-800 mb-3">✅ Sample Data Loaded Successfully</h4>
                    <div class="text-sm text-green-700 space-y-1">
                        <p><strong>Provider:</strong> <span class="capitalize">${data.provider}</span></p>
                        <p><strong>Records Processed:</strong> ${data.total_records}</p>
                        <p><strong>Successfully Imported:</strong> ${data.successful_imports}</p>
                        ${data.errors > 0 ? `<p><strong>Errors:</strong> ${data.errors}</p>` : ''}
                        ${data.error_details && data.error_details.length > 0 ? 
                            `<details class="mt-2">
                                <summary class="cursor-pointer font-medium">Error Details</summary>
                                <ul class="mt-2 ml-4 list-disc">
                                    ${data.error_details.map(err => `<li>${err}</li>`).join('')}
                                </ul>
                            </details>` : 
                            ''
                        }
                    </div>
                    <div class="mt-3 p-3 bg-green-100 rounded text-green-800 text-sm">
                        <strong>📊 Sample data has been loaded into the database and is now available for search and comparison.</strong>
                    </div>
                </div>
            `;
            showNotification(`Sample data for ${provider} loaded successfully`, 'success');
        } else {
            result.innerHTML = `
                <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 class="font-semibold text-red-800 mb-2">❌ Failed to Load Sample Data</h4>
                    <p class="text-red-700">${data.detail || 'Unknown error occurred'}</p>
                </div>
            `;
            showNotification('Failed to load sample data', 'error');
        }
    } catch (error) {
        result.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 class="font-semibold text-red-800 mb-2">❌ Error Loading Sample Data</h4>
                <p class="text-red-700">Network error: ${error.message}</p>
                <p class="text-red-600 text-sm mt-1">Please check your connection and try again.</p>
            </div>
        `;
        showNotification('Error loading sample data: ' + error.message, 'error');
    } finally {
        loading.classList.add('hidden');
    }
}

// Danger Zone Functions
async function clearAllData() {
    const result = document.getElementById('clearResult');
    
    if (!confirm('Are you sure you want to delete ALL analysis data? This cannot be undone!')) {
        return;
    }
    
    const confirmation = prompt('Type "DELETE_ALL_DATA" to confirm:');
    if (confirmation !== 'DELETE_ALL_DATA') {
        result.innerHTML = `
            <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p class="text-yellow-800">⚠️ Confirmation failed. Data not deleted.</p>
            </div>
        `;
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/clear-data?confirm=DELETE_ALL_DATA`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            result.innerHTML = `
                <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <h4 class="font-semibold text-green-800 mb-2">✅ Data Cleared Successfully</h4>
                    <p class="text-green-700">${data.message}</p>
                </div>
            `;
            showNotification('All data cleared successfully', 'success');
        } else {
            result.innerHTML = `
                <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 class="font-semibold text-red-800 mb-2">❌ Failed to Clear Data</h4>
                    <p class="text-red-700">${data.detail}</p>
                </div>
            `;
            showNotification('Failed to clear data', 'error');
        }
    } catch (error) {
        result.innerHTML = `
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 class="font-semibold text-red-800 mb-2">❌ Failed to Clear Data</h4>
                <p class="text-red-700">${error.message}</p>
            </div>
        `;
        showNotification('Failed to clear data: ' + error.message, 'error');
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const notification = document.createElement('div');
    notification.className = `p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;
    
    const styles = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    
    const icons = {
        success: 'icon-check',
        error: 'icon-times',
        warning: 'icon-warning',
        info: 'icon-info'
    };
    
    notification.className += ` ${styles[type]}`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <span class="icon ${icons[type]}"></span>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 hover:opacity-75">
                <span class="icon icon-times"></span>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

// Initialize Admin Panel
document.addEventListener('DOMContentLoaded', function() {
    console.log('Medical Price Comparator Admin Panel initialized');
    
    // Set up global error handling
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        showNotification('An unexpected error occurred', 'error');
    });
});