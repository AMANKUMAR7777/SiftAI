// SiftAI Frontend Controller
// Simplified 1-Click Action Flow & Realtime Streaming Categorization
// Strictly zero emojis, zero hyphens, zero gradients

let state = {
  currentDirectory: '',
  files: [],
  models: [],
  activeModel: 'qwen2.5:3b',
  isProcessing: false,
  isCategorized: false
};

// DOM Elements
const activeFolderLabel = document.getElementById('activeFolderLabel');
const btnBrowseFolder = document.getElementById('btnBrowseFolder');
const modelSelect = document.getElementById('modelSelect');
const filterInput = document.getElementById('filterInput');
const btnMainAction = document.getElementById('btnMainAction');
const mainActionBtnText = document.getElementById('mainActionBtnText');

const filesTable = document.getElementById('filesTable');
const filesTableBody = document.getElementById('filesTableBody');
const emptyStateBox = document.getElementById('emptyStateBox');
const selectAllCheckbox = document.getElementById('selectAllCheckbox');

const statTotalFiles = document.getElementById('statTotalFiles');
const statCategorized = document.getElementById('statCategorized');
const statTotalSize = document.getElementById('statTotalSize');
const statProtection = document.getElementById('statProtection');

const progressCard = document.getElementById('progressCard');
const progressBarFill = document.getElementById('progressBarFill');
const progressStatusLabel = document.getElementById('progressStatusLabel');
const progressPercent = document.getElementById('progressPercent');

const treePreviewContainer = document.getElementById('treePreviewContainer');
const historyListContainer = document.getElementById('historyListContainer');
const btnRefreshHistory = document.getElementById('btnRefreshHistory');

const sidebarOllamaStatus = document.getElementById('sidebarOllamaStatus');
const ollamaStatusText = document.getElementById('ollamaStatusText');
const sidebarActiveModel = document.getElementById('sidebarActiveModel');
const settingsModelList = document.getElementById('settingsModelList');

// Toast notifications (no emojis, no hyphens)
function showToast(message, type = 'normal') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Format model display name without hyphens
function cleanModelDisplayName(name) {
  return name.replace(/-/g, ' ').replace(/:/g, ' ');
}

const quickFolderSelect = document.getElementById('quickFolderSelect');
const includeSubfoldersCheck = document.getElementById('includeSubfoldersCheck');
const folderDisplayGroup = document.getElementById('folderDisplayGroup');

// Initialize system status and models
async function initSystem() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();

    state.currentDirectory = data.default_folder;
    activeFolderLabel.textContent = data.default_folder;
    activeFolderLabel.title = data.default_folder;
    state.quickFolders = data.quick_folders || {};

    const ollama = data.ollama || {};
    if (ollama.online) {
      sidebarOllamaStatus.classList.remove('offline');
      ollamaStatusText.textContent = 'Ollama Connected';
    } else {
      sidebarOllamaStatus.classList.add('offline');
      ollamaStatusText.textContent = 'Ollama Standby';
    }

    state.models = ollama.models || ['qwen2.5:3b'];
    // Default to qwen2.5:3b if available because it fits 100% in GPU
    if (state.models.includes('qwen2.5:3b')) {
      state.activeModel = 'qwen2.5:3b';
    } else {
      state.activeModel = ollama.default_model || state.models[0] || 'qwen2.5:3b';
    }

    populateModelDropdown();
    updateModelBadge();

    // Automatically scan the initial directory
    await scanCurrentDirectory();
  } catch (err) {
    console.error('System init error:', err);
    showToast('Failed to connect to backend server', 'error');
  }
}

function populateModelDropdown() {
  modelSelect.innerHTML = '';
  settingsModelList.innerHTML = '';

  state.models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    const isQwen = m.includes('qwen');
    opt.textContent = `${cleanModelDisplayName(m)} ${isQwen ? '(Recommended)' : ''}`;
    if (m === state.activeModel) opt.selected = true;
    modelSelect.appendChild(opt);

    const badge = document.createElement('div');
    badge.className = 'model-name-badge';
    badge.textContent = `${cleanModelDisplayName(m)} (Available)`;
    settingsModelList.appendChild(badge);
  });
}

