// Medical Price Comparator - Admin Panel
// Simple, component-based approach

// Admin state
const adminState = {
  csvFile: null,
  csvPreviewData: null,
  isLoading: false,
  provider: '',
  apiBaseUrl: '/api/v1'
};

// Initialize admin panel
function initializeAdmin() {
  try {
    setupFileUpload();
    setupProviderSelection();
    console.log('Admin panel initialized successfully');
  } catch (error) {
    console.error('Failed to initialize admin panel:', error);
    showToast('Admin panel failed to initialize', 'error');
  }
}

// File upload setup
function setupFileUpload() {
  const csvFile = document.getElementById('csvFile');
  if (csvFile) {
    csvFile.addEventListener('change', handleCSVFileSelect);
  }
}

// Provider selection setup
function setupProviderSelection() {
  const providerSelect = document.getElementById('provider');
  if (providerSelect) {
    providerSelect.addEventListener('change', (e) => {
      adminState.provider = e.target.value;
    });
  }
}

// Handle CSV file selection
function handleCSVFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    adminState.csvFile = file;
    previewCSV();
  } else {
    adminState.csvFile = null;
    hideCSVPreview();
  }
}

// Preview CSV file
async function previewCSV() {
  if (!adminState.csvFile) {
    hideCSVPreview();
    return;
  }
  
  const previewContainer = document.getElementById('csvPreview');
  if (!previewContainer) return;
  
  try {
    setLoadingState(true);
    showCSVPreview();
    
    const formData = new FormData();
    formData.append('file', adminState.csvFile);
    
    const response = await fetch(`${adminState.apiBaseUrl}/admin/csv-preview`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Failed to preview CSV');
    }
    
    const data = await response.json();
    adminState.csvPreviewData = data;
    displayCSVPreview(data);
    
  } catch (error) {
    console.error('CSV preview error:', error);
    showToast('Failed to preview CSV file', 'error');
    hideCSVPreview();
  } finally {
    setLoadingState(false);
  }
}

// Display CSV preview
function displayCSVPreview(data) {
  const previewContainer = document.getElementById('csvPreview');
  if (!previewContainer) return;
  
  let html = `
    <div class="csv-preview-content">
      <h4 style="margin-bottom: 1rem; font-weight: 600;">CSV Preview</h4>
      <div style="margin-bottom: 1rem;">
        <strong>File:</strong> ${adminState.csvFile.name}<br>
        <strong>Rows:</strong> ${data.rows || 0}<br>
        <strong>Columns:</strong> ${data.columns || 0}
      </div>
  `;
  
  if (data.preview && data.preview.length > 0) {
    html += `
      <div style="overflow-x: auto; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.875rem;">
          <thead>
            <tr style="background: var(--gray-100);">
    `;
    
    // Headers
    Object.keys(data.preview[0]).forEach(header => {
      html += `<th style="padding: 0.5rem; border: 1px solid var(--gray-300); text-align: left;">${header}</th>`;
    });
    
    html += `
            </tr>
          </thead>
          <tbody>
    `;
    
    // Rows (show first 5)
    data.preview.slice(0, 5).forEach(row => {
      html += '<tr>';
      Object.values(row).forEach(cell => {
        html += `<td style="padding: 0.5rem; border: 1px solid var(--gray-300);">${cell || ''}</td>`;
      });
      html += '</tr>';
    });
    
    html += `
          </tbody>
        </table>
      </div>
    `;
    
    if (data.preview.length > 5) {
      html += `<p style="color: var(--gray-600); font-size: 0.875rem;">Showing first 5 rows of ${data.preview.length} total rows</p>`;
    }
  }
  
  html += '</div>';
  previewContainer.innerHTML = html;
}

// Show/hide CSV preview
function showCSVPreview() {
  const previewContainer = document.getElementById('csvPreview');
  if (previewContainer) {
    previewContainer.classList.add('show');
  }
}

function hideCSVPreview() {
  const previewContainer = document.getElementById('csvPreview');
  if (previewContainer) {
    previewContainer.classList.remove('show');
    previewContainer.innerHTML = '';
  }
}

// Import CSV data
async function importCSV() {
  if (!adminState.csvFile) {
    showToast('Please select a CSV file first', 'warning');
    return;
  }
  
  if (!adminState.provider) {
    showToast('Please select a provider', 'warning');
    return;
  }
  
  try {
    setButtonLoading('importButton', true);
    
    const formData = new FormData();
    formData.append('file', adminState.csvFile);
    formData.append('provider', adminState.provider);
    
    const response = await fetch(`${adminState.apiBaseUrl}/admin/import-csv`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Import failed');
    }
    
    const result = await response.json();
    showImportResult(result);
    showToast('CSV imported successfully', 'success');
    
    // Clear form
    clearImportForm();
    
  } catch (error) {
    console.error('Import error:', error);
    showToast('Failed to import CSV', 'error');
  } finally {
    setButtonLoading('importButton', false);
  }
}

