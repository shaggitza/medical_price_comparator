// OCR Module - Handles file upload and OCR processing

let ocrState = {
  selectedFile: null,
  isProcessing: false,
  results: [],
  unmatchedItems: [],
  isCollapsed: true
};

// File handling
function initializeFileUpload() {
  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');
  
  // File input change handler
  fileInput.addEventListener('change', handleFileSelect);
  
  // Drag and drop handlers
  uploadZone.addEventListener('dragover', handleDragOver);
  uploadZone.addEventListener('dragleave', handleDragLeave);
  uploadZone.addEventListener('drop', handleFileDrop);
  uploadZone.addEventListener('click', () => fileInput.click());
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    setSelectedFile(file);
  }
}

function handleDragOver(event) {
  event.preventDefault();
  event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
  event.preventDefault();
  event.currentTarget.classList.remove('dragover');
}

function handleFileDrop(event) {
  event.preventDefault();
  event.currentTarget.classList.remove('dragover');
  
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    setSelectedFile(files[0]);
  }
}

function setSelectedFile(file) {
  if (!file.type.startsWith('image/')) {
    showToast('Please select an image file', 'error');
    return;
  }
  
  ocrState.selectedFile = file;
  updateFileDisplay();
  updateProcessButton();
}

function updateFileDisplay() {
  const fileInfo = document.getElementById('fileInfo');
  const fileName = document.getElementById('fileName');
  
  if (ocrState.selectedFile) {
    fileName.textContent = ocrState.selectedFile.name;
    showElement('fileInfo');
  } else {
    hideElement('fileInfo');
  }
}

function updateProcessButton() {
  const button = document.getElementById('processButton');
  if (button) {
    button.disabled = !ocrState.selectedFile || ocrState.isProcessing;
  }
}

function clearFile() {
  ocrState.selectedFile = null;
  document.getElementById('fileInput').value = '';
  updateFileDisplay();
  updateProcessButton();
  hideElement('ocrResults');
  clearOCRResults();
}

// OCR Processing
async function processOCR() {
  if (!ocrState.selectedFile) {
    showToast('Please select a file first', 'warning');
    return;
  }
  
  ocrState.isProcessing = true;
  setButtonLoading('processButton', true);
  
  try {
    const formData = new FormData();
    formData.append('file', ocrState.selectedFile);
    
    const response = await fetch('/api/v1/ocr/process', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('OCR processing failed');
    }
    
    const data = await response.json();
    handleOCRResults(data);
    showToast('OCR processing completed successfully', 'success');
    
  } catch (error) {
    console.error('OCR processing error:', error);
    showToast('OCR processing failed. Please try again.', 'error');
  } finally {
    ocrState.isProcessing = false;
    setButtonLoading('processButton', false);
    updateProcessButton();
  }
}

function handleOCRResults(data) {
  ocrState.results = data.matched_analyses || [];
  ocrState.unmatchedItems = data.unmatched_items || [];
  
  displayOCRResults();
}

function displayOCRResults() {
  showElement('ocrResults');
  updateOCRContent();
}

function updateOCRContent() {
  const unmatchedSection = document.getElementById('unmatchedSection');
  const matchedSection = document.getElementById('matchedSection');
  const unmatchedList = document.getElementById('unmatchedList');
  const matchedList = document.getElementById('matchedList');
  
  // Clear previous results
  clearContainer('unmatchedList');
  clearContainer('matchedList');
  
  // Show/hide unmatched section
  if (ocrState.unmatchedItems.length > 0) {
    showElement('unmatchedSection');
    
    ocrState.unmatchedItems.forEach((item, index) => {
      const unmatchedComponent = createUnmatchedItem(
        item,
        (selectedAnalysis) => resolveUnmatchedItem(index, selectedAnalysis),
        () => dismissUnmatchedItem(index)
      );
      unmatchedList.appendChild(unmatchedComponent);
    });
  } else {
    hideElement('unmatchedSection');
  }
  
  // Display matched results
  if (ocrState.results.length > 0) {
    ocrState.results.forEach(result => {
      const resultElement = document.createElement('div');
      resultElement.className = 'matched-item';
      resultElement.innerHTML = `
        <div class="matched-content">
          <span class="analysis-name">${result.analysis}</span>
          <span class="status-badge status-success">✅ Matched</span>
        </div>
      `;
      matchedList.appendChild(resultElement);
    });
  }
  
  // Update toggle state
  updateOCRToggle();
}

function resolveUnmatchedItem(index, selectedAnalysis) {
  // Remove from unmatched items
  ocrState.unmatchedItems.splice(index, 1);
  
  // Add to matched results
  ocrState.results.push({ analysis: selectedAnalysis });
  
  // Update display
  updateOCRContent();
  
  // Add to comparison table
  addAnalysisToTable(selectedAnalysis);
  
  showToast(`Added "${selectedAnalysis}" to comparison table`, 'success');
}

function dismissUnmatchedItem(index) {
  ocrState.unmatchedItems.splice(index, 1);
  updateOCRContent();
  showToast('Item dismissed', 'info');
}

function clearOCRResults() {
  ocrState.results = [];
  ocrState.unmatchedItems = [];
  clearContainer('unmatchedList');
  clearContainer('matchedList');
  hideElement('unmatchedSection');
}

// OCR Results Toggle
function toggleOCRResults() {
  const isExpanded = toggleElement('ocrResultsContent');
  updateOCRToggleButton(isExpanded);
}

function updateOCRToggleButton(isExpanded) {
  const toggleIcon = document.getElementById('ocrToggleIcon');
  const toggleText = document.getElementById('ocrToggleText');
  
  if (toggleIcon) {
    toggleIcon.textContent = isExpanded ? '🔼' : '🔽';
  }
  
  if (toggleText) {
    toggleText.textContent = isExpanded ? 'Collapse' : 'Expand';
  }
}

function updateOCRToggle() {
  const hasContent = ocrState.results.length > 0 || ocrState.unmatchedItems.length > 0;
  const toggle = document.getElementById('ocrToggle');
  
  if (toggle) {
    toggle.style.display = hasContent ? 'flex' : 'none';
  }
}

// Initialize OCR module
function initializeOCR() {
  initializeFileUpload();
  
  // Make functions globally available
  window.processOCR = processOCR;
  window.clearFile = clearFile;
  window.toggleOCRResults = toggleOCRResults;
}

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { initializeOCR, ocrState };
}