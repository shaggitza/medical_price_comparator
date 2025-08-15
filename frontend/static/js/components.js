// UI Components - Reusable component functions

// Toast notification component
function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <span>${message}</span>
    </div>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => {
      if (container.contains(toast)) {
        container.removeChild(toast);
      }
    }, 300);
  }, duration);
}

// Toggle element visibility
function toggleElement(elementId, showClass = 'show') {
  const element = document.getElementById(elementId);
  if (element) {
    element.classList.toggle(showClass);
    return element.classList.contains(showClass);
  }
  return false;
}

// Show/hide element
function showElement(elementId, showClass = 'show') {
  const element = document.getElementById(elementId);
  if (element) {
    element.classList.add(showClass);
  }
}

function hideElement(elementId, showClass = 'show') {
  const element = document.getElementById(elementId);
  if (element) {
    element.classList.remove(showClass);
  }
}

// Create button component
function createButton(text, onclick, className = 'button button-primary', icon = null) {
  const button = document.createElement('button');
  button.className = className;
  button.onclick = onclick;
  
  if (icon) {
    button.innerHTML = `${icon} ${text}`;
  } else {
    button.textContent = text;
  }
  
  return button;
}

// Create status badge component
function createStatusBadge(text, type = 'pending') {
  const badge = document.createElement('span');
  badge.className = `status-badge status-${type}`;
  badge.textContent = text;
  return badge;
}

// Loading spinner component
function createLoadingSpinner() {
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';
  return spinner;
}

// Create suggestion item component
function createSuggestionItem(analysis, category, onclick) {
  const item = document.createElement('div');
  item.className = 'suggestion-item';
  item.onclick = onclick;
  item.innerHTML = `
    <div>${analysis}</div>
    <div class="suggestion-category">${category}</div>
  `;
  return item;
}

// Create table row component
function createTableRow(analysis, reginamariaPrice, medlifePrice, onRemove) {
  const row = document.createElement('tr');
  row.innerHTML = `
    <td>${analysis}</td>
    <td>${reginamariaPrice ? `${reginamariaPrice} RON` : 'N/A'}</td>
    <td>${medlifePrice ? `${medlifePrice} RON` : 'N/A'}</td>
    <td>
      <button type="button" class="button button-danger" onclick="${onRemove}">
        🗑️ Remove
      </button>
    </td>
  `;
  return row;
}

// Create unmatched item component with search functionality
function createUnmatchedItem(text, onResolve, onDismiss) {
  const container = document.createElement('div');
  container.className = 'unmatched-item';
  
  const itemId = 'unmatched_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  
  container.innerHTML = `
    <div class="unmatched-content">
      <div class="unmatched-text">
        <strong>${text}</strong>
        <span class="status-badge status-pending">⏳ Pending</span>
      </div>
      <div class="unmatched-actions">
        <div class="search-container">
          <input type="text" 
                 class="search-input" 
                 id="${itemId}_input"
                 placeholder="Search for matching analysis..."
                 value="${text}">
          <div class="suggestions" id="${itemId}_suggestions"></div>
        </div>
        <button type="button" class="button button-danger" onclick="${onDismiss}">
          ❌ Dismiss
        </button>
      </div>
    </div>
  `;
  
  // Add event listeners for search functionality
  const input = container.querySelector(`#${itemId}_input`);
  const suggestionsContainer = container.querySelector(`#${itemId}_suggestions`);
  
  let debounceTimer;
  
  function handleSearch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const query = input.value.trim();
      if (query.length > 0) {
        searchSuggestions(query, suggestionsContainer, (selectedAnalysis) => {
          onResolve(selectedAnalysis);
          hideElement(suggestionsContainer.id);
        });
      } else {
        hideElement(suggestionsContainer.id);
      }
    }, 200);
  }
  
  input.addEventListener('input', handleSearch);
  input.addEventListener('focus', handleSearch);
  input.addEventListener('click', handleSearch);
  
  // Hide suggestions when clicking outside
  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) {
      hideElement(suggestionsContainer.id);
    }
  });
  
  return container;
}

// Create total item component
function createTotalItem(label, value) {
  const item = document.createElement('div');
  item.className = 'total-item';
  item.innerHTML = `
    <div class="total-label">${label}</div>
    <div class="total-value">${value} RON</div>
  `;
  return item;
}

// Clear container contents
function clearContainer(containerId) {
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = '';
  }
}

// Set button loading state
function setButtonLoading(buttonId, isLoading = true) {
  const button = document.getElementById(buttonId);
  if (!button) return;
  
  if (isLoading) {
    button.disabled = true;
    button.classList.add('opacity-50', 'cursor-not-allowed');
    const icon = button.querySelector('[id$="Icon"]');
    const text = button.querySelector('[id$="Text"]');
    if (icon) icon.innerHTML = '<div class="loading-spinner"></div>';
    if (text) text.textContent = 'Processing...';
  } else {
    button.disabled = false;
    button.classList.remove('opacity-50', 'cursor-not-allowed');
    const icon = button.querySelector('[id$="Icon"]');
    const text = button.querySelector('[id$="Text"]');
    if (icon) icon.textContent = '✨';
    if (text) text.textContent = 'Process with AI';
  }
}