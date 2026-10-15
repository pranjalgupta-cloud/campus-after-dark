/* ════════════════════════════════
   Campus After Dark — main.js
   Shared frontend utilities
   ════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
    setTimeout(function () {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Sidebar toggle for mobile
  var sidebarToggle = document.getElementById('sidebarToggle');
  var sidebar = document.querySelector('.cad-sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
    // Close on outside click
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('show') &&
          !sidebar.contains(e.target) &&
          e.target !== sidebarToggle) {
        sidebar.classList.remove('show');
      }
    });
  }

  // Highlight active nav link in sidebar
  var current = window.location.pathname;
  document.querySelectorAll('.cad-sidebar .nav-link').forEach(function (link) {
    if (link.getAttribute('href') === current) {
      link.classList.add('active');
    }
  });

  // Confirm dialogs for destructive actions
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      var msg = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!confirm(msg)) e.preventDefault();
    });
  });

  // Mark notifications as read when bell is clicked
  var notifBtn = document.getElementById('markAllRead');
  if (notifBtn) {
    notifBtn.addEventListener('click', function () {
      fetch('/bookings/notifications/read/', { method: 'GET' })
        .then(function () {
          document.querySelectorAll('.cad-notif-badge').forEach(function (b) {
            b.remove();
          });
        });
    });
  }
});

// ── Booking price calculator ──────────────────────────────────────────
function calcBookingPrice() {
  var startInput = document.getElementById('id_start_time');
  var endInput = document.getElementById('id_end_time');
  var priceEl = document.getElementById('pricePerHour');
  var breakdownEl = document.getElementById('priceBreakdown');
  var commRateEl = document.getElementById('commissionRate');

  if (!startInput || !endInput || !priceEl || !breakdownEl) return;

  var start = startInput.value;
  var end = endInput.value;
  if (!start || !end) { breakdownEl.style.display = 'none'; return; }

  var [sh, sm] = start.split(':').map(Number);
  var [eh, em] = end.split(':').map(Number);
  var hours = ((eh * 60 + em) - (sh * 60 + sm)) / 60;

  if (hours <= 0) { breakdownEl.style.display = 'none'; return; }

  var pricePerHour = parseFloat(priceEl.value);
  var commRate = parseFloat(commRateEl ? commRateEl.value : '10');
  var subtotal = pricePerHour * hours;
  var commission = subtotal * commRate / 100;
  var payout = subtotal - commission;

  function fmt(n) { return '₹' + n.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }

  document.getElementById('calcHours').textContent = hours.toFixed(2) + ' hrs';
  document.getElementById('calcSubtotal').textContent = fmt(subtotal);
  document.getElementById('calcCommission').textContent = fmt(commission);
  document.getElementById('calcPayout').textContent = fmt(payout);
  document.getElementById('calcTotal').textContent = fmt(subtotal);
  breakdownEl.style.display = 'block';
}

// ── Dashboard Charts ──────────────────────────────────────────────────
function renderRevenueChart(canvasId, labels, revenueData, commissionData) {
  var ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Gross Revenue (₹)',
          data: revenueData,
          backgroundColor: 'rgba(15,32,68,0.85)',
          borderRadius: 6,
        },
        {
          label: 'Platform Commission (₹)',
          data: commissionData,
          backgroundColor: 'rgba(245,158,11,0.8)',
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: function (ctx) {
              return ctx.dataset.label + ': ₹' + ctx.parsed.y.toLocaleString('en-IN');
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (v) { return '₹' + v.toLocaleString('en-IN'); }
          }
        }
      }
    }
  });
}

function renderAdminChart(canvasId, labels, bookingCounts, revenueData) {
  var ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Bookings',
          data: bookingCounts,
          borderColor: '#0f2044',
          backgroundColor: 'rgba(15,32,68,0.08)',
          fill: true,
          tension: 0.4,
          yAxisID: 'y',
        },
        {
          label: 'Revenue (₹)',
          data: revenueData,
          borderColor: '#f59e0b',
          backgroundColor: 'rgba(245,158,11,0.08)',
          fill: true,
          tension: 0.4,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { position: 'top' } },
      scales: {
        y: { beginAtZero: true, position: 'left', title: { display: true, text: 'Bookings' } },
        y1: {
          beginAtZero: true, position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { callback: function (v) { return '₹' + v.toLocaleString('en-IN'); } }
        }
      }
    }
  });
}
