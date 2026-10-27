/* LogicLab frontend. All Boolean results come from the Python API; this file only renders them.
   User-supplied text is only ever inserted with textContent / setAttribute (never innerHTML). */
(() => {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const $ = (id) => document.getElementById(id);
  const el = {
    form: $('expr-form'), input: $('expression'), clear: $('clear-btn'), message: $('message'),
    simBtn: $('sim-btn'), simLabel: $('sim-label'), tableWrap: $('table-wrap'), circuitWrap: $('circuit-wrap'),
    explainWrap: $('explain-wrap'), switches: $('switches'), output: $('output-display'),
    copy: $('copy-btn'), csv: $('csv-btn'), examples: $('examples-grid'), toasts: $('toasts'),
    status: $('status'), statusText: $('status-text'),
    statVars: $('stat-vars'), statOps: $('stat-ops'), statRows: $('stat-rows'), statOut: $('stat-out'),
  };
  const state = { data: null, inputs: {}, current: null, requestId: 0 };

  // ---------------------------------------------------------------- helpers
  function node(tag, props = {}, text) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) e.setAttribute(k, v);
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function svg(tag, attrs = {}, text) {
    const e = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function setStatus(online) {
    el.status.classList.toggle('offline', !online);
    el.statusText.textContent = online ? 'SYSTEM ONLINE' : 'SERVER OFFLINE';
  }
  function toast(text, kind) {
    const t = node('div', { class: 'toast ' + kind }, text);
    while (el.toasts.children.length >= 3) el.toasts.firstChild.remove();
    el.toasts.appendChild(t);
    setTimeout(() => t.classList.add('leaving'), 3200);
    setTimeout(() => t.remove(), 3550);
  }
  // Inline message is the accessible channel (screen readers); the toast is a visual extra.
  function showMessage(text, kind) {
    el.message.textContent = text;
    el.message.className = 'message' + (kind ? ' ' + kind : '');
    el.message.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    if (kind) toast(text, kind);
  }
  async function post(path, payload) {
    let res;
    try {
      res = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    } catch (e) {
      setStatus(false);
      throw new Error('Cannot reach the LogicLab server. Is it still running?');
    }
    setStatus(true);
    let body = null;
    try { body = await res.json(); } catch (e) { /* non-JSON response */ }
    return body;
  }
  const errorText = (body) => (body && body.error && body.error.message) || 'Unexpected response from the server.';
  const levelName = (v) => (v ? 'HIGH' : 'LOW');

  function emptyState(container, title, text) {
    const icon = svg('svg', { viewBox: '0 0 24 24', 'aria-hidden': 'true' });
    icon.appendChild(svg('rect', { x: 6, y: 6, width: 12, height: 12, rx: 2 }));
    icon.appendChild(svg('path', { d: 'M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4' }));
    const box = node('div', { class: 'empty' });
    box.append(icon, node('strong', {}, title), node('p', {}, text));
    container.replaceChildren(box);
  }

  // -------------------------------------------------------------- dashboard
  function updateStats() {
    const d = state.data;
    if (!d) {
      [el.statVars, el.statOps, el.statRows, el.statOut].forEach((s) => s.replaceChildren(node('span', { class: 'none' }, '—')));
      return;
    }
    el.statVars.replaceChildren(...(d.variables.length
      ? d.variables.map((v) => node('span', { class: 'tag' }, v))
      : [node('span', { class: 'none' }, 'none')]));
    el.statOps.replaceChildren(...(d.operators.length
      ? d.operators.map((o) => node('span', { class: 'tag' }, o))
      : [node('span', { class: 'none' }, 'none')]));
    el.statRows.textContent = String(d.combinations);
    const out = state.current.output;
    el.statOut.replaceChildren(node('span', { class: out ? 'hi' : 'lo' }, `${out} ${levelName(out)}`));
  }

  // ------------------------------------------------------------ truth table
  function renderTable() {
    const { variables, rows } = state.data.truth_table;
    const table = node('table', { class: 'truth' });
    table.appendChild(node('caption', {}, `Truth table for ${state.data.normalized} (${rows.length} rows)`));
    const head = node('tr');
    [...variables, 'Output'].forEach((h) => head.appendChild(node('th', { scope: 'col' }, h)));
    table.appendChild(node('thead')).appendChild(head);
    const body = node('tbody');
    rows.forEach((r, i) => {
      const tr = node('tr', { 'data-index': i });
      r.inputs.forEach((v) => tr.appendChild(node('td', {}, v)));
      tr.appendChild(node('td', { class: 'out-' + r.output }, r.output));
      body.appendChild(tr);
    });
    table.appendChild(body);
    el.tableWrap.replaceChildren(table);
    el.copy.disabled = false;
    el.csv.disabled = false;
  }
  function highlightRow() {
    let activeRow = null;
    el.tableWrap.querySelectorAll('tbody tr').forEach((tr) => {
      const active = Number(tr.getAttribute('data-index')) === state.current.row_index;
      tr.classList.toggle('active', active);
      if (active) { tr.setAttribute('aria-current', 'true'); activeRow = tr; } else tr.removeAttribute('aria-current');
    });
    // keep the active row visible inside the scrollable table (no page scroll)
    const box = el.tableWrap;
    if (activeRow && box.scrollHeight > box.clientHeight) {
      const top = activeRow.offsetTop, bottom = top + activeRow.offsetHeight;
      if (top < box.scrollTop + 40) box.scrollTop = Math.max(0, top - 40);
      else if (bottom > box.scrollTop + box.clientHeight) box.scrollTop = bottom - box.clientHeight;
    }
  }
  function tableAsRows() {
    const { variables, rows } = state.data.truth_table;
    return [[...variables, 'Output'], ...rows.map((r) => [...r.inputs, r.output])];
  }
  async function copyTable() {
    const text = tableAsRows().map((r) => r.join('\t')).join('\n');
    try {
      await navigator.clipboard.writeText(text);
    } catch (e) {
      const ta = node('textarea', { 'aria-hidden': 'true' });
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
      ta.remove();
      if (!ok) { showMessage('Copy failed. Use Download CSV instead.', 'error'); return; }
    }
    showMessage('Truth table copied to the clipboard.', 'success');
  }
  function downloadCsv() {
    const csv = tableAsRows().map((r) => r.join(',')).join('\r\n') + '\r\n';
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const a = node('a', { href: url, download: 'logiclab-truth-table.csv' });
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showMessage('CSV downloaded.', 'success');
  }

  // ---------------------------------------------------------------- circuit
  const GATE_PATH = {
    AND: 'M0,-25 H30 C48,-25 60,-13 60,0 C60,13 48,25 30,25 H0 Z',
    OR: 'M0,-25 C25,-25 48,-14 60,0 C48,14 25,25 0,25 C12,12 12,-12 0,-25 Z',
    XOR: 'M0,-25 C25,-25 48,-14 60,0 C48,14 25,25 0,25 C12,12 12,-12 0,-25 Z',
    NOT: 'M0,-18 L38,0 L0,18 Z',
  };
  const STEP_MS = 140; // reveal delay per circuit level

  // `reveal` = play the level-by-level entrance (only right after Simulate, not on every toggle)
  function renderCircuit(reveal) {
    const c = state.data.circuit;
    if (!c) {
      emptyState(el.circuitWrap, 'Circuit unavailable',
        state.data.circuit_error || 'This expression has no circuit diagram. The truth table is still valid.');
      return;
    }
    const vals = state.current.node_values || {};
    const byId = Object.fromEntries(c.nodes.map((n) => [n.id, n]));
    const root = svg('svg', {
      class: 'circuit' + (reveal ? ' reveal' : ''), width: c.width, height: c.height, viewBox: `0 0 ${c.width} ${c.height}`, role: 'img',
      'aria-label': `Logic circuit for ${state.data.normalized}. Output is ${state.current.output}.`,
    });
    c.edges.forEach((e) => {
      const delay = `${byId[e.from].level * STEP_MS + 60}ms`;
      const wire = svg('path', { d: e.path, class: 'wire wire-' + vals[e.from] });
      wire.style.setProperty('--d', delay);
      root.appendChild(wire);
      if (vals[e.from]) { // moving dashes show HIGH signal travelling source -> destination
        const flow = svg('path', { d: e.path, class: 'wire wire-flow' });
        flow.style.setProperty('--d', delay);
        root.appendChild(flow);
      }
    });
    c.nodes.forEach((n) => {
      const v = vals[n.id];
      const kind = n.type.toLowerCase();
      const g = svg('g', { transform: `translate(${n.x},${n.y})`, class: `node node-${kind}` + (v ? ' hi' : '') });
      g.style.setProperty('--d', `${n.level * STEP_MS}ms`);
      if (n.type === 'INPUT' || n.type === 'CONST' || n.type === 'OUTPUT') {
        g.appendChild(svg('rect', { class: 'box ' + (v ? 'box-hi' : 'box-lo'), x: 0, y: -14, width: n.w, height: 28, rx: 6 }));
        g.appendChild(svg('text', { class: 'svg-text', x: n.w / 2, y: 0 }, n.label));
      } else {
        g.appendChild(svg('path', { class: 'gate-body', d: GATE_PATH[n.type] }));
        if (n.type === 'XOR') g.appendChild(svg('path', { class: 'gate-extra', d: 'M-7,-25 C5,-12 5,12 -7,25' }));
        if (n.type === 'NOT') g.appendChild(svg('circle', { class: 'gate-body', cx: 42, cy: 0, r: 4 }));
        g.appendChild(svg('text', { class: 'svg-small', x: n.w / 2, y: 42 }, n.type));
      }
      const cls = 'sig' + (v ? '' : ' sig-0');
      g.appendChild(n.type === 'OUTPUT'
        ? svg('text', { class: cls, x: n.w + 8, y: 5 }, `= ${v}`)
        : svg('text', { class: cls, x: n.w + 6, y: -8 }, String(v)));
      root.appendChild(g);
    });
    el.circuitWrap.replaceChildren(root);
  }

  // --------------------------------------------------------- input testing
  function buildSwitches() {
    const names = state.data.variables;
    if (!names.length) {
      el.switches.replaceChildren(node('p', { class: 'placeholder' }, 'This expression has no variables, so there is nothing to toggle.'));
      return;
    }
    el.switches.replaceChildren(...names.map((name) => {
      const b = node('button', { type: 'button', class: 'switch', role: 'switch', 'data-var': name, 'aria-label': `Input ${name}` });
      b.appendChild(node('span', { class: 'track', 'aria-hidden': 'true' }));
      b.appendChild(node('span', { class: 'switch-text' }));
      b.addEventListener('click', () => toggleInput(name));
      return b;
    }));
  }
  function renderCurrent(reveal) {
    const { inputs, output, row_index: idx } = state.current;
    el.switches.querySelectorAll('.switch').forEach((b) => {
      const name = b.getAttribute('data-var');
      b.setAttribute('aria-checked', inputs[name] ? 'true' : 'false');
      b.querySelector('.switch-text').textContent = `${name} = ${inputs[name]}`;
    });
    el.output.replaceChildren(
      node('span', {}, 'Output ='),
      node('span', { class: 'big' + (output ? ' hi' : '') }, String(output)),
      node('span', { class: 'state' }, levelName(output)),
      node('span', { class: 'row-note' }, `Truth table row ${idx + 1} of ${state.data.combinations} is highlighted.`));
    highlightRow();
    renderCircuit(reveal);
    updateStats();
    updateNow();
  }
  async function toggleInput(name) {
    if (!state.data) return;
    const next = { ...state.inputs, [name]: state.inputs[name] ? 0 : 1 };
    const id = ++state.requestId;
    let body;
    try {
      body = await post('/api/evaluate', { expression: state.data.expression, inputs: next });
    } catch (e) { showMessage(e.message, 'error'); return; }
    if (id !== state.requestId) return; // a newer toggle superseded this one
    if (!body || !body.ok) { showMessage(errorText(body), 'error'); return; }
    state.inputs = next;
    state.current = body.current;
    renderCurrent(false);
  }

  // ------------------------------------------------------------ explanation
  function renderExplain() {
    const d = state.data;
    const structure = node('section', { class: 'card mini rise r1' });
    structure.append(node('h3', {}, 'How it works'), node('p', {}, d.explanation.summary));
    const canon = node('p');
    canon.append('Fully parenthesised: ', node('code', {}, d.normalized));
    structure.appendChild(canon);

    const cards = [structure];
    if (d.explanation.steps.length) {
      const steps = node('section', { class: 'card mini rise r2' });
      steps.appendChild(node('h3', {}, 'Gate by gate (inner gates first)'));
      const ol = node('ol');
      d.explanation.steps.forEach((s) => {
        const li = node('li');
        li.append(node('code', {}, s.expression), ' — ' + s.meaning);
        ol.appendChild(li);
      });
      steps.appendChild(ol);
      cards.push(steps);
    }
    const now = node('section', { class: 'card mini rise r3' });
    now.append(node('h3', {}, 'Right now'), node('p', { class: 'now', id: 'explain-current' }));
    cards.push(now);
    el.explainWrap.replaceChildren(...cards);
  }
  function updateNow() {
    const cur = $('explain-current');
    if (!cur) return;
    const names = state.data.variables;
    const given = names.length ? names.map((n) => `${n}=${state.current.inputs[n]}`).join(', ') : 'no inputs';
    cur.textContent = `${given} → output ${state.current.output} (${levelName(state.current.output)})`;
  }

  // ------------------------------------------------------------- main flow
  function clearResults(reason) {
    state.data = null; state.current = null; state.inputs = {};
    emptyState(el.circuitWrap, 'No circuit yet', reason || 'Enter an expression and press SIMULATE CIRCUIT.');
    const tableMsg = node('p', { class: 'hint' }, 'The truth table appears here after a successful simulation.');
    el.tableWrap.replaceChildren(tableMsg);
    const idle = node('section', { class: 'card mini' });
    idle.append(node('h3', {}, 'How it works'), node('p', {}, 'Run a simulation to see a plain-English explanation of your expression, gate by gate.'));
    el.explainWrap.replaceChildren(idle);
    el.switches.replaceChildren();
    el.output.replaceChildren();
    el.copy.disabled = true;
    el.csv.disabled = true;
    updateStats();
  }
  function setBusy(busy) {
    el.simBtn.disabled = busy;
    el.simBtn.classList.toggle('is-loading', busy);
    el.simLabel.textContent = busy ? 'SIMULATING…' : 'SIMULATE CIRCUIT';
    el.circuitWrap.setAttribute('aria-busy', busy ? 'true' : 'false');
  }
  async function simulate() {
    let body;
    setBusy(true);
    try {
      body = await post('/api/simulate', { expression: el.input.value });
    } catch (e) {
      showMessage(e.message, 'error');
      return;
    } finally {
      setBusy(false);
    }
    if (!body || !body.ok) {
      clearResults('Fix the expression to see its circuit.'); // never leave stale results beside an error
      showMessage(errorText(body), 'error');
      const pos = body && body.error ? body.error.position : null;
      el.input.focus();
      if (Number.isInteger(pos) && pos <= el.input.value.length) {
        el.input.setSelectionRange(pos, Math.min(pos + 1, el.input.value.length));
      }
      return;
    }
    state.requestId++;
    state.data = body;
    state.inputs = { ...body.current.inputs };
    state.current = body.current;
    renderTable();
    renderExplain();
    buildSwitches();
    renderCurrent(true);
    showMessage(`Simulation complete: ${body.variables.length} variable(s), ${body.combinations} row(s).`, 'success');
  }
  function insertAtCursor(text) {
    const input = el.input;
    const s = input.selectionStart == null ? input.value.length : input.selectionStart;
    const e = input.selectionEnd == null ? s : input.selectionEnd;
    input.value = input.value.slice(0, s) + text + input.value.slice(e);
    input.focus();
    input.setSelectionRange(s + text.length, s + text.length);
  }
  // ------------------------------------------------------------------ views
  // Each section declares which views show it (data-views). Only one view is visible at a time;
  // nothing is created or destroyed, so About can never be duplicated.
  const VIEWS = ['dashboard', 'simulator', 'truth-table', 'examples', 'about'];
  const navLinks = [...document.querySelectorAll('nav a[href^="#"]')];
  function showView(id, push) {
    if (!VIEWS.includes(id)) id = 'dashboard';
    document.querySelectorAll('[data-views]').forEach((s) => {
      s.hidden = !s.getAttribute('data-views').split(' ').includes(id);
    });
    navLinks.forEach((a) => {
      if (a.getAttribute('href') === '#' + id) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (push && location.hash !== '#' + id) history.pushState(null, '', '#' + id);
    if (id === 'truth-table' && state.current) highlightRow(); // scroll box was hidden while rendering
    try { window.scrollTo(0, 0); } catch (e) { /* not supported in some test environments */ }
  }
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest && ev.target.closest('a[href^="#"]');
    if (!a) return;
    const id = a.getAttribute('href').slice(1);
    if (!VIEWS.includes(id)) return;
    ev.preventDefault();
    showView(id, true);
  });
  window.addEventListener('popstate', () => showView(location.hash.slice(1), false));

  // --------------------------------------------------------------- examples
  async function loadExamples() {
    let list = [];
    try {
      const res = await fetch('/api/examples');
      list = (await res.json()).examples || [];
      setStatus(true);
    } catch (e) {
      setStatus(false);
      showMessage('Could not load the example list.', 'error');
    }
    el.examples.replaceChildren(...list.map((ex) => {
      const card = node('article', { class: 'card ex-card rise' });
      const actions = node('div', { class: 'ex-actions' });
      const load = node('button', { type: 'button', class: 'btn-ghost' }, 'Load');
      const run = node('button', { type: 'button', class: 'btn-ghost go' }, 'Load & simulate');
      load.addEventListener('click', () => {
        el.input.value = ex.expression;
        showMessage(`Loaded "${ex.name}". Edit it or press SIMULATE CIRCUIT.`, 'success');
        showView('simulator', true);
        el.input.focus();
      });
      run.addEventListener('click', () => { el.input.value = ex.expression; showView('simulator', true); simulate(); });
      actions.append(load, run);
      card.append(node('h3', {}, ex.name), node('code', {}, ex.expression), actions);
      return card;
    }));
  }

  // ---------------------------------------------------------------- wiring
  el.form.addEventListener('submit', (ev) => { ev.preventDefault(); simulate(); });
  el.clear.addEventListener('click', () => {
    el.input.value = '';
    clearResults();
    showMessage('Reset. Ready for a new expression.', 'success');
    el.input.focus();
  });
  document.querySelectorAll('[data-insert]').forEach((b) => b.addEventListener('click', () => insertAtCursor(b.getAttribute('data-insert'))));
  el.copy.addEventListener('click', copyTable);
  el.csv.addEventListener('click', downloadCsv);

  clearResults();
  showView(location.hash.slice(1), false);
  loadExamples().then(simulate);
})();