function updateModelBadge() {
  sidebarActiveModel.textContent = `Model: ${cleanModelDisplayName(state.activeModel)}`;
}

modelSelect.addEventListener('change', (e) => {
  state.activeModel = e.target.value;
  updateModelBadge();
  resetActionState();
});

// Tab Navigation
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const tab = btn.getAttribute('data-tab');
    document.querySelectorAll('.tab-view').forEach(view => view.style.display = 'none');

    if (tab === 'workspace') {
      document.getElementById('viewWorkspace').style.display = 'block';
    } else if (tab === 'tree') {
      document.getElementById('viewTree').style.display = 'block';
      renderFolderTree();
    } else if (tab === 'history') {
      document.getElementById('viewHistory').style.display = 'block';
      loadHistory();
    } else if (tab === 'settings') {
      document.getElementById('viewSettings').style.display = 'block';
    }
  });
});

// Quick folder switcher dropdown
quickFolderSelect.addEventListener('change', async (e) => {
  const chosen = e.target.value;
  if (chosen === 'Custom') {
    await triggerFolderPicker();
  } else if (state.quickFolders && state.quickFolders[chosen]) {
    state.currentDirectory = state.quickFolders[chosen];
    activeFolderLabel.textContent = state.currentDirectory;
    activeFolderLabel.title = state.currentDirectory;
    await scanCurrentDirectory();
  }
});

// Recursive toggle
includeSubfoldersCheck.addEventListener('change', async () => {
  await scanCurrentDirectory();
});

// Trigger Windows folder picker
async function triggerFolderPicker() {
  try {
    const res = await fetch('/api/pick_folder', { method: 'POST' });
    const data = await res.json();
    if (data.success && data.directory) {
      state.currentDirectory = data.directory;
      activeFolderLabel.textContent = data.directory;
      activeFolderLabel.title = data.directory;
      quickFolderSelect.value = 'Custom';
      await scanCurrentDirectory();
    }
  } catch (err) {
    const manual = prompt('Enter any directory path to organize:', state.currentDirectory);
    if (manual && manual.trim()) {
      state.currentDirectory = manual.trim();
      activeFolderLabel.textContent = manual.trim();
      activeFolderLabel.title = manual.trim();
      quickFolderSelect.value = 'Custom';
      await scanCurrentDirectory();
    }
  }
}

btnBrowseFolder.addEventListener('click', triggerFolderPicker);

// Drag and drop support on folder bar
['dragenter', 'dragover'].forEach(eventName => {
  folderDisplayGroup.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    folderDisplayGroup.classList.add('drag-active');
  });
});

['dragleave', 'drop'].forEach(eventName => {
  folderDisplayGroup.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
    folderDisplayGroup.classList.remove('drag-active');
  });
});

folderDisplayGroup.addEventListener('drop', async (e) => {
  e.preventDefault();
  const items = e.dataTransfer.items;
  if (items && items.length > 0) {
    // Open picker or prompt to confirm path
    showToast('Folder dropped. Selecting directory...', 'normal');
    await triggerFolderPicker();
  }
});

// Scan directory
async function scanCurrentDirectory() {
  resetActionState();
  const includeSub = includeSubfoldersCheck ? includeSubfoldersCheck.checked : false;

  try {
    const res = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory: state.currentDirectory,
        include_subfolders: includeSub
      })
    });

    const result = await res.json();
    if (!result.success) {
      throw new Error(result.error || 'Failed to scan directory');
    }

    state.files = result.data.files || [];
    statTotalFiles.textContent = result.data.total_files.toString();
    statTotalSize.textContent = result.data.total_size_formatted;
    statCategorized.textContent = '0';

    renderFilesTable();
    updateSelectionState();

    if (state.files.length === 0) {
      btnMainAction.disabled = true;
    } else {
      btnMainAction.disabled = false;
    }
  } catch (err) {
    showToast(`Scan error: ${err.message}`, 'error');
  }
}

