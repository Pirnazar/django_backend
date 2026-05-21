(function () {
  'use strict';

  const cfg = window.BOX_BUILDER_CONFIG;
  let box = null;

  const $ = (id) => document.getElementById(id);

  function urlFor(tpl, id) { return tpl.replace('/0/', '/' + id + '/'); }

  function showMsg(text, ok) {
    const el = $('scan-msg');
    el.textContent = text;
    el.className = 'mt-3 text-sm ' + (ok ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400');
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3500);
  }

  function pulse(ok) {
    const inp = $('scan-input');
    inp.classList.remove('pulse-green', 'pulse-red');
    void inp.offsetWidth;
    inp.classList.add(ok ? 'pulse-green' : 'pulse-red');
  }

  function renderBox(data) {
    box = data;
    $('sum-code').textContent = data.box_code;
    const statusMap = { open: 'Открыта', closed: 'Закрыта', labeled: 'Этикетка' };
    $('sum-status').textContent = statusMap[data.status] || data.status;
    $('sum-dest').textContent = data.destination_code || '—';
    $('sum-wh').textContent = data.warehouse_code || '—';
    $('sum-count').textContent = data.total_items;
    $('sum-weight').textContent = (parseFloat(data.total_weight_kg) || 0).toFixed(2) + ' кг';
    $('sum-volume').textContent = (parseFloat(data.total_volume_m3) || 0).toFixed(4) + ' м³';
    $('items-count-badge').textContent = data.total_items;

    const tbody = $('items-tbody');
    tbody.innerHTML = '';
    (data.items || []).forEach((it, i) => {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td class="px-3 py-2 text-gray-500">' + (i + 1) + '</td>' +
        '<td class="px-3 py-2 font-mono">' + escapeHtml(it.item_code) + '</td>' +
        '<td class="px-3 py-2 font-mono text-gray-500">' + escapeHtml(it.barcode || '—') + '</td>' +
        '<td class="px-3 py-2">' + escapeHtml(it.client_code || '') + ' <span class="text-gray-500">' + escapeHtml((it.client_name || '').slice(0, 20)) + '</span></td>' +
        '<td class="px-3 py-2 text-right">' + it.weight_kg + ' кг</td>' +
        '<td class="px-3 py-2 text-right">' + it.volume_m3 + ' м³</td>' +
        '<td class="px-3 py-2 text-right">' +
          (data.status === 'open' ? '<button data-item="' + it.id + '" class="btn-rm text-red-500 hover:text-red-700">✕</button>' : '') +
        '</td>';
      tbody.appendChild(tr);
    });
    tbody.querySelectorAll('.btn-rm').forEach((b) => {
      b.addEventListener('click', () => removeItem(b.getAttribute('data-item')));
    });

    $('items-section').classList.toggle('hidden', !data.items || data.items.length === 0);

    if (data.status !== 'open') {
      $('scan-input').disabled = true;
      $('btn-close-box').disabled = true;
      $('btn-print').classList.remove('hidden');
      $('btn-new').classList.remove('hidden');
      $('btn-new').setAttribute('href', cfg.selfUrl);
    }
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
  }

  async function jpost(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cfg.csrfToken },
      body: JSON.stringify(body || {}),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || ('HTTP ' + r.status));
    return data;
  }

  async function createBox() {
    try {
      const data = await jpost(cfg.createUrl, {
        box_code: $('inp-box-code').value.trim(),
        barcode: $('inp-box-barcode').value.trim(),
      });
      renderBox(data);
      $('step-create').classList.add('hidden');
      $('step-scan').classList.remove('hidden');
      $('items-section').classList.remove('hidden');
      setTimeout(() => $('scan-input').focus(), 50);
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  }

  async function scan(code) {
    if (!code || !box) return;
    try {
      const data = await jpost(urlFor(cfg.scanUrlTpl, box.id), { barcode: code });
      renderBox(data);
      pulse(true);
      showMsg('✓ Добавлен ' + code, true);
    } catch (e) {
      pulse(false);
      showMsg('✗ ' + e.message, false);
    }
    $('scan-input').value = '';
    $('scan-input').focus();
  }

  async function removeItem(itemId) {
    if (!box) return;
    if (!confirm('Удалить груз из коробки?')) return;
    try {
      const data = await jpost(urlFor(cfg.removeUrlTpl, box.id), { item_id: parseInt(itemId, 10) });
      renderBox(data);
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  }

  async function closeBox() {
    if (!box) return;
    if (!confirm('Закрыть коробку? После этого нельзя добавлять грузы.')) return;
    try {
      const data = await jpost(urlFor(cfg.closeUrlTpl, box.id));
      renderBox(data);
    } catch (e) {
      alert('Ошибка: ' + e.message);
    }
  }

  async function printLabel() {
    if (!box) return;
    try {
      const r = await fetch(cfg.printerUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(box.print_payload),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || ('HTTP ' + r.status));
      await jpost(urlFor(cfg.printedUrlTpl, box.id));
      alert('Этикетка отправлена на принтер');
    } catch (e) {
      alert('Ошибка печати: ' + e.message + '\n\nПроверьте, что printer-сервис запущен на ' + cfg.printerUrl);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('btn-create-box').addEventListener('click', createBox);
    $('btn-close-box').addEventListener('click', closeBox);
    $('btn-print').addEventListener('click', printLabel);

    $('scan-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const v = $('scan-input').value.trim();
        if (v) scan(v);
      }
    });
  });
})();
