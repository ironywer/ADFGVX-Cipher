// ===== State =====
const API = '';
let encryptMode = 'manual'; // manual | auto
let encryptInput = 'text';  // text | file
let decryptMode = 'session'; // session | manual
let decryptInput = 'text';   // text | file

// ===== Toast =====
function toast(msg, type = 'info') {
  const c = document.getElementById('toastContainer');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ===== Tabs =====
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
  });
});

// ===== Loading helpers =====
function setLoading(btn, loading) {
  if (loading) { btn.classList.add('loading'); btn.disabled = true; }
  else { btn.classList.remove('loading'); btn.disabled = false; }
}

// ===== Session status =====
async function refreshSession() {
  try {
    const r = await fetch(API + '/api/session-state');
    const s = await r.json();
    const gDot = document.getElementById('gridDot');
    const kDot = document.getElementById('keywordsDot');
    const eDot = document.getElementById('encryptedDot');

    gDot.className = 'status-dot ' + (s.grid_available ? 'active' : 'inactive');
    document.getElementById('gridStatusText').textContent = s.grid_available ? 'Таблица: готова' : 'Таблица: нет';

    kDot.className = 'status-dot ' + (s.keywords_count > 0 ? 'active' : 'inactive');
    document.getElementById('keywordsStatusText').textContent = `Ключи: ${s.keywords_count}`;

    eDot.className = 'status-dot ' + (s.last_encrypted ? 'active' : 'inactive');
    document.getElementById('encryptedStatusText').textContent = s.last_encrypted ? 'Шифротекст: есть' : 'Шифротекст: нет';
  } catch (e) { console.error(e); }
}

