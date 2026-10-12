const domains = [
  ['overall','Overall'],['flores','FLORES · 36 languages'],['code','Python code'],['math','Math'],['chat','Chat'],['pdf','PDFs']
];
let data;
let activeDomain = 'flores';
let worstFirst = false;
let coverage;
let threshold = 2;
let nvidiaOnly = false;
const fmt = value => Number(value).toFixed(2);
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function renderDomains() {
  document.getElementById('domain-controls').innerHTML = domains.map(([key,label]) => `<button type="button" data-domain="${key}" class="${key===activeDomain?'active':''}">${label}</button>`).join('');
  document.querySelectorAll('[data-domain]').forEach(button => button.addEventListener('click', () => { activeDomain = button.dataset.domain; renderDomains(); renderAggregate(); }));
}
function renderAggregate() {
  const rows = [...data.aggregate].sort((a,b) => a[activeDomain]-b[activeDomain]);
  const max = Math.max(...rows.map(row => row[activeDomain]));
  document.getElementById('chart').innerHTML = rows.map(row => `<div class="barrow ${row.name.startsWith('OpenEuroLLM v2')?'featured':''}" title="${escapeHtml(row.coverage)}"><div class="label">${escapeHtml(row.name)}</div><div class="track"><div class="fill" style="width:${100*row[activeDomain]/max}%"></div></div><div class="value">${fmt(row[activeDomain])}</div></div>`).join('');
  document.querySelector('#aggregate-table tbody').innerHTML = rows.map(row => `<tr class="${row.name.startsWith('OpenEuroLLM v2')?'highlight-row':''}"><td>${escapeHtml(row.name)}</td><td>${row.vocab.toLocaleString('en-US')}</td>${['overall','flores','code','math','chat','pdf'].map(key=>`<td>${fmt(row[key])}</td>`).join('')}</tr>`).join('');
}
function renderLanguages() {
  const query = document.getElementById('language-search').value.trim().toLowerCase();
  let rows = data.languages.filter(row => row[0].includes(query) || row[1].toLowerCase().includes(query));
  rows = rows.sort((a,b) => worstFirst ? b[3]-a[3] : a[1].localeCompare(b[1]));
  document.querySelector('#language-table tbody').innerHTML = rows.map(([code,name,v1_256,v2_256,v1_128,v2_128]) => {
    const delta = v2_256-v1_256;
    return `<tr><td>${escapeHtml(name)} <small>(${escapeHtml(code)})</small></td><td>${fmt(v2_256)}</td><td>${fmt(v2_128)}</td><td>${fmt(v1_256)}</td><td class="${delta<=0?'delta-good':'delta-bad'}">${delta>0?'+':''}${fmt(delta)}</td></tr>`;
  }).join('');
}
function renderCoverage() {
  const suffix = threshold === 2 ? '2x' : '3x';
  const rows = coverage.tokenizers.filter(row => !nvidiaOnly || row.repo.startsWith('nvidia/')).sort((a,b) => b[`within_${suffix}_priority`] - a[`within_${suffix}_priority`] || b[`within_${suffix}_languages`] - a[`within_${suffix}_languages`]);
  const unavailable = '<tr class="unavailable"><td>Llama 3.1 8B</td><td>—</td><td>—</td><td>—</td><td>—</td><td>Original tokenizer gated</td></tr><tr class="unavailable"><td>EuroLLM 9B</td><td>—</td><td>—</td><td>—</td><td>—</td><td>Original tokenizer gated</td></tr>';
  document.querySelector('#coverage-table tbody').innerHTML = rows.map(row => `<tr class="${row.name === 'OpenEuroLLM v2 256k' ? 'highlight-row' : ''}"><td>${escapeHtml(row.name)}</td><td><strong>${row[`within_${suffix}_priority`]}</strong> / ${coverage.priority_languages}</td><td><strong>${row[`within_${suffix}_languages`]}</strong> / ${coverage.distinct_languages}</td><td>${fmt(row.mean_ratio)}×</td><td>${row.vocab_size.toLocaleString('en-US')}</td><td><a href="https://huggingface.co/${encodeURI(row.repo)}/tree/${encodeURIComponent(row.revision)}" target="_blank" rel="noopener noreferrer">Pinned revision ↗</a></td></tr>`).join('') + (nvidiaOnly ? '' : unavailable);
  document.querySelectorAll('[data-threshold]').forEach(button => { const active = Number(button.dataset.threshold) === threshold; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
  document.querySelectorAll('[data-coverage-filter]').forEach(button => { const active = (button.dataset.coverageFilter === 'nvidia') === nvidiaOnly; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
}
fetch('data.json').then(response => { if(!response.ok) throw new Error(response.status); return response.json(); }).then(json => { data=json; renderDomains();renderAggregate();renderLanguages();document.getElementById('language-search').addEventListener('input',renderLanguages);document.getElementById('sort-worst').addEventListener('click',()=>{worstFirst=!worstFirst;document.getElementById('sort-worst').textContent=worstFirst?'Show A–Z':'Show highest cost first';renderLanguages();}); }).catch(error => {document.getElementById('chart').textContent=`Could not load comparison data: ${error.message}`;});
fetch('coverage.json').then(response => { if (!response.ok) throw new Error(response.status); return response.json(); }).then(json => { coverage=json; renderCoverage(); document.querySelectorAll('[data-threshold]').forEach(button => button.addEventListener('click', () => { threshold=Number(button.dataset.threshold); renderCoverage(); })); document.querySelectorAll('[data-coverage-filter]').forEach(button => button.addEventListener('click', () => { nvidiaOnly=button.dataset.coverageFilter === 'nvidia'; renderCoverage(); })); }).catch(error => {document.querySelector('#coverage-table tbody').innerHTML = `<tr><td colspan="6">Could not load coverage data: ${escapeHtml(error.message)}</td></tr>`;});
