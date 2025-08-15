// Medical Price Comparator - Main Application
// Simple, modular approach with reusable components

// Application state
const appState = {
  initialized: false,
  apiBaseUrl: '/api/v1'
};

// Initialize the application
function initializeApp() {
  if (appState.initialized) return;
  
  try {
    // Initialize all modules
    initializeComponents();
    initializeOCR();
    initializeSearch();
    initializeTable();
    
    // Set up global error handling
    setupErrorHandling();
    
    // Set up CSS style additions for selected suggestions
    setupSuggestionStyles();
    
    appState.initialized = true;
    console.log('Medical Price Comparator initialized successfully');
    
  } catch (error) {
    console.error('Failed to initialize application:', error);
    showToast('Application failed to initialize', 'error');
  }
}

// Initialize component-specific functionality
function initializeComponents() {
  // Add click outside handlers for dropdowns
  document.addEventListener('click', handleGlobalClick);
  
  // Add keyboard shortcuts
  document.addEventListener('keydown', handleGlobalKeydown);
}

// Global click handler
function handleGlobalClick(event) {
  // Close suggestions if clicking outside search containers
  if (!event.target.closest('.search-container')) {
    const suggestions = document.querySelectorAll('.suggestions');
    suggestions.forEach(suggestion => {
      hideElement(suggestion.id);
    });
  }
}

// Global keyboard shortcuts
function handleGlobalKeydown(event) {
  // ESC key closes all dropdowns
  if (event.key === 'Escape') {
    const suggestions = document.querySelectorAll('.suggestions');
    suggestions.forEach(suggestion => {
      hideElement(suggestion.id);
    });
  }
}

// Set up global error handling
function setupErrorHandling() {
  window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
  });
  
  window.addEventListener('error', event => {
    console.error('Global error:', event.error);
    showToast('An error occurred in the application', 'error');
  });
}

// Add CSS for selected suggestions
function setupSuggestionStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .suggestion-item.selected {
      background-color: var(--primary);
      color: white;
    }
    
    .suggestion-item.selected .suggestion-category {
      color: rgba(255, 255, 255, 0.8);
    }
    
    .unmatched-item {
      background: var(--gray-50);
      border: 1px solid var(--gray-200);
      border-radius: var(--radius);
      padding: 1rem;
      margin-bottom: 1rem;
    }
    
    .unmatched-content {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    
    .unmatched-text {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    
    .unmatched-actions {
      display: flex;
      gap: 1rem;
      align-items: flex-start;
    }
    
    .unmatched-actions .search-container {
      flex: 1;
    }
    
    .matched-item {
      background: var(--gray-50);
      border: 1px solid var(--gray-200);
      border-radius: var(--radius);
      padding: 1rem;
      margin-bottom: 0.5rem;
    }
    
    .matched-content {
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
    
    .analysis-name {
      font-weight: 500;
      color: var(--gray-800);
    }
    
    @media (max-width: 768px) {
      .unmatched-actions {
        flex-direction: column;
      }
      
      .unmatched-text {
        flex-direction: column;
        align-items: flex-start;
      }
    }
  `;
  document.head.appendChild(style);
}

// Utility functions for cross-module communication
function broadcastEvent(eventName, data) {
  const event = new CustomEvent(eventName, { detail: data });
  document.dispatchEvent(event);
}

function listenToEvent(eventName, callback) {
  document.addEventListener(eventName, callback);
}

// Application lifecycle
function onDocumentReady() {
  initializeApp();
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', onDocumentReady);
} else {
  onDocumentReady();
}

// Export for global access
window.appState = appState;
window.broadcastEvent = broadcastEvent;
window.listenToEvent = listenToEvent;