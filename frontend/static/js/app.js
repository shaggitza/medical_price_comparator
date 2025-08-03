// Medical Price Comparator - Main Application Logic
// Vanilla JavaScript implementation

// Global state
let appState = {
    selectedFile: null,
    selectedFileName: '',
    isProcessing: false,
    analysisTable: [],
    pendingItems: [],
    providers: ['reginamaria', 'medlife'],
    ocrResults: [],
    unmatchedItems: [],
    suggestions: [],
    showSuggestions: false,
    searchQuery: '',
    apiBaseUrl: '/api/v1'
};

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        appState.selectedFile = file;
        appState.selectedFileName = file.name;
        updateFileDisplay();
        updateProcessButton();
    }
}

function clearFile() {
    appState.selectedFile = null;
    appState.selectedFileName = '';
    document.getElementById('imageFile').value = '';
    updateFileDisplay();
    updateProcessButton();
}

function updateFileDisplay() {
    const fileInfo = document.getElementById('selectedFileInfo');
    const fileName = document.getElementById('selectedFileName');
    
    if (appState.selectedFile) {
        fileName.textContent = appState.selectedFileName;
        fileInfo.classList.remove('hidden');
    } else {
        fileInfo.classList.add('hidden');
    }
}

function updateProcessButton() {
    const btn = document.getElementById('processBtn');
    const hasFile = appState.selectedFile !== null;
    const isProcessing = appState.isProcessing;
    
    btn.disabled = !hasFile || isProcessing;
    btn.className = `btn btn-primary ${(!hasFile || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}`;
}

// OCR Processing
async function processOCR() {
    if (!appState.selectedFile) {
        showNotification('Please select an image file', 'error');
        return;
    }
    
    appState.isProcessing = true;
    updateProcessingState();
    
    const formData = new FormData();
    formData.append('image', appState.selectedFile);
    
    try {
        const response = await fetch(`${appState.apiBaseUrl}/ocr/process`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.analyses && result.analyses.length > 0) {
            await processOCRResults(result.analyses);
        } else {
            showNotification('No analyses detected in the image. Please try a clearer image or add analyses manually.', 'warning');
        }
    } catch (error) {
        console.error('OCR Error:', error);
        showNotification('Error processing image: ' + error.message, 'error');
    } finally {
        appState.isProcessing = false;
        updateProcessingState();
    }
}

function updateProcessingState() {
    const icon = document.getElementById('processIcon');
    const text = document.getElementById('processText');
    
    if (appState.isProcessing) {
        icon.className = 'loading-spinner';
        text.textContent = 'Processing...';
    } else {
        icon.className = 'icon icon-magic';
        text.textContent = 'Process with AI';
    }
    updateProcessButton();
}

async function processOCRResults(detectedAnalyses) {
    const matched = [];
    const unmatched = [];
    
    for (const analysisName of detectedAnalyses) {
        try {
            const response = await fetch(`${appState.apiBaseUrl}/analyses/compare`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    analysis_names: [analysisName]
                })
            });
            
            const data = await response.json();
            
            if (data.results && data.results.length > 0 && data.results[0].found !== false) {
                matched.push(data.results[0]);
            } else {
                unmatched.push(analysisName);
            }
        } catch (error) {
            unmatched.push(analysisName);
        }
    }
    
    // Add matched analyses to table
    matched.forEach(analysis => {
        if (!appState.analysisTable.some(item => item.name === analysis.name)) {
            appState.analysisTable.push(analysis);
        }
    });
    
    // Add unmatched items to pending resolution
    unmatched.forEach((item, index) => {
        if (!appState.pendingItems.some(pending => pending.detectedText === item)) {
            appState.pendingItems.push({
                detectedText: item,
                id: Date.now() + index,
                suggestions: []
            });
        }
    });
    
    appState.ocrResults = matched;
    appState.unmatchedItems = unmatched.map((item, index) => ({
        detectedText: item,
        id: Date.now() + index
    }));
    
    updateProviders();
    updateOCRResults();
    updateAnalysisTable();
    
    if (matched.length > 0) {
        showNotification(`Successfully matched ${matched.length} analysis${matched.length > 1 ? 'es' : ''}`, 'success');
    }
}

