/**
 * Ýyldyrym Cargo — Admin Dashboard
 * Chart.js v4 + polling (no WebSocket).
 * Config injected by template: window.DASH_CONFIG
 */
'use strict';

// ── Config ────────────────────────────────────────────────────────────────────
const CFG = window.DASH_CONFIG || {};
const API          = CFG.apiBase      || '/admin/dashboard/api/';
const HAS_FINANCE  = CFG.hasFinance   === true;
const POLL_MS      = CFG.pollInterval || 30_000;

// ── Brand palette ─────────────────────────────────────────────────────────────
const C = {
  blue:   '#2563EB',
  green:  '#16A34A',
  amber:  '#F59E0B',
  red:    '#EF4444',
  sky:    '#0EA5E9',
  violet: '#8B5CF6',
  teal:   '#14B8A6',
  gray:   '#64748B',
  indigo: '#6366F1',
  orange: '#F97316',
  cyan:   '#06B6D4',
};

// ── Status → Russian label ────────────────────────────────────────────────────
const DELIVERY_LABELS = {
  created:                'Создан',
  at_china_warehouse:     'Склад (КНР)',
  measured:               'Измерен',
  photographed:           'Сфотографирован',
  labeled:                'Маркирован',
  packed:                 'Упакован',
  grouped:                'В партии',
  sent_to_urumqi:         'Отправлен→Урумчи',
  arrived_urumqi:         'Прибыл Урумчи',
  sent_to_turkmenistan:   'Отправлен→ТМ',
  arrived_turkmenistan:   'Прибыл в ТМ',
  out_for_delivery:       'На доставке',
  delivered:              'Доставлен',
  cancelled:              'Отменён',
};

const DELIVERY_COLORS = {
  created:                C.gray,
  at_china_warehouse:     C.blue,
  measured:               C.sky,
  photographed:           C.violet,
  labeled:                C.cyan,
  packed:                 C.amber,
  grouped:                C.indigo,
  sent_to_urumqi:         C.orange,
  arrived_urumqi:         C.teal,
  sent_to_turkmenistan:   C.orange,
  arrived_turkmenistan:   C.teal,
  out_for_delivery:       C.green,
  delivered:              C.green,
  cancelled:              C.red,
};

const PAYMENT_LABELS = {
  unpaid:         'Не оплачено',
  partially_paid: 'Частично',
  paid:           'Оплачено',
  refunded:       'Возврат',
};

const PAYMENT_COLORS = {
  unpaid:         C.red,
  partially_paid: C.amber,
  paid:           C.green,
  refunded:       C.violet,
};

const ACTION_LABELS = { CREATE: 'Создан', UPDATE: 'Изменён', DELETE: 'Удалён' };

// ── Chart instances ───────────────────────────────────────────────────────────
const charts = {};

// ── Detect dark mode ──────────────────────────────────────────────────────────
function isDark() {
  return document.documentElement.classList.contains('dark');
}

function chartTextColor() {
  return isDark() ? '#94A3B8' : '#64748B';
}

function chartGridColor() {
  return isDark() ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)';
}

// ── Chart.js default overrides ────────────────────────────────────────────────
function applyChartDefaults() {
  const tc = chartTextColor();
  Chart.defaults.color = tc;
  Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
  Chart.defaults.font.size = 11;
}

// ── Init empty charts ─────────────────────────────────────────────────────────
function initCharts() {
  applyChartDefaults();

  // Items by delivery_status — doughnut
  charts.itemsStatus = new Chart(
    document.getElementById('chartItemsStatus'),
    {
      type: 'doughnut',
      data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderWidth: 2, borderColor: 'transparent' }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: {
          legend: {
            position: 'right',
            labels: { boxWidth: 10, padding: 8, font: { size: 10 } },
          },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } },
        },
      },
    }
  );

  // Payments by payment_status — doughnut
  charts.paymentsStatus = new Chart(
    document.getElementById('chartPaymentsStatus'),
    {
      type: 'doughnut',
      data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderWidth: 2, borderColor: 'transparent' }] },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: {
          legend: {
            position: 'right',
            labels: { boxWidth: 10, padding: 8, font: { size: 10 } },
          },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed}` } },
        },
      },
    }
  );

  // Revenue & expenses — bar (finance only)
  if (HAS_FINANCE && document.getElementById('chartRevenue')) {
    charts.revenue = new Chart(
      document.getElementById('chartRevenue'),
      {
        type: 'bar',
        data: {
          labels: [],
          datasets: [
            { label: 'Доход', data: [], backgroundColor: C.green + 'CC', borderRadius: 4 },
            { label: 'Расходы', data: [], backgroundColor: C.red + 'CC', borderRadius: 4 },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          scales: {
            x: { grid: { color: chartGridColor() }, ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 10 } },
            y: { beginAtZero: true, grid: { color: chartGridColor() } },
          },
          plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 10 } } },
        },
      }
    );
  }

  // Items by day — line
  charts.itemsByDay = new Chart(
    document.getElementById('chartItemsByDay'),
    {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Новых грузов',
          data: [],
          borderColor: C.blue,
          backgroundColor: C.blue + '18',
          borderWidth: 2,
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          fill: true,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { grid: { color: chartGridColor() }, ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 10 } },
          y: { beginAtZero: true, grid: { color: chartGridColor() } },
        },
        plugins: { legend: { display: false } },
      },
    }
  );

  // Items by destination — horizontal bar
  charts.byDestination = new Chart(
    document.getElementById('chartByDestination'),
    {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'Грузов', data: [], backgroundColor: C.sky + 'CC', borderRadius: 4 }] },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { beginAtZero: true, grid: { color: chartGridColor() } },
          y: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
      },
    }
  );

  // Items by warehouse — horizontal bar
  charts.byWarehouse = new Chart(
    document.getElementById('chartByWarehouse'),
    {
      type: 'bar',
      data: { labels: [], datasets: [{ label: 'Грузов', data: [], backgroundColor: C.teal + 'CC', borderRadius: 4 }] },
      options: {
        indexAxis: 'y',
        responsive: true, maintainAspectRatio: false,
        scales: {
          x: { beginAtZero: true, grid: { color: chartGridColor() } },
          y: { grid: { display: false } },
        },
        plugins: { legend: { display: false } },
      },
    }
  );
}

// ── Chart update helpers ──────────────────────────────────────────────────────
function updateDoughnut(chart, rows, labelMap, colorMap) {
  if (!chart) return;
  chart.data.labels   = rows.map(r => labelMap[r.status] || r.status);
  chart.data.datasets[0].data            = rows.map(r => r.count);
  chart.data.datasets[0].backgroundColor = rows.map(r => colorMap[r.status] || C.gray);
  chart.update('none'); // skip animation for silent refresh
}

function updateBarXY(chart, labels, datasets) {
  if (!chart) return;
  chart.data.labels = labels;
  datasets.forEach((d, i) => { chart.data.datasets[i].data = d; });
  chart.update('none');
}

// ── Card update ───────────────────────────────────────────────────────────────
function updateCards(data) {
  // Update any element with data-key="..."
  document.querySelectorAll('[data-key]').forEach(el => {
    const key = el.dataset.key;
    if (!(key in data)) return;
    const val = data[key];
    const fmt = el.dataset.format;
    if (fmt === 'money') {
      el.textContent = Number(val).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' $';
    } else {
      el.textContent = val;
    }
  });
}

// ── Table renderers ───────────────────────────────────────────────────────────
function statusBadge(status, label) {
  return `<span class="cg-status-badge cg-status-${status}">${label}</span>`;
}

function payBadge(status, label) {
  return `<span class="cg-status-badge cg-pay-${status}">${label}</span>`;
}

function renderRecentItems(items) {
  const tbody = document.getElementById('tbody-recent-items');
  if (!tbody) return;
  if (!items || !items.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="cg-empty">Нет грузов</td></tr>';
    return;
  }
  tbody.innerHTML = items.map(i => `
    <tr>
      <td><a href="${i.admin_url}" class="cg-code">${i.item_code}</a></td>
      <td class="truncate max-w-[80px]">${i.client_name}</td>
      <td>${statusBadge(i.delivery_status, (DELIVERY_LABELS[i.delivery_status] || i.delivery_status_display).substring(0, 12))}</td>
      <td class="text-right text-gray-500">${i.created_at}</td>
    </tr>`).join('');
}

function renderRecentPayments(payments) {
  const tbody = document.getElementById('tbody-recent-payments');
  if (!tbody) return;
  if (!payments || !payments.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="cg-empty">Нет платежей</td></tr>';
    return;
  }
  tbody.innerHTML = payments.map(p => `
    <tr>
      <td class="truncate max-w-[80px]">${p.client_name}</td>
      <td class="font-medium">${Number(p.amount).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${p.currency}</td>
      <td>${payBadge(p.status, p.status_display)}</td>
      <td class="text-right text-gray-500">${p.created_at}</td>
    </tr>`).join('');
}

function renderRecentActivity(activity) {
  const tbody = document.getElementById('tbody-recent-activity');
  if (!tbody) return;
  if (!activity || !activity.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="cg-empty">Нет действий</td></tr>';
    return;
  }
  const actionClass = { CREATE: 'text-green-600 dark:text-green-400', UPDATE: 'text-amber-600 dark:text-amber-400', DELETE: 'text-red-600 dark:text-red-400' };
  tbody.innerHTML = activity.map(l => `
    <tr>
      <td><span class="${actionClass[l.action] || ''} font-medium">${ACTION_LABELS[l.action] || l.action}</span></td>
      <td class="truncate max-w-[70px]">${l.entity_type} #${l.entity_id}</td>
      <td class="truncate max-w-[60px]">${l.actor}</td>
      <td class="text-right text-gray-500 text-[10px]">${l.created_at}</td>
    </tr>`).join('');
}

// ── UI state helpers ──────────────────────────────────────────────────────────
function setLoading(on) {
  const spinner = document.getElementById('dash-spinner');
  if (spinner) spinner.classList.toggle('hidden', !on);
}

function showError(show) {
  const badge = document.getElementById('dash-error-badge');
  if (badge) badge.classList.toggle('hidden', !show);
}

function markUpdated() {
  const el = document.getElementById('dash-updated');
  if (!el) return;
  const now = new Date();
  const hms = now.toTimeString().slice(0, 8);
  el.textContent = `Обновлено: ${hms}`;
}

// ── Fetch helper ──────────────────────────────────────────────────────────────
async function fetchJson(url) {
  const res = await fetch(url, { credentials: 'same-origin' });
  if (res.status === 401) {
    window.location.href = '/admin/login/?next=' + encodeURIComponent(window.location.pathname);
    throw new Error('Unauthorized');
  }
  if (!res.ok) throw new Error(`HTTP ${res.status} at ${url}`);
  return res.json();
}

// ── Main refresh ──────────────────────────────────────────────────────────────
async function refresh() {
  setLoading(true);
  try {
    // Parallel fetch of all chart & table data
    const fetches = [
      fetchJson(API + 'summary/'),
      fetchJson(API + 'items-status/'),
      fetchJson(API + 'payments-status/'),
      fetchJson(API + 'items-by-day/'),
      fetchJson(API + 'items-by-destination/'),
      fetchJson(API + 'items-by-warehouse/'),
      fetchJson(API + 'recent-items/'),
      fetchJson(API + 'recent-payments/'),
      fetchJson(API + 'recent-activity/'),
    ];
    if (HAS_FINANCE) fetches.push(fetchJson(API + 'revenue-expenses/'));

    const results = await Promise.allSettled(fetches);
    const [
      resSummary, resItemsStatus, resPayStatus,
      resItemsByDay, resByDest, resByWh,
      resRecentItems, resRecentPay, resRecentAct,
      resRevenue,
    ] = results;

    // Cards
    if (resSummary.status === 'fulfilled') updateCards(resSummary.value);

    // Doughnut: items by delivery_status
    if (resItemsStatus.status === 'fulfilled') {
      updateDoughnut(charts.itemsStatus, resItemsStatus.value.items || [], DELIVERY_LABELS, DELIVERY_COLORS);
    }

    // Doughnut: payments by status
    if (resPayStatus.status === 'fulfilled') {
      updateDoughnut(charts.paymentsStatus, resPayStatus.value.payments || [], PAYMENT_LABELS, PAYMENT_COLORS);
    }

    // Line: items by day
    if (resItemsByDay.status === 'fulfilled') {
      const d = resItemsByDay.value;
      updateBarXY(charts.itemsByDay, d.labels || [], [d.counts || []]);
    }

    // Bar: by destination
    if (resByDest.status === 'fulfilled') {
      const rows = resByDest.value.destinations || [];
      updateBarXY(charts.byDestination, rows.map(r => r.code), [rows.map(r => r.count)]);
    }

    // Bar: by warehouse
    if (resByWh.status === 'fulfilled') {
      const rows = resByWh.value.warehouses || [];
      updateBarXY(charts.byWarehouse, rows.map(r => r.code), [rows.map(r => r.count)]);
    }

    // Bar: revenue (finance)
    if (HAS_FINANCE && resRevenue && resRevenue.status === 'fulfilled') {
      const d = resRevenue.value;
      updateBarXY(charts.revenue, d.labels || [], [d.revenue || [], d.expenses || []]);
    }

    // Recent tables
    if (resRecentItems.status === 'fulfilled') renderRecentItems(resRecentItems.value.items);
    if (resRecentPay.status === 'fulfilled')   renderRecentPayments(resRecentPay.value.payments);
    if (resRecentAct.status === 'fulfilled')   renderRecentActivity(resRecentAct.value.activity);

    showError(false);
    markUpdated();
  } catch (err) {
    console.warn('[Dashboard] refresh error:', err);
    showError(true);
  } finally {
    setLoading(false);
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
let pollTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  refresh();
  pollTimer = setInterval(refresh, POLL_MS);

  document.getElementById('btn-refresh')?.addEventListener('click', () => {
    clearInterval(pollTimer);
    refresh();
    pollTimer = setInterval(refresh, POLL_MS);
  });
});