// Reset button to initial Organize state
function resetActionState() {
  state.isCategorized = false;
  state.isProcessing = false;
  btnMainAction.className = 'btn-primary btn-large-action';
  btnMainAction.disabled = state.files.length === 0;
  btnMainAction.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
    <span>Organize Files</span>
  `;
}

// Set button to Move state
function setReadyToMoveState() {
  state.isCategorized = true;
  state.isProcessing = false;
  btnMainAction.className = 'btn-accent-mint btn-large-action';
  btnMainAction.disabled = false;
  btnMainAction.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
    <span>Move Files Now</span>
  `;
}

// Single Unified Main Action Button Click
btnMainAction.addEventListener('click', async () => {
  if (state.isProcessing) return;

  if (!state.isCategorized) {
    // Step 1: Run AI Categorization with live batch streaming
    await runStreamingCategorization();
  } else {
    // Step 2: Move files safely
    await executeSafeMove();
  }
});

// Realtime Streaming Categorization (never stuck at 0%)
async function runStreamingCategorization() {
  const selectedFiles = state.files.filter(f => f.selected);
  if (selectedFiles.length === 0) {
    showToast('Please select at least one file', 'error');
    return;
  }

  state.isProcessing = true;
  btnMainAction.disabled = true;
  btnMainAction.innerHTML = `<span>Analyzing...</span>`;

  progressCard.style.display = 'block';
  progressBarFill.style.width = '5%';
  progressPercent.textContent = '5%';
  progressStatusLabel.textContent = `Starting local model ${cleanModelDisplayName(state.activeModel)}...`;

  try {
    const response = await fetch('/api/categorize_stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: selectedFiles,
        model: state.activeModel
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let totalProcessed = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop(); // keep remainder

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const update = JSON.parse(line.substring(6));
            totalProcessed = update.processed;
            const pct = update.percentage;

            progressBarFill.style.width = `${pct}%`;
            progressPercent.textContent = `${pct}%`;
            progressStatusLabel.textContent = `Categorized ${totalProcessed} of ${update.total} files...`;

            // Merge items into state immediately
            const batchMap = {};
            (update.items || []).forEach(item => {
              batchMap[item.name] = item;
            });

            state.files.forEach(f => {
              if (batchMap[f.name]) {
                f.suggested_folder = batchMap[f.name].suggested_folder;
                f.reason = batchMap[f.name].reason;
              }
            });

            statCategorized.textContent = totalProcessed.toString();
            renderFilesTable();
            renderFolderTree();
          } catch (e) {
            console.error('Error parsing SSE chunk:', e);
          }
        }
      }
    }

    progressBarFill.style.width = '100%';
    progressPercent.textContent = '100%';
    progressStatusLabel.textContent = `All ${totalProcessed} files categorized into detailed topics`;
    showToast(`Categorized ${totalProcessed} files. Review folders and click Move Files Now`, 'success');

    // Switch button to "Move Files Now"
    setReadyToMoveState();

    setTimeout(() => {
      progressCard.style.display = 'none';
    }, 2000);
  } catch (err) {
    showToast(`Categorization error: ${err.message}`, 'error');
    progressCard.style.display = 'none';
    resetActionState();
  } finally {
    state.isProcessing = false;
  }
}

// Execute safe move
async function executeSafeMove() {
  const selectedItems = state.files.filter(f => f.selected && f.suggested_folder);
  if (selectedItems.length === 0) {
    showToast('No categorized files to move', 'error');
    return;
  }

  btnMainAction.disabled = true;
  btnMainAction.innerHTML = `<span>Moving files safely...</span>`;

  try {
    const res = await fetch('/api/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        directory: state.currentDirectory,
        items: selectedItems
      })
    });

    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to move files');
    }

    const result = data.result || {};
    showToast(`Safely moved ${result.moved_count} files into detailed folders`, 'success');

    // Rescan folder
    await scanCurrentDirectory();
  } catch (err) {
    showToast(`Move error: ${err.message}`, 'error');
    setReadyToMoveState();
  }
}

// Render Files in Table
function renderFilesTable() {
  const query = filterInput.value.toLowerCase().trim();
  filesTableBody.innerHTML = '';

  const visibleFiles = state.files.filter(f => {
    if (!query) return true;
    return f.name.toLowerCase().includes(query) ||
           f.extension.toLowerCase().includes(query) ||
           (f.suggested_folder && f.suggested_folder.toLowerCase().includes(query)) ||
           (f.reason && f.reason.toLowerCase().includes(query));
  });

  if (visibleFiles.length === 0) {
    filesTable.style.display = 'none';
    emptyStateBox.style.display = 'block';
    return;
  }

  filesTable.style.display = 'table';
  emptyStateBox.style.display = 'none';

  visibleFiles.forEach(file => {
    const tr = document.createElement('tr');

    // Checkbox
    const tdCheck = document.createElement('td');
    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.className = 'custom-checkbox';
    chk.checked = !!file.selected;
    chk.addEventListener('change', () => {
      file.selected = chk.checked;
      updateSelectionState();
    });
    tdCheck.appendChild(chk);

    // File name and extension pill
    const tdName = document.createElement('td');
    tdName.innerHTML = `
      <div class="file-title-cell">
        <span class="file-type-pill">${file.extension}</span>
        <span class="file-name-text" title="${file.name}">${file.name}</span>
      </div>
    `;

    // Type and Size
    const tdSize = document.createElement('td');
    tdSize.innerHTML = `
      <div style="font-weight: 600; color: var(--text-navy);">${file.size_formatted}</div>
      <div style="font-size: 11px; color: var(--text-light); margin-top: 2px;">${file.modified}</div>
    `;

    // Context preview
    const tdPreview = document.createElement('td');
    tdPreview.innerHTML = `
      <span class="file-context-preview" title="${file.sample || 'Standard file'}">
        ${file.sample || 'File metadata'}
      </span>
    `;

    // Suggested folder (editable input)
    const tdFolder = document.createElement('td');
    const folderInput = document.createElement('input');
    folderInput.type = 'text';
    folderInput.className = 'category-input';
    folderInput.value = file.suggested_folder || '';
    folderInput.placeholder = 'Click Organize Files';
    folderInput.addEventListener('input', (e) => {
      file.suggested_folder = e.target.value.trim();
      renderFolderTree();
    });
    tdFolder.appendChild(folderInput);

    // Reason tag
    const tdReason = document.createElement('td');
    if (file.reason) {
      tdReason.innerHTML = `<span class="category-reason-pill">${file.reason}</span>`;
    } else {
      tdReason.innerHTML = `<span style="color: var(--text-light); font-size: 12px;">Waiting</span>`;
    }

    tr.appendChild(tdCheck);
    tr.appendChild(tdName);
    tr.appendChild(tdSize);
    tr.appendChild(tdPreview);
    tr.appendChild(tdFolder);
    tr.appendChild(tdReason);

    filesTableBody.appendChild(tr);
  });
}

filterInput.addEventListener('input', renderFilesTable);

// Selection handlers
selectAllCheckbox.addEventListener('change', () => {
  const isChecked = selectAllCheckbox.checked;
  state.files.forEach(f => f.selected = isChecked);
  renderFilesTable();
  updateSelectionState();
});

function updateSelectionState() {
  const selected = state.files.filter(f => f.selected);
  selectAllCheckbox.checked = selected.length === state.files.length && state.files.length > 0;
  btnMainAction.disabled = selected.length === 0;
}

// Render Folder Tree Preview
function renderFolderTree() {
  const groups = {};
  state.files.forEach(f => {
    const folder = f.suggested_folder || 'Unassigned Loose Files';
    if (!groups[folder]) {
      groups[folder] = [];
    }
    groups[folder].push(f);
  });

  const keys = Object.keys(groups);
  if (keys.length === 0) {
    treePreviewContainer.innerHTML = `
      <div class="empty-state-box">
        <p>No organized folders generated yet. Click Organize Files first.</p>
      </div>
    `;
    return;
  }

  treePreviewContainer.innerHTML = '';
  keys.forEach(folderName => {
    const fileList = groups[folderName];
    const groupCard = document.createElement('div');
    groupCard.className = 'tree-folder-group';

    groupCard.innerHTML = `
      <div class="tree-folder-header">
        <div class="tree-folder-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
          <span>${folderName}</span>
        </div>
        <span class="tree-file-count-badge">${fileList.length} files</span>
      </div>
      <div class="tree-folder-contents">
        ${fileList.map(item => `
          <div class="tree-file-row">
            <span style="font-weight: 500; color: var(--text-navy);">${item.name}</span>
            <span style="font-size: 11px; color: var(--text-light);">${item.size_formatted}</span>
          </div>
        `).join('')}
      </div>
    `;

    treePreviewContainer.appendChild(groupCard);
  });
}

// Load History and Ledger
btnRefreshHistory.addEventListener('click', loadHistory);

async function loadHistory() {
  historyListContainer.innerHTML = '<div style="padding: 20px; color: var(--text-light);">Loading audit ledger...</div>';

  try {
    const res = await fetch('/api/history');
    const data = await res.json();

    if (!data.success || !data.batches || data.batches.length === 0) {
      historyListContainer.innerHTML = `
        <div class="empty-state-box">
          <p>No organization batches recorded yet. Your moves will appear here with one click undo protection.</p>
        </div>
      `;
      return;
    }

    historyListContainer.innerHTML = '';
    data.batches.forEach(b => {
      const card = document.createElement('div');
      card.className = 'history-card-item';

      const isReverted = b.status === 'reverted';
      const badgeClass = isReverted ? 'history-badge reverted' : 'history-badge active';
      const badgeText = isReverted ? 'Restored / Reverted' : 'Active Batch';

      card.innerHTML = `
        <div class="history-info-col">
          <h4>Batch ${b.id}</h4>
          <p>Directory: ${b.source_directory}</p>
          <p>Organized on ${b.created_at} &bull; ${b.files_count} files moved</p>
          <span class="${badgeClass}">${badgeText}</span>
        </div>
        <div>
          ${!isReverted ? `
            <button class="btn-outline-rose btn-undo-action" data-batch="${b.id}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
              <span>Undo Batch Move</span>
            </button>
          ` : '<span style="font-size: 13px; color: var(--text-light); font-weight: 600;">Files Restored</span>'}
        </div>
      `;

      historyListContainer.appendChild(card);
    });

    document.querySelectorAll('.btn-undo-action').forEach(btn => {
      btn.addEventListener('click', async () => {
        const batchId = btn.getAttribute('data-batch');
        await executeUndo(batchId);
      });
    });
  } catch (err) {
    historyListContainer.innerHTML = `<div style="color: var(--accent-rose);">Failed to load history: ${err.message}</div>`;
  }
}

async function executeUndo(batchId) {
  if (!confirm(`Are you sure you want to undo Batch ${batchId}?\nAll files will be safely moved back to their original locations.`)) {
    return;
  }

  try {
    const res = await fetch('/api/undo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_id: batchId })
    });

    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Undo operation failed');
    }

    showToast(`Batch ${batchId} successfully undone. Restored ${data.restored_count} files.`, 'success');
    loadHistory();
    await scanCurrentDirectory();
  } catch (err) {
    showToast(`Undo error: ${err.message}`, 'error');
  }
}

// Start application
window.addEventListener('DOMContentLoaded', initSystem);