function updateOCRResults() {
    const resultsDiv = document.getElementById('ocrResults');
    const resultsList = document.getElementById('ocrResultsList');
    const unmatchedDiv = document.getElementById('unmatchedItems');
    const unmatchedList = document.getElementById('unmatchedItemsList');
    
    // Update matched results
    if (appState.ocrResults.length > 0) {
        let html = '';
        appState.ocrResults.forEach(result => {
            html += `
                <div class="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div class="flex items-center justify-between">
                        <div>
                            <span class="font-medium">${result.name}</span>
                            <span class="text-sm text-gray-600 ml-2">${result.category || ''}</span>
                        </div>
                        <span class="status-badge status-success">
                            <span class="icon icon-check"></span>
                            Matched
                        </span>
                    </div>
                </div>
            `;
        });
        resultsList.innerHTML = html;
        resultsDiv.classList.remove('hidden');
    } else {
        resultsDiv.classList.add('hidden');
    }
    
    // Update unmatched items
    if (appState.unmatchedItems.length > 0) {
        let html = '';
        appState.unmatchedItems.forEach(item => {
            html += `
                <div class="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-medium">${item.detectedText}</span>
                        <span class="status-badge status-pending">
                            <span class="icon icon-clock"></span>
                            Pending
                        </span>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="dismissUnmatched(${item.id})" class="btn btn-sm btn-outline">
                            <span class="icon icon-times"></span>
                            Dismiss
                        </button>
                    </div>
                </div>
            `;
        });
        unmatchedList.innerHTML = html;
        unmatchedDiv.classList.remove('hidden');
    } else {
        unmatchedDiv.classList.add('hidden');
    }
}

// Search functionality
let searchTimeout = null;

function handleSearchInput(event) {
    const query = event.target.value.trim();
    appState.searchQuery = query;
    
    clearTimeout(searchTimeout);
    
    if (query.length < 2) {
        hideSuggestions();
        return;
    }
    
    searchTimeout = setTimeout(() => {
        fetchSuggestions(query);
    }, 300);
}

function handleSearchKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        addAnalysisFromSearch();
    } else if (event.key === 'Escape') {
        hideSuggestions();
    }
}

async function fetchSuggestions(query) {
    try {
        const response = await fetch(`${appState.apiBaseUrl}/analyses/suggestions?query=${encodeURIComponent(query)}&limit=8`);
        const data = await response.json();
        appState.suggestions = data.suggestions || [];
        updateSuggestions();
    } catch (error) {
        console.error('Error fetching suggestions:', error);
        appState.suggestions = [];
        hideSuggestions();
    }
}

function updateSuggestions() {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    
    if (appState.suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    let html = '';
    appState.suggestions.forEach(suggestion => {
        html += `
            <div class="suggestion-item" onclick="selectSuggestion('${suggestion.name}')">
                <div class="font-medium">${suggestion.name}</div>
                <div class="suggestion-category">${suggestion.category}</div>
            </div>
        `;
    });
    
    suggestionsDiv.innerHTML = html;
    suggestionsDiv.classList.remove('hidden');
}

function hideSuggestions() {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    suggestionsDiv.classList.add('hidden');
}

function showSuggestions() {
    if (appState.suggestions.length > 0) {
        document.getElementById('searchSuggestions').classList.remove('hidden');
    }
}

function selectSuggestion(analysisName) {
    document.getElementById('searchInput').value = analysisName;
    appState.searchQuery = analysisName;
    hideSuggestions();
    addAnalysisFromSearch();
}

async function addAnalysisFromSearch() {
    const analysisName = appState.searchQuery.trim();
    
    if (!analysisName) {
        showNotification('Please enter an analysis name', 'error');
        return;
    }
    
    // Check if already in table
    if (appState.analysisTable.some(item => item.name.toLowerCase() === analysisName.toLowerCase())) {
        showNotification('This analysis is already in the table', 'warning');
        document.getElementById('searchInput').value = '';
        appState.searchQuery = '';
        hideSuggestions();
        return;
    }
    
    try {
        const response = await fetch(`${appState.apiBaseUrl}/analyses/compare`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                analysis_names: [analysisName]
            })
        });
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0 && data.results[0].found !== false) {
            const analysis = data.results[0];
            appState.analysisTable.push(analysis);
            document.getElementById('searchInput').value = '';
            appState.searchQuery = '';
            hideSuggestions();
            updateProviders();
            updateAnalysisTable();
            showNotification(`Added "${analysis.name}" to comparison table`, 'success');
        } else {
            showNotification('Analysis not found in database', 'error');
        }
    } catch (error) {
        console.error('Error adding analysis:', error);
        showNotification('Error adding analysis: ' + error.message, 'error');
    }
}