// ===== Grid =====
async function generateGrid() {
  const btn = document.getElementById('btnGenerateGrid');
  setLoading(btn, true);
  try {
    const fd = new FormData();
    const alpha = document.getElementById('customAlphabet').value.trim();
    if (alpha) fd.append('custom_alphabet', alpha);
    const r = await fetch(API + '/api/encrypt-auto/generate-grid', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderGrid(d.grid);
    toast('Таблица сгенерирована', 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
  finally { setLoading(btn, false); }
}

function handleGridFileSelect(input) {
  document.getElementById('gridFileName').textContent = input.files[0]?.name || '';
}

async function loadGrid() {
  const btn = document.getElementById('btnLoadGrid');
  const file = document.getElementById('gridFileInput').files[0];
  if (!file) return toast('Выберите файл', 'error');
  setLoading(btn, true);
  try {
    const fd = new FormData();
    fd.append('grid_file', file);
    const r = await fetch(API + '/api/encrypt-auto/load-grid', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderGrid(d.grid);
    toast('Таблица загружена из файла', 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
  finally { setLoading(btn, false); }
}

function renderGrid(grid) {
  const letters = ['A', 'D', 'F', 'G', 'V', 'X'];
  // Build reverse: code -> char
  const rev = {};
  for (const [ch, code] of Object.entries(grid)) rev[code] = ch;

  let html = '<thead><tr><th></th>';
  letters.forEach(l => html += `<th>${l}</th>`);
  html += '</tr></thead><tbody>';

  letters.forEach(row => {
    html += `<tr><td class="header-cell">${row}</td>`;
    letters.forEach(col => {
      const code = row + col;
      html += `<td>${rev[code] || '—'}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody>';

  document.getElementById('gridTable').innerHTML = html;
  document.getElementById('gridDisplayCard').style.display = 'block';
}

async function downloadGrid() {
  try {
    const r = await fetch(API + '/api/encrypt-auto/download-grid');
    if (!r.ok) throw new Error('Нет таблицы');
    const blob = await r.blob();
    downloadBlob(blob, 'adfgvx_grid.json');
    toast('Таблица скачана', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

// ===== Keywords =====
async function addKeyword() {
  const input = document.getElementById('newKeyword');
  const kw = input.value.trim();
  if (!kw) return toast('Введите ключевое слово', 'error');
  try {
    const fd = new FormData();
    fd.append('keyword', kw);
    const r = await fetch(API + '/api/encrypt-auto/keywords/add', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderKeywords(d.keywords);
    input.value = '';
    toast(`Ключ "${kw.toUpperCase()}" добавлен`, 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
}

function handleKeywordsFileSelect(input) {
  document.getElementById('keywordsFileName').textContent = input.files[0]?.name || '';
}

async function uploadKeywords() {
  const file = document.getElementById('keywordsFileInput').files[0];
  if (!file) return toast('Выберите файл', 'error');
  try {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('merge', 'true');
    const r = await fetch(API + '/api/encrypt-auto/keywords/upload', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderKeywords(d.keywords);
    toast(`Добавлено ключей: ${d.added_count}`, 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
}

async function removeKeyword(kw) {
  try {
    const r = await fetch(API + `/api/encrypt-auto/keywords/${encodeURIComponent(kw)}`, { method: 'DELETE' });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderKeywords(d.keywords);
    toast(`Ключ "${kw}" удалён`, 'info');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
}

async function clearKeywords() {
  if (!confirm('Удалить все ключевые слова?')) return;
  try {
    const r = await fetch(API + '/api/encrypt-auto/keywords/clear', { method: 'DELETE' });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка');
    renderKeywords([]);
    toast('Все ключи удалены', 'info');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
}

async function downloadKeywords() {
  try {
    const r = await fetch(API + '/api/encrypt-auto/keywords/download');
    if (!r.ok) throw new Error('Нет ключей');
    const blob = await r.blob();
    downloadBlob(blob, 'adfgvx_keywords.json');
    toast('Ключи скачаны', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

function renderKeywords(keywords) {
  const el = document.getElementById('keywordsList');
  if (!keywords || !keywords.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-icon">🔑</div><p>Ключевых слов пока нет</p></div>';
    return;
  }
  el.innerHTML = keywords.map(kw =>
    `<span class="keyword-tag">${kw} <span class="badge badge-success">${kw.length}</span>
      <button class="remove-btn" onclick="removeKeyword('${kw}')">✕</button></span>`
  ).join('');
}

async function loadKeywords() {
  try {
    const r = await fetch(API + '/api/encrypt-auto/keywords');
    const d = await r.json();
    if (d.keywords) renderKeywords(d.keywords);
  } catch (e) { console.error(e); }
}

// ===== Encrypt toggles =====
function setEncryptMode(mode) {
  encryptMode = mode;
  document.getElementById('encModeManual').classList.toggle('active', mode === 'manual');
  document.getElementById('encModeAuto').classList.toggle('active', mode === 'auto');
  document.getElementById('encryptKeywordField').style.display = mode === 'manual' ? 'block' : 'none';
}

function setEncryptInput(type) {
  encryptInput = type;
  document.getElementById('encInputText').classList.toggle('active', type === 'text');
  document.getElementById('encInputFile').classList.toggle('active', type === 'file');
  document.getElementById('encryptTextInput').style.display = type === 'text' ? 'block' : 'none';
  document.getElementById('encryptFileInput').style.display = type === 'file' ? 'block' : 'none';
}

function handleEncryptFileSelect(input) {
  document.getElementById('encryptFileName').textContent = input.files[0]?.name || '';
}

// ===== Encrypt =====
async function encryptText() {
  const btn = document.getElementById('btnEncrypt');
  setLoading(btn, true);
  try {
    const fd = new FormData();
    if (encryptInput === 'text') {
      const text = document.getElementById('encryptPlaintext').value.trim();
      if (!text) throw new Error('Введите текст');
      fd.append('plaintext', text);
    } else {
      const file = document.getElementById('encryptFileField').files[0];
      if (!file) throw new Error('Выберите файл');
      fd.append('file', file);
    }

    let url;
    if (encryptMode === 'manual') {
      const kw = document.getElementById('encryptKeyword').value.trim();
      if (!kw) throw new Error('Введите ключевое слово');
      fd.append('keyword', kw);
      url = API + '/api/encrypt-auto/encrypt-with-keyword';
    } else {
      url = API + '/api/encrypt-auto/encrypt-auto-keyword';
    }

    const r = await fetch(url, { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка шифрования');

    document.getElementById('encryptedResult').textContent = d.encrypted_text;
    const s = d.stats;
    document.getElementById('encryptStats').innerHTML = `
      <div class="stat-item"><span class="stat-label">Исходная длина</span><span class="stat-value">${s.original_length}</span></div>
      <div class="stat-item"><span class="stat-label">Закодированная</span><span class="stat-value">${s.encoded_length}</span></div>
      <div class="stat-item"><span class="stat-label">Шифротекст</span><span class="stat-value">${s.encrypted_length}</span></div>
      <div class="stat-item"><span class="stat-label">Ключ</span><span class="stat-value">${d.keyword_used}</span></div>
    `;
    document.getElementById('encryptResultCard').style.display = 'block';
    toast('Текст зашифрован!', 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
  finally { setLoading(btn, false); }
}

async function downloadEncrypted() {
  try {
    const r = await fetch(API + '/api/encrypt-auto/download-encrypted-text');
    if (!r.ok) throw new Error('Нет шифротекста');
    const blob = await r.blob();
    downloadBlob(blob, 'encrypted_text.txt');
    toast('Шифротекст скачан', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

// ===== Decrypt toggles =====
function setDecryptMode(mode) {
  decryptMode = mode;
  document.getElementById('decModeSession').classList.toggle('active', mode === 'session');
  document.getElementById('decModeManual').classList.toggle('active', mode === 'manual');
  document.getElementById('decryptManualFields').style.display = mode === 'manual' ? 'block' : 'none';
}

function setDecryptInput(type) {
  decryptInput = type;
  document.getElementById('decInputText').classList.toggle('active', type === 'text');
  document.getElementById('decInputFile').classList.toggle('active', type === 'file');
  document.getElementById('decryptTextInput').style.display = type === 'text' ? 'block' : 'none';
  document.getElementById('decryptFileInput').style.display = type === 'file' ? 'block' : 'none';
}

function handleDecryptFileSelect(input) {
  document.getElementById('decryptCipherFileName').textContent = input.files[0]?.name || '';
}
function handleDecryptGridFileSelect(input) {
  document.getElementById('decryptGridFileName').textContent = input.files[0]?.name || '';
}

// ===== Decrypt =====
async function decryptText() {
  const btn = document.getElementById('btnDecrypt');
  setLoading(btn, true);
  try {
    const fd = new FormData();
    let url;

    if (decryptMode === 'session') {
      // Session mode
      if (decryptInput === 'text') {
        const text = document.getElementById('decryptCiphertext').value.trim();
        if (!text) throw new Error('Введите шифротекст');
        fd.append('ciphertext', text);
        url = API + '/api/decrypt-auto/decrypt-text-session';
      } else {
        const file = document.getElementById('decryptCipherFile').files[0];
        if (!file) throw new Error('Выберите файл');
        fd.append('cipher_file', file);
        url = API + '/api/decrypt-auto/decrypt-file-session';
      }
    } else {
      // Manual mode
      const kw = document.getElementById('decryptKeyword').value.trim();
      if (!kw) throw new Error('Введите ключевое слово');
      fd.append('keyword', kw);

      const gridFile = document.getElementById('decryptGridFile').files[0];
      if (!gridFile) throw new Error('Загрузите файл таблицы');
      fd.append('grid_file', gridFile);

      if (decryptInput === 'text') {
        const text = document.getElementById('decryptCiphertext').value.trim();
        if (!text) throw new Error('Введите шифротекст');
        fd.append('ciphertext', text);
        url = API + '/api/decrypt-auto/decrypt-text';
      } else {
        const file = document.getElementById('decryptCipherFile').files[0];
        if (!file) throw new Error('Выберите файл');
        fd.append('cipher_file', file);
        url = API + '/api/decrypt-auto/decrypt-file';
      }
    }

    const r = await fetch(url, { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Ошибка дешифрования');

    document.getElementById('decryptedResult').textContent = d.decrypted_text;
    const s = d.stats;
    document.getElementById('decryptStats').innerHTML = `
      <div class="stat-item"><span class="stat-label">Длина шифротекста</span><span class="stat-value">${s.cipher_length}</span></div>
      <div class="stat-item"><span class="stat-label">Расшифровано</span><span class="stat-value">${s.decrypted_length}</span></div>
      <div class="stat-item"><span class="stat-label">Ключ</span><span class="stat-value">${s.keyword_used}</span></div>
    `;
    document.getElementById('decryptResultCard').style.display = 'block';
    toast('Текст дешифрован!', 'success');
    refreshSession();
  } catch (e) { toast(e.message, 'error'); }
  finally { setLoading(btn, false); }
}

async function downloadDecrypted() {
  try {
    const r = await fetch(API + '/api/decrypt-auto/download-decrypted-text');
    if (!r.ok) throw new Error('Нет расшифрованного текста');
    const blob = await r.blob();
    downloadBlob(blob, 'decrypted_text.txt');
    toast('Расшифрованный текст скачан', 'success');
  } catch (e) { toast(e.message, 'error'); }
}

// ===== Helpers =====
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  a.remove(); URL.revokeObjectURL(url);
}

// ===== Drag & Drop for file upload areas =====
document.querySelectorAll('.file-upload-area').forEach(area => {
  area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('dragover'); });
  area.addEventListener('dragleave', () => area.classList.remove('dragover'));
  area.addEventListener('drop', e => {
    e.preventDefault(); area.classList.remove('dragover');
    const input = area.querySelector('input[type="file"]');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event('change'));
    }
  });
});

// ===== Init =====
async function init() {
  await refreshSession();
  await loadKeywords();
  // Try to load current grid display
  try {
    const r = await fetch(API + '/api/encrypt-auto/grid-status');
    const d = await r.json();
    if (d.exists && d.sample) {
      // Fetch full grid for display
      const gr = await fetch(API + '/api/encrypt-auto/download-grid');
      const gd = await gr.json();
      if (gd.grid) renderGrid(gd.grid);
    }
  } catch (e) { console.error(e); }
}

init();