// Show import result
function showImportResult(result) {
  const resultContainer = document.getElementById('importResult');
  if (!resultContainer) return;
  
  const html = `
    <div style="background: var(--success); color: white; padding: 1rem; border-radius: var(--radius); margin-top: 1rem;">
      <h4 style="margin-bottom: 0.5rem;">✅ Import Successful</h4>
      <p>Imported ${result.imported || 0} analyses for ${adminState.provider}</p>
      ${result.errors ? `<p style="margin-top: 0.5rem;">⚠️ ${result.errors} errors encountered</p>` : ''}
    </div>
  `;
  
  resultContainer.innerHTML = html;
  
  // Clear after 5 seconds
  setTimeout(() => {
    resultContainer.innerHTML = '';
  }, 5000);
}

// Clear import form
function clearImportForm() {
  const csvFile = document.getElementById('csvFile');
  const provider = document.getElementById('provider');
  
  if (csvFile) csvFile.value = '';
  if (provider) provider.value = '';
  
  adminState.csvFile = null;
  adminState.provider = '';
  adminState.csvPreviewData = null;
  
  hideCSVPreview();
}

// Load sample data
async function loadSampleData(provider) {
  if (!provider) {
    showToast('Provider not specified', 'warning');
    return;
  }
  
  try {
    const response = await fetch(`${adminState.apiBaseUrl}/admin/load-sample-data/${provider}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Failed to load sample data');
    }
    
    const result = await response.json();
    showSampleResult(result, provider);
    showToast(`Sample data loaded for ${provider}`, 'success');
    
  } catch (error) {
    console.error('Sample data error:', error);
    showToast(`Failed to load sample data for ${provider}`, 'error');
  }
}

// Show sample result
function showSampleResult(result, provider) {
  const resultContainer = document.getElementById('sampleResult');
  if (!resultContainer) return;
  
  const html = `
    <div style="background: var(--secondary); color: white; padding: 1rem; border-radius: var(--radius);">
      <h4 style="margin-bottom: 0.5rem;">✅ Sample Data Loaded</h4>
      <p>Loaded ${result.count || 0} sample analyses for ${provider}</p>
    </div>
  `;
  
  resultContainer.innerHTML = html;
  
  // Clear after 5 seconds
  setTimeout(() => {
    resultContainer.innerHTML = '';
  }, 5000);
}

// Load import history
async function loadImportHistory() {
  const historyContainer = document.getElementById('importHistory');
  if (!historyContainer) return;
  
  try {
    historyContainer.innerHTML = '<div class="loading-state">Loading import history...</div>';
    
    const response = await fetch(`${adminState.apiBaseUrl}/admin/import-history`);
    
    if (!response.ok) {
      throw new Error('Failed to load import history');
    }
    
    const history = await response.json();
    displayImportHistory(history);
    
  } catch (error) {
    console.error('History error:', error);
    historyContainer.innerHTML = '<div style="color: var(--danger);">Failed to load import history</div>';
  }
}

// Display import history
function displayImportHistory(history) {
  const historyContainer = document.getElementById('importHistory');
  if (!historyContainer) return;
  
  if (!history.imports || history.imports.length === 0) {
    historyContainer.innerHTML = '<p style="color: var(--gray-500);">No import history found</p>';
    return;
  }
  
  let html = '<div class="history-list">';
  
  history.imports.forEach(item => {
    html += `
      <div style="background: var(--gray-50); padding: 1rem; border-radius: var(--radius); margin-bottom: 1rem;">
        <div style="font-weight: 600; margin-bottom: 0.5rem;">${item.provider || 'Unknown'}</div>
        <div style="font-size: 0.875rem; color: var(--gray-600);">
          ${item.date || 'Unknown date'} - ${item.count || 0} items imported
        </div>
      </div>
    `;
  });
  
  html += '</div>';
  historyContainer.innerHTML = html;
}

// Clear all data
async function clearAllData() {
  if (!confirm('Are you sure you want to clear ALL data? This action cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch(`${adminState.apiBaseUrl}/admin/clear-all`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error('Failed to clear data');
    }
    
    const result = await response.json();
    showClearResult(result);
    showToast('All data cleared successfully', 'success');
    
  } catch (error) {
    console.error('Clear data error:', error);
    showToast('Failed to clear data', 'error');
  }
}

// Show clear result
function showClearResult(result) {
  const resultContainer = document.getElementById('clearResult');
  if (!resultContainer) return;
  
  const html = `
    <div style="background: var(--danger); color: white; padding: 1rem; border-radius: var(--radius);">
      <h4 style="margin-bottom: 0.5rem;">🗑️ Data Cleared</h4>
      <p>Removed ${result.deleted || 0} items from database</p>
    </div>
  `;
  
  resultContainer.innerHTML = html;
  
  // Clear after 5 seconds
  setTimeout(() => {
    resultContainer.innerHTML = '';
  }, 5000);
}

// Set loading state
function setLoadingState(isLoading) {
  adminState.isLoading = isLoading;
  // Could add global loading indicator here if needed
}

// Initialize when DOM is ready
function onAdminReady() {
  initializeAdmin();
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', onAdminReady);
} else {
  onAdminReady();
}

// Make functions globally available
window.previewCSV = previewCSV;
window.importCSV = importCSV;
window.loadSampleData = loadSampleData;
window.loadImportHistory = loadImportHistory;
window.clearAllData = clearAllData;