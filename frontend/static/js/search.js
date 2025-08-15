// Search Module - Handles analysis search and suggestions

let searchState = {
  query: '',
  suggestions: [],
  isVisible: false,
  selectedIndex: -1
};

const API_BASE_URL = '/api/v1';

// Initialize search functionality
function initializeSearch() {
  const searchInput = document.getElementById('searchInput');
  const suggestionsContainer = document.getElementById('suggestions');
  
  if (searchInput) {
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', handleSearchKeydown);
    searchInput.addEventListener('focus', handleSearchFocus);
  }
  
  // Hide suggestions when clicking outside
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-container')) {
      hideSuggestions();
    }
  });
  
  // Make functions globally available
  window.addToTable = addToTable;
}

function handleSearchInput(event) {
  const query = event.target.value.trim();
  searchState.query = query;
  searchState.selectedIndex = -1;
  
  if (query.length >= 2) {
    debounceSearch(query);
  } else {
    hideSuggestions();
  }
}

function handleSearchKeydown(event) {
  const suggestions = searchState.suggestions;
  
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault();
      searchState.selectedIndex = Math.min(searchState.selectedIndex + 1, suggestions.length - 1);
      updateSelectedSuggestion();
      break;
      
    case 'ArrowUp':
      event.preventDefault();
      searchState.selectedIndex = Math.max(searchState.selectedIndex - 1, -1);
      updateSelectedSuggestion();
      break;
      
    case 'Enter':
      event.preventDefault();
      if (searchState.selectedIndex >= 0 && suggestions[searchState.selectedIndex]) {
        selectSuggestion(suggestions[searchState.selectedIndex]);
      } else if (searchState.query) {
        addToTable();
      }
      break;
      
    case 'Escape':
      hideSuggestions();
      break;
  }
}

function handleSearchFocus() {
  if (searchState.query.length >= 2) {
    showSuggestions();
  }
}

// Debounced search to avoid too many API calls
let searchTimeout;
function debounceSearch(query) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    searchAnalyses(query);
  }, 200);
}

// Search for analyses
async function searchAnalyses(query) {
  try {
    const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`);
    
    if (!response.ok) {
      throw new Error('Search request failed');
    }
    
    const data = await response.json();
    searchState.suggestions = data.suggestions || [];
    displaySuggestions();
    
  } catch (error) {
    console.error('Search error:', error);
    searchState.suggestions = [];
    hideSuggestions();
  }
}

// Search suggestions for unmatched items (used by OCR module)
async function searchSuggestions(query, suggestionsContainer, onSelect) {
  try {
    const response = await fetch(`${API_BASE_URL}/suggestions?q=${encodeURIComponent(query)}`);
    
    if (!response.ok) {
      throw new Error('Suggestions request failed');
    }
    
    const data = await response.json();
    const suggestions = data.suggestions || [];
    
    displayTableSuggestions(suggestions, suggestionsContainer, onSelect);
    
  } catch (error) {
    console.error('Suggestions error:', error);
    hideElement(suggestionsContainer.id);
  }
}

function displaySuggestions() {
  const container = document.getElementById('suggestions');
  if (!container) return;
  
  clearContainer('suggestions');
  
  if (searchState.suggestions.length === 0) {
    hideSuggestions();
    return;
  }
  
  searchState.suggestions.forEach((suggestion, index) => {
    const item = createSuggestionItem(
      suggestion.name,
      suggestion.category || 'Medical Analysis',
      () => selectSuggestion(suggestion)
    );
    
    if (index === searchState.selectedIndex) {
      item.classList.add('selected');
    }
    
    container.appendChild(item);
  });
  
  showSuggestions();
}

function displayTableSuggestions(suggestions, container, onSelect) {
  container.innerHTML = '';
  
  if (suggestions.length === 0) {
    hideElement(container.id);
    return;
  }
  
  suggestions.forEach(suggestion => {
    const item = createSuggestionItem(
      suggestion.name,
      suggestion.category || 'Medical Analysis',
      () => {
        onSelect(suggestion.name);
        hideElement(container.id);
      }
    );
    
    container.appendChild(item);
  });
  
  showElement(container.id);
}

function updateSelectedSuggestion() {
  const container = document.getElementById('suggestions');
  if (!container) return;
  
  const items = container.querySelectorAll('.suggestion-item');
  items.forEach((item, index) => {
    if (index === searchState.selectedIndex) {
      item.classList.add('selected');
      item.scrollIntoView({ block: 'nearest' });
    } else {
      item.classList.remove('selected');
    }
  });
}

function selectSuggestion(suggestion) {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.value = suggestion.name;
    searchState.query = suggestion.name;
  }
  
  hideSuggestions();
  addToTable();
}

function showSuggestions() {
  showElement('suggestions');
  searchState.isVisible = true;
}

function hideSuggestions() {
  hideElement('suggestions');
  searchState.isVisible = false;
  searchState.selectedIndex = -1;
}

function addToTable() {
  const query = searchState.query.trim();
  
  if (!query) {
    showToast('Please enter an analysis name', 'warning');
    return;
  }
  
  // Check if already in table
  if (isAnalysisInTable(query)) {
    showToast('Analysis is already in the comparison table', 'warning');
    return;
  }
  
  // Add to table
  addAnalysisToTable(query);
  
  // Clear search
  clearSearch();
  
  showToast(`Added "${query}" to comparison table`, 'success');
}

function clearSearch() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.value = '';
  }
  
  searchState.query = '';
  searchState.suggestions = [];
  hideSuggestions();
}

// Check if analysis is already in table (defined in table.js)
function isAnalysisInTable(analysisName) {
  // This will be properly implemented when we create table.js
  return window.tableState && window.tableState.analyses.some(
    analysis => analysis.name.toLowerCase() === analysisName.toLowerCase()
  );
}

// Add analysis to table (defined in table.js)
function addAnalysisToTable(analysisName) {
  // This will be properly implemented when we create table.js
  if (window.addAnalysisToComparisonTable) {
    window.addAnalysisToComparisonTable(analysisName);
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { 
    initializeSearch, 
    searchSuggestions,
    searchState 
  };
}