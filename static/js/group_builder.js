/**
 * Shipment Group Builder — live summary + AJAX interactions.
 */
'use strict';

(function () {
  const CFG = window.BUILDER_CONFIG || {};

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const selDest    = document.getElementById('sel-destination');
  const selWh      = document.getElementById('sel-warehouse');
  const btnLoad    = document.getElementById('btn-load-items');
  const section    = document.getElementById('items-section');
  const loader     = document.getElementById('items-loader');
  const emptyMsg   = document.getElementById('items-empty');
  const tbody      = document.getElementById('items-tbody');
  const chkAll     = document.getElementById('chk-all');
  const searchInp  = document.getElementById('search-items');
  const btnSelAll  = document.getElementById('btn-select-all');
  const btnClrAll  = document.getElementById('btn-clear-all');
  const countBadge = document.getElementById('items-count-badge');

  const sumCount   = document.getElementById('sum-count');
  const sumWeight  = document.getElementById('sum-weight');
  const sumVolume  = document.getElementById('sum-volume');
  const sumTotal   = document.getElementById('sum-total');
  const sumUnpaid  = document.getElementById('sum-unpaid');

  const inpCode    = document.getElementById('inp-group-code');
  const inpStatus  = document.getElementById('inp-status');
  const inpComment = document.getElementById('inp-comment');
  const btnCreate  = document.getElementById('btn-create-group');
  const errBox     = document.getElementById('create-error');

  // ── State ─────────────────────────────────────────────────────────────────
  let allItems = [];  // raw JSON from API

  // ── Helpers ───────────────────────────────────────────────────────────────

  function fmt(n, unit) {
    return n.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + (unit ? ' ' + unit : '');
  }

  function getChecked() {
    return [...document.querySelectorAll('#items-tbody .row-check:checked')];
  }

  function getVisibleRows() {
    return [...document.querySelectorAll('#items-tbody tr:not([hidden])')];
  }

  // ── Enable load button when both selects have values ─────────────────────
  function onFilterChange() {
    btnLoad.disabled = !(selDest.value && selWh.value);
  }
  selDest.addEventListener('change', onFilterChange);
  selWh.addEventListener('change', onFilterChange);

  // ── Load items via AJAX ───────────────────────────────────────────────────
  btnLoad.addEventListener('click', async () => {
    section.classList.remove('hidden');
    loader.classList.remove('hidden');
    emptyMsg.classList.add('hidden');
    tbody.innerHTML = '';
    updateSummary();

    const url = `${CFG.itemsUrl}?destination_id=${selDest.value}&warehouse_id=${selWh.value}`;
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      const data = await res.json();
      allItems = data.items || [];
    } catch {
      allItems = [];
    }

    loader.classList.add('hidden');

    if (!allItems.length) {
      emptyMsg.classList.remove('hidden');
      countBadge.textContent = '0';
      return;
    }

    countBadge.textContent = allItems.length;
    renderRows(allItems);
    updateSummary();
  });

  // ── Render rows ───────────────────────────────────────────────────────────
  function renderRows(items) {
    tbody.innerHTML = '';
    items.forEach(item => {
      const tr = document.createElement('tr');
      tr.dataset.id       = item.id;
      tr.dataset.weight   = item.weight_kg;
      tr.dataset.volume   = item.volume_m3;
      tr.dataset.total    = item.total_price;
      tr.dataset.payment  = item.payment_status;
      tr.dataset.search   = (item.item_code + ' ' + item.client_code + ' ' + item.client_name).toLowerCase();

      tr.className = 'hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer';
      tr.innerHTML = `
        <td class="px-3 py-2 text-center">
          <input type="checkbox" class="row-check rounded" data-id="${item.id}">
        </td>
        <td class="px-3 py-2"><span class="cg-code">${item.item_code}</span></td>
        <td class="px-3 py-2">
          <span class="font-mono text-xs text-gray-500">${item.client_code}</span>
          <span class="ml-1 text-gray-700 dark:text-gray-300">${item.client_name}</span>
        </td>
        <td class="px-3 py-2 text-right cg-nowrap">${fmt(item.weight_kg)} кг</td>
        <td class="px-3 py-2 text-right cg-nowrap">${fmt(item.volume_m3)} м³</td>
        <td class="px-3 py-2 text-xs text-gray-600 dark:text-gray-400">${item.payment_status}</td>
        <td class="px-3 py-2 text-xs text-gray-600 dark:text-gray-400">${item.delivery_status}</td>
        <td class="px-3 py-2 text-xs text-gray-400">${item.created_at}</td>
      `;

      // Click row → toggle checkbox
      tr.addEventListener('click', e => {
        if (e.target.type === 'checkbox') return;
        const chk = tr.querySelector('.row-check');
        chk.checked = !chk.checked;
        onCheckChange(tr, chk.checked);
      });

      tr.querySelector('.row-check').addEventListener('change', e => {
        onCheckChange(tr, e.target.checked);
      });

      tbody.appendChild(tr);
    });
    updateHeaderCheckbox();
  }

  function onCheckChange(tr, checked) {
    tr.classList.toggle('selected', checked);
    updateSummary();
    updateHeaderCheckbox();
  }

  // ── Summary ───────────────────────────────────────────────────────────────
  function updateSummary() {
    const checked = getChecked();
    let count = 0, weight = 0, volume = 0, total = 0, unpaid = 0;

    checked.forEach(chk => {
      const tr = chk.closest('tr');
      count++;
      weight += parseFloat(tr.dataset.weight) || 0;
      volume += parseFloat(tr.dataset.volume) || 0;
      total  += parseFloat(tr.dataset.total)  || 0;
      if (tr.dataset.payment !== 'Оплачено') {
        unpaid += parseFloat(tr.dataset.total) || 0;
      }
    });

    sumCount.textContent  = count;
    sumWeight.textContent = fmt(weight) + ' кг';
    sumVolume.textContent = fmt(volume) + ' м³';
    sumTotal.textContent  = fmt(total);
    sumUnpaid.textContent = fmt(unpaid);

    btnCreate.disabled = count === 0;
  }

  function updateHeaderCheckbox() {
    const all     = [...document.querySelectorAll('#items-tbody .row-check')];
    const checked = all.filter(c => c.checked);
    chkAll.checked       = all.length > 0 && checked.length === all.length;
    chkAll.indeterminate = checked.length > 0 && checked.length < all.length;
  }

  // ── Select / clear all ────────────────────────────────────────────────────
  chkAll.addEventListener('change', () => {
    getVisibleRows().forEach(tr => {
      const chk = tr.querySelector('.row-check');
      if (chk) {
        chk.checked = chkAll.checked;
        tr.classList.toggle('selected', chkAll.checked);
      }
    });
    updateSummary();
  });

  btnSelAll.addEventListener('click', () => {
    getVisibleRows().forEach(tr => {
      const chk = tr.querySelector('.row-check');
      if (chk) { chk.checked = true; tr.classList.add('selected'); }
    });
    updateSummary();
    updateHeaderCheckbox();
  });

  btnClrAll.addEventListener('click', () => {
    document.querySelectorAll('#items-tbody .row-check').forEach(chk => {
      chk.checked = false;
      chk.closest('tr').classList.remove('selected');
    });
    updateSummary();
    updateHeaderCheckbox();
  });

  // ── Search filter ─────────────────────────────────────────────────────────
  searchInp.addEventListener('input', () => {
    const q = searchInp.value.toLowerCase().trim();
    document.querySelectorAll('#items-tbody tr').forEach(tr => {
      const match = !q || (tr.dataset.search || '').includes(q);
      tr.hidden = !match;
    });
    updateHeaderCheckbox();
  });

  // ── Create group ──────────────────────────────────────────────────────────
  btnCreate.addEventListener('click', async () => {
    errBox.classList.add('hidden');
    const itemIds = getChecked().map(chk => parseInt(chk.dataset.id, 10));

    if (!itemIds.length) return;

    btnCreate.disabled = true;
    btnCreate.textContent = 'Создание...';

    try {
      const res = await fetch(CFG.createUrl, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CFG.csrfToken,
        },
        body: JSON.stringify({
          destination_id: selDest.value,
          warehouse_id:   selWh.value,
          item_ids:       itemIds,
          group_code:     inpCode.value.trim(),
          status:         inpStatus.value,
          comment:        inpComment.value.trim(),
        }),
      });

      const data = await res.json();

      if (data.success) {
        window.location.href = data.admin_url;
      } else {
        showError(data.error || 'Неизвестная ошибка');
        btnCreate.disabled = false;
        btnCreate.innerHTML = '<span class="material-symbols-outlined text-lg">add_box</span> Создать партию';
      }
    } catch (e) {
      showError('Ошибка соединения: ' + e.message);
      btnCreate.disabled = false;
      btnCreate.innerHTML = '<span class="material-symbols-outlined text-lg">add_box</span> Создать партию';
    }
  });

  function showError(msg) {
    errBox.textContent = msg;
    errBox.classList.remove('hidden');
  }

})();
