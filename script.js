const $ = id => document.getElementById(id);
let hist = JSON.parse(localStorage.getItem('nexora_history') || '[]');
let interactionId = localStorage.getItem('nexora_interaction_id') || '';

function openPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === name));
  document.querySelectorAll('.workspace-nav button').forEach(b => b.classList.toggle('active', b.dataset.panel === name));
  const ws = $('workspace');
  if (ws) ws.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.body.classList.remove('nav-open');
  const nav = $('topnav'), menu = $('menuBtn');
  if (nav) nav.classList.remove('open');
  if (menu) menu.setAttribute('aria-expanded', 'false');
}

document.querySelectorAll('.workspace-nav button').forEach(b => b.addEventListener('click', () => openPanel(b.dataset.panel)));

const menuBtn = $('menuBtn');
if (menuBtn) menuBtn.addEventListener('click', () => {
  const nav = $('topnav');
  const open = nav.classList.toggle('open');
  menuBtn.setAttribute('aria-expanded', String(open));
});

function addMessage(role, text) {
  const d = document.createElement('div');
  d.className = 'msg';
  const badge = document.createElement('b');
  badge.textContent = role === 'ai' ? 'N' : 'Y';
  const span = document.createElement('span');
  const strong = document.createElement('strong');
  strong.textContent = role === 'ai' ? 'NEXORA' : 'YOU';
  span.append(strong, document.createElement('br'), document.createTextNode(text));
  d.append(badge, span);
  $('messages').appendChild(d);
  $('messages').scrollTop = $('messages').scrollHeight;
  return span;
}

async function sendMessage() {
  const input = $('chatInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMessage('user', text);
  hist.push({ role: 'user', text });
  localStorage.setItem('nexora_history', JSON.stringify(hist.slice(-50)));
  const target = addMessage('ai', 'NEXORA is processing...');
  try {
    const payload = { message: text, model: 'gemini-3.6-flash' };
    if (interactionId) payload.interaction_id = interactionId;
    const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    let data = {};
    try { data = await response.json(); } catch (_) {}
    if (!response.ok) throw new Error(data.detail || 'AI request failed.');
    interactionId = data.interaction_id || interactionId;
    if (interactionId) localStorage.setItem('nexora_interaction_id', interactionId);
    target.innerHTML = '<strong>NEXORA</strong><br>' + esc(data.reply || 'No response received.');
    hist.push({ role: 'assistant', text: data.reply || '' });
    localStorage.setItem('nexora_history', JSON.stringify(hist.slice(-50)));
  } catch (error) {
    target.innerHTML = '<strong>NEXORA</strong><br>' + esc('Connection error: ' + error.message);
  }
}

$('chatInput').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

function clearChat() {
  hist = [];
  interactionId = '';
  localStorage.removeItem('nexora_history');
  localStorage.removeItem('nexora_interaction_id');
  $('messages').innerHTML = '';
  addMessage('ai', 'Neural session reset. What would you like to create?');
}

async function searchWeb() {
  const q = $('searchInput').value.trim();
  if (!q) return;
  $('results').innerHTML = '<p class="loading">Searching the web...</p>';
  try {
    const r = await fetch('/api/search?q=' + encodeURIComponent(q));
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || 'Search failed.');
    $('results').innerHTML = (d.results || []).map(x => `<div class="result"><a target="_blank" rel="noopener" href="${escAttr(x.url)}">${esc(x.title || x.url)}</a><p>${esc(x.snippet || '')}</p></div>`).join('') || '<p>No results found.</p>';
  } catch (e) { $('results').textContent = e.message; }
}

function generateImage() {
  const p = $('imagePrompt').value.trim();
  if (!p) return;
  $('imageResult').innerHTML = '<p class="loading">Generating image...</p><div class="media"><img src="/api/image?prompt=' + encodeURIComponent(p) + '" alt="NEXORA generated image" onload="this.previousElementSibling.remove()" onerror="this.previousElementSibling.textContent=\'Image generation failed.\'" /></div>';
}

async function generateVideo() {
  const p = $('videoPrompt').value.trim();
  if (!p) return;
  $('videoResult').textContent = 'Submitting video job...';
  try {
    const r = await fetch('/api/video', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: p }) });
    const d = await r.json();
    $('videoResult').textContent = d.message || 'Video gateway response received.';
  } catch (_) { $('videoResult').textContent = 'Video provider is not configured yet.'; }
}

function runCode() { $('preview').srcdoc = $('codeInput').value; }
function quick(text) { openPanel('chat'); $('chatInput').value = text; sendMessage(); }
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' }[c])); }
function escAttr(s) { return esc(s); }
function startVoice() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { alert('Voice input is not supported by this browser.'); return; }
  const r = new Recognition();
  r.lang = 'en-US'; r.interimResults = false; r.maxAlternatives = 1;
  r.onresult = e => { $('chatInput').value = e.results[0][0].transcript; sendMessage(); };
  r.onerror = () => {};
  r.start();
}

runCode();