// Table management
function removeAnalysis(index) {
    const analysis = appState.analysisTable[index];
    appState.analysisTable.splice(index, 1);
    updateProviders();
    updateAnalysisTable();
    showNotification(`Removed "${analysis.name}" from table`, 'success');
}

function dismissPending(index) {
    const pending = appState.pendingItems[index];
    appState.pendingItems.splice(index, 1);
    updateAnalysisTable();
    showNotification(`Dismissed "${pending.detectedText}"`, 'success');
}

function dismissUnmatched(itemId) {
    appState.unmatchedItems = appState.unmatchedItems.filter(item => item.id !== itemId);
    updateOCRResults();
}

function updateAnalysisTable() {
    const emptyTable = document.getElementById('emptyTable');
    const tableContainer = document.getElementById('analysisTableContainer');
    const tableBody = document.getElementById('analysisTableBody');
    const totalsSection = document.getElementById('totalsSection');
    
    const hasData = appState.analysisTable.length > 0 || appState.pendingItems.length > 0;
    
    if (hasData) {
        emptyTable.classList.add('hidden');
        tableContainer.classList.remove('hidden');
        
        // Update table body
        let html = '';
        
        // Add confirmed analyses
        appState.analysisTable.forEach((analysis, index) => {
            html += `
                <tr>
                    <td>
                        <div>
                            <div class="font-semibold">${analysis.name}</div>
                            ${analysis.alternative_names && analysis.alternative_names.length > 0 ? 
                                `<div class="text-sm text-gray-600">(${analysis.alternative_names.join(', ')})</div>` : ''}
                        </div>
                    </td>
                    <td>${formatProviderPrices(analysis, 'reginamaria')}</td>
                    <td>${formatProviderPrices(analysis, 'medlife')}</td>
                    <td>
                        <button onclick="removeAnalysis(${index})" class="btn btn-sm btn-danger">
                            <span class="icon icon-trash"></span>
                            Remove
                        </button>
                    </td>
                </tr>
            `;
        });
        
        // Add pending items
        appState.pendingItems.forEach((pending, index) => {
            html += `
                <tr class="bg-yellow-50">
                    <td>
                        <div class="flex items-center gap-2 mb-2">
                            <span class="icon icon-warning text-yellow-600"></span>
                            <span class="font-medium text-yellow-800">${pending.detectedText}</span>
                        </div>
                        <div class="text-xs text-yellow-700">OCR detected item - needs manual resolution</div>
                    </td>
                    <td colspan="2">
                        <div class="relative">
                            <input type="text" 
                                   value="${pending.detectedText}"
                                   placeholder="Search for analysis name..."
                                   class="form-input text-sm"
                                   onchange="handlePendingSearch(${pending.id}, this.value)">
                        </div>
                    </td>
                    <td>
                        <button onclick="dismissPending(${index})" class="btn btn-sm btn-outline">
                            <span class="icon icon-times"></span>
                            Dismiss
                        </button>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
        
        // Update totals
        updateTotals();
    } else {
        emptyTable.classList.remove('hidden');
        tableContainer.classList.add('hidden');
        totalsSection.classList.add('hidden');
    }
}

function formatProviderPrices(analysis, provider) {
    const prices = analysis.prices && analysis.prices[provider];
    if (!prices) {
        return '<div class="text-gray-400">N/A</div>';
    }
    
    let html = '<div>';
    if (prices.normal) {
        html += `<div class="mb-1">
            <span class="text-xs font-medium text-gray-600">Normal:</span>
            <span class="font-semibold">${prices.normal.amount} ${prices.normal.currency}</span>
        </div>`;
    }
    if (prices.premium) {
        html += `<div class="mb-1">
            <span class="text-xs font-medium text-gray-600">Premium:</span>
            <span class="font-semibold">${prices.premium.amount} ${prices.premium.currency}</span>
        </div>`;
    }
    if (prices.subscription) {
        html += `<div>
            <span class="text-xs font-medium text-gray-600">Subscription:</span>
            <span class="font-semibold">${prices.subscription.amount} ${prices.subscription.currency}</span>
        </div>`;
    }
    html += '</div>';
    return html;
}

function updateTotals() {
    const totalsSection = document.getElementById('totalsSection');
    const totalsGrid = document.getElementById('totalsGrid');
    
    if (appState.analysisTable.length === 0) {
        totalsSection.classList.add('hidden');
        return;
    }
    
    let html = '';
    appState.providers.forEach(provider => {
        const totals = getProviderTotal(provider);
        if (totals.hasData) {
            html += `
                <div class="p-4 bg-gray-50 rounded-lg">
                    <h5 class="font-semibold mb-3">${provider.charAt(0).toUpperCase() + provider.slice(1)}</h5>
                    <div class="space-y-2">
                        ${totals.normal > 0 ? `
                            <div class="flex justify-between">
                                <span class="text-sm text-gray-600">Normal Plan:</span>
                                <span class="font-semibold">${totals.normal.toFixed(2)} RON</span>
                            </div>
                        ` : ''}
                        ${totals.premium > 0 ? `
                            <div class="flex justify-between">
                                <span class="text-sm text-gray-600">Premium Plan:</span>
                                <span class="font-semibold">${totals.premium.toFixed(2)} RON</span>
                            </div>
                        ` : ''}
                        ${totals.subscription > 0 ? `
                            <div class="flex justify-between">
                                <span class="text-sm text-gray-600">Subscription Plan:</span>
                                <span class="font-semibold">${totals.subscription.toFixed(2)} RON</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
    });
    
    if (html) {
        totalsGrid.innerHTML = html;
        totalsSection.classList.remove('hidden');
    } else {
        totalsSection.classList.add('hidden');
    }
}

// Utility functions
function updateProviders() {
    const providerSet = new Set();
    appState.analysisTable.forEach(analysis => {
        Object.keys(analysis.prices || {}).forEach(provider => {
            providerSet.add(provider);
        });
    });
    
    if (providerSet.size === 0) {
        appState.providers = ['reginamaria', 'medlife'];
    } else {
        appState.providers = Array.from(providerSet);
    }
}

function getProviderTotal(provider) {
    const totals = {
        normal: 0,
        premium: 0,
        subscription: 0,
        hasData: false
    };
    
    appState.analysisTable.forEach(analysis => {
        const providerPrices = analysis.prices && analysis.prices[provider];
        if (providerPrices) {
            if (providerPrices.normal) {
                totals.normal += providerPrices.normal.amount;
                totals.hasData = true;
            }
            if (providerPrices.premium) {
                totals.premium += providerPrices.premium.amount;
                totals.hasData = true;
            }
            if (providerPrices.subscription) {
                totals.subscription += providerPrices.subscription.amount;
                totals.hasData = true;
            }
        }
    });
    
    return totals;
}

async function handlePendingSearch(pendingId, query) {
    if (query.length < 2) return;
    
    try {
        const response = await fetch(`${appState.apiBaseUrl}/analyses/suggestions?query=${encodeURIComponent(query)}&limit=5`);
        const data = await response.json();
        // Implementation for pending search suggestions can be added here
    } catch (error) {
        console.error('Error fetching pending suggestions:', error);
    }
}

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

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Medical Price Comparator initialized');
    
    // Set up drag and drop for file upload
    const uploadArea = document.getElementById('uploadArea');
    
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                appState.selectedFile = file;
                appState.selectedFileName = file.name;
                document.getElementById('imageFile').files = files;
                updateFileDisplay();
                updateProcessButton();
            } else {
                showNotification('Please select an image file', 'error');
            }
        }
    });
    
    // Set up click outside to hide suggestions
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#searchInput') && !e.target.closest('#searchSuggestions')) {
            hideSuggestions();
        }
    });
    
    // Initialize UI state
    updateFileDisplay();
    updateProcessButton();
    updateAnalysisTable();
});