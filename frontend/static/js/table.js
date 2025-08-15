// Table Module - Handles comparison table functionality

let tableState = {
  analyses: [],
  providers: ['reginamaria', 'medlife'],
  totals: {}
};

const API_BASE_URL = '/api/v1';

// Initialize table functionality
function initializeTable() {
  updateTableDisplay();
  
  // Make functions globally available
  window.addAnalysisToComparisonTable = addAnalysisToComparisonTable;
  window.removeAnalysisFromTable = removeAnalysisFromTable;
  window.tableState = tableState;
}

// Add analysis to comparison table
async function addAnalysisToComparisonTable(analysisName) {
  // Check if already exists
  if (tableState.analyses.some(a => a.name.toLowerCase() === analysisName.toLowerCase())) {
    showToast('Analysis is already in the table', 'warning');
    return;
  }
  
  try {
    // Fetch price data
    const response = await fetch(`${API_BASE_URL}/analysis/${encodeURIComponent(analysisName)}/prices`);
    
    let priceData = {};
    if (response.ok) {
      priceData = await response.json();
    }
    
    // Add to table state
    const analysis = {
      name: analysisName,
      prices: {
        reginamaria: priceData.reginamaria || null,
        medlife: priceData.medlife || null
      }
    };
    
    tableState.analyses.push(analysis);
    updateTableDisplay();
    calculateTotals();
    
  } catch (error) {
    console.error('Error adding analysis to table:', error);
    
    // Add with no price data if API fails
    const analysis = {
      name: analysisName,
      prices: {
        reginamaria: null,
        medlife: null
      }
    };
    
    tableState.analyses.push(analysis);
    updateTableDisplay();
    calculateTotals();
  }
}

// Remove analysis from table
function removeAnalysisFromTable(index) {
  if (index >= 0 && index < tableState.analyses.length) {
    const analysisName = tableState.analyses[index].name;
    tableState.analyses.splice(index, 1);
    updateTableDisplay();
    calculateTotals();
    showToast(`Removed "${analysisName}" from table`, 'info');
  }
}

// Update table display
function updateTableDisplay() {
  const tableWrapper = document.getElementById('tableWrapper');
  const emptyState = document.getElementById('emptyState');
  const tableBody = document.getElementById('tableBody');
  
  if (tableState.analyses.length === 0) {
    hideElement('tableWrapper');
    showElement('emptyState');
    hideElement('totalsSection');
    return;
  }
  
  hideElement('emptyState');
  showElement('tableWrapper');
  
  // Clear table body
  clearContainer('tableBody');
  
  // Add rows
  tableState.analyses.forEach((analysis, index) => {
    const row = createAnalysisRow(analysis, index);
    tableBody.appendChild(row);
  });
}

// Create analysis table row
function createAnalysisRow(analysis, index) {
  const row = document.createElement('tr');
  
  const reginamariaPrice = analysis.prices.reginamaria;
  const medlifePrice = analysis.prices.medlife;
  
  row.innerHTML = `
    <td>
      <strong>${analysis.name}</strong>
    </td>
    <td>
      ${reginamariaPrice ? `${reginamariaPrice} RON` : '<span style="color: var(--gray-400)">N/A</span>'}
    </td>
    <td>
      ${medlifePrice ? `${medlifePrice} RON` : '<span style="color: var(--gray-400)">N/A</span>'}
    </td>
    <td>
      <button type="button" 
              class="button button-danger" 
              onclick="removeAnalysisFromTable(${index})"
              title="Remove analysis">
        🗑️ Remove
      </button>
    </td>
  `;
  
  return row;
}

// Calculate totals
function calculateTotals() {
  if (tableState.analyses.length === 0) {
    hideElement('totalsSection');
    return;
  }
  
  const totals = {
    reginamaria: 0,
    medlife: 0,
    reginamariaCount: 0,
    medlifeCount: 0
  };
  
  tableState.analyses.forEach(analysis => {
    if (analysis.prices.reginamaria) {
      totals.reginamaria += parseFloat(analysis.prices.reginamaria);
      totals.reginamariaCount++;
    }
    if (analysis.prices.medlife) {
      totals.medlife += parseFloat(analysis.prices.medlife);
      totals.medlifeCount++;
    }
  });
  
  tableState.totals = totals;
  displayTotals();
}

// Display totals
function displayTotals() {
  const totalsGrid = document.getElementById('totalsGrid');
  const totals = tableState.totals;
  
  if (!totalsGrid) return;
  
  clearContainer('totalsGrid');
  
  // Reginamaria total
  if (totals.reginamariaCount > 0) {
    const reginamariaTotal = createTotalItem(
      `Reginamaria (${totals.reginamariaCount} items)`,
      totals.reginamaria.toFixed(2)
    );
    totalsGrid.appendChild(reginamariaTotal);
  }
  
  // Medlife total
  if (totals.medlifeCount > 0) {
    const medlifeTotal = createTotalItem(
      `Medlife (${totals.medlifeCount} items)`,
      totals.medlife.toFixed(2)
    );
    totalsGrid.appendChild(medlifeTotal);
  }
  
  // Savings comparison
  if (totals.reginamariaCount > 0 && totals.medlifeCount > 0) {
    const difference = Math.abs(totals.reginamaria - totals.medlife);
    const cheaper = totals.reginamaria < totals.medlife ? 'Reginamaria' : 'Medlife';
    
    if (difference > 0) {
      const savingsItem = createTotalItem(
        `💰 Savings with ${cheaper}`,
        difference.toFixed(2)
      );
      savingsItem.style.background = 'var(--success)';
      savingsItem.style.color = 'white';
      totalsGrid.appendChild(savingsItem);
    }
  }
  
  showElement('totalsSection');
}

// Clear all analyses
function clearTable() {
  tableState.analyses = [];
  tableState.totals = {};
  updateTableDisplay();
  showToast('Table cleared', 'info');
}

// Export table data
function exportTableData() {
  if (tableState.analyses.length === 0) {
    showToast('No data to export', 'warning');
    return;
  }
  
  const csvContent = generateCSV();
  downloadCSV(csvContent, 'medical_analysis_comparison.csv');
  showToast('Table data exported', 'success');
}

// Generate CSV content
function generateCSV() {
  const headers = ['Analysis', 'Reginamaria (RON)', 'Medlife (RON)'];
  const rows = [headers];
  
  tableState.analyses.forEach(analysis => {
    const row = [
      analysis.name,
      analysis.prices.reginamaria || 'N/A',
      analysis.prices.medlife || 'N/A'
    ];
    rows.push(row);
  });
  
  // Add totals row
  if (Object.keys(tableState.totals).length > 0) {
    rows.push(['']); // Empty row
    rows.push([
      'TOTAL',
      tableState.totals.reginamaria ? tableState.totals.reginamaria.toFixed(2) : 'N/A',
      tableState.totals.medlife ? tableState.totals.medlife.toFixed(2) : 'N/A'
    ]);
  }
  
  return rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
}

// Download CSV file
function downloadCSV(content, filename) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

// Bulk add analyses (for OCR results)
function addMultipleAnalyses(analysisList) {
  analysisList.forEach(analysis => {
    addAnalysisToComparisonTable(analysis);
  });
}

// Get table state (for external use)
function getTableState() {
  return { ...tableState };
}

// Set table state (for external use)
function setTableState(newState) {
  tableState = { ...newState };
  updateTableDisplay();
  calculateTotals();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { 
    initializeTable,
    addAnalysisToComparisonTable,
    removeAnalysisFromTable,
    clearTable,
    exportTableData,
    addMultipleAnalyses,
    getTableState,
    setTableState,
    tableState
  };
}