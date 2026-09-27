/**
 * HEALTHSYNC AI — National Health Command Center
 * Client Application Logic
 */

document.addEventListener('DOMContentLoaded', function () {
  initLiveClock();
  initSidebarToggle();
  initDashboardChart();
  initWhatIfSimulator();
});

// ============================================================
// 1. LIVE COMMAND CENTER CLOCK
// ============================================================
function initLiveClock() {
  const clockEl = document.getElementById('liveClock');
  if (!clockEl) return;

  function update() {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    const timeStr = now.toLocaleTimeString('en-GB', { hour12: false });
    clockEl.textContent = `${dateStr} ${timeStr} IST`;
  }
  update();
  setInterval(update, 1000);
}

// ============================================================
// 2. SIDEBAR TOGGLE FOR MOBILE
// ============================================================
function initSidebarToggle() {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener('click', function () {
    sidebar.classList.toggle('show');
  });

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', function (e) {
    if (window.innerWidth < 992 && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
      sidebar.classList.remove('show');
    }
  });
}

// ============================================================
// 3. TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const toastId = 'toast_' + Date.now();
  const bgClass = type === 'success' ? 'bg-success text-white' :
                  type === 'danger' ? 'bg-danger text-white' :
                  type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white';

  const html = `
    <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 show shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center">
          <i class="fa-solid fa-circle-info me-2"></i>
          <span>${message}</span>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="document.getElementById('${toastId}').remove()"></button>
      </div>
    </div>
  `;
  container.insertAdjacentHTML('beforeend', html);

  setTimeout(() => {
    const el = document.getElementById(toastId);
    if (el) el.remove();
  }, 4500);
}

// ============================================================
// 4. DASHBOARD CHART (AI DEMAND FORECAST)
// ============================================================
let demandChartInstance = null;

function initDashboardChart() {
  const canvas = document.getElementById('demandForecastChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');

  // Baseline 7-day data
  const data7 = {
    labels: ['Day -6', 'Day -5', 'Day -4', 'Day -3', 'Day -2', 'Yesterday', 'Today'],
    actual: [480, 510, 495, 540, 560, 590, 620],
    predicted: [490, 505, 515, 535, 575, 610, 638]
  };

  const data30 = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    actual: [3400, 3620, 3890, 4100],
    predicted: [3450, 3700, 3980, 4310]
  };

  const data90 = {
    labels: ['Month 1', 'Month 2', 'Month 3'],
    actual: [14200, 15800, 16900],
    predicted: [14500, 16200, 18100]
  };

  demandChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data7.labels,
      datasets: [
        {
          label: 'Actual Demand (Units)',
          data: data7.actual,
          borderColor: '#0284c7',
          backgroundColor: 'rgba(2, 132, 199, 0.08)',
          borderWidth: 2.5,
          tension: 0.3,
          fill: true
        },
        {
          label: 'AI Predicted Demand (Units)',
          data: data7.predicted,
          borderColor: '#7928ca',
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          borderDash: [5, 5],
          tension: 0.3,
          pointBackgroundColor: '#7928ca'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { family: 'Inter', size: 12, weight: 600 } }
        },
        tooltip: {
          backgroundColor: '#0b132b',
          titleFont: { size: 13, weight: 'bold' },
          bodyFont: { size: 12 },
          padding: 10,
          cornerRadius: 8
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: { color: 'rgba(0, 0, 0, 0.05)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });

  // Window switch buttons
  document.querySelectorAll('.forecast-window-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.forecast-window-btn').forEach(b => b.classList.remove('active', 'btn-primary'));
      document.querySelectorAll('.forecast-window-btn').forEach(b => b.classList.add('btn-outline-primary'));
      this.classList.add('active', 'btn-primary');
      this.classList.remove('btn-outline-primary');

      const window = this.dataset.window;
      let activeData = data7;
      if (window === '30') activeData = data30;
      if (window === '90') activeData = data90;

      demandChartInstance.data.labels = activeData.labels;
      demandChartInstance.data.datasets[0].data = activeData.actual;
      demandChartInstance.data.datasets[1].data = activeData.predicted;
      demandChartInstance.update();
    });
  });
}

// ============================================================
// 5. WHAT-IF SIMULATOR ENGINE (INNOVATION 6)
// ============================================================
function initWhatIfSimulator() {
  const container = document.getElementById('whatIfContainer');
  if (!container) return;

  const buttons = document.querySelectorAll('.what-if-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', function () {
      buttons.forEach(b => b.classList.remove('active', 'btn-primary'));
      buttons.forEach(b => b.classList.add('btn-outline-secondary'));
      this.classList.add('active', 'btn-primary');
      this.classList.remove('btn-outline-secondary');

      const increasePct = parseFloat(this.dataset.percent);
      runWhatIfSimulation(increasePct);
    });
  });
}

function runWhatIfSimulation(percent) {
  const statusEl = document.getElementById('whatIfStatus');
  if (statusEl) statusEl.textContent = 'Simulating...';

  fetch('/api/forecast/what-if', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ demand_increase: percent })
  })
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        showToast('Simulation failed: ' + data.error, 'danger');
        return;
      }

      const sim = data.simulation;
      if (statusEl) statusEl.textContent = `Simulation active: +${percent}% Demand`;

      // Update UI metrics
      const bedEl = document.getElementById('simBedOccupancy');
      if (bedEl) bedEl.textContent = sim.simulated_bed_occupancy + '%';

      const alertEl = document.getElementById('simAlertCount');
      if (alertEl) alertEl.textContent = sim.simulated_alert_count;

      const critPhcEl = document.getElementById('simCritPhcs');
      if (critPhcEl) critPhcEl.textContent = sim.simulated_crit_phcs;

      const critMedsEl = document.getElementById('simCritMeds');
      if (critMedsEl) critMedsEl.textContent = sim.critical_medicines_count;

      const deficitEl = document.getElementById('simDeficitUnits');
      if (deficitEl) deficitEl.textContent = sim.total_shortage_units.toLocaleString() + ' units';

      // Update table if present
      const tableBody = document.getElementById('whatIfTableBody');
      if (tableBody && sim.all_medicines) {
        tableBody.innerHTML = '';
        sim.all_medicines.forEach(m => {
          const badgeClass = m.risk_level === 'CRITICAL' ? 'badge-critical' :
                            m.risk_level === 'HIGH' ? 'badge-high' :
                            m.risk_level === 'MEDIUM' ? 'badge-medium' : 'badge-low';
          const row = `
            <tr>
              <td class="fw-semibold">${m.medicine_name}</td>
              <td>${m.current_stock.toLocaleString()} ${m.unit}</td>
              <td>${m.daily_usage} / day</td>
              <td class="text-primary fw-bold">${m.predicted_7d.toLocaleString()} ${m.unit}</td>
              <td class="fw-bold">${m.stockout_days} days</td>
              <td><span class="badge ${badgeClass}">${m.risk_level}</span></td>
              <td class="small text-muted">${m.reason}</td>
            </tr>
          `;
          tableBody.insertAdjacentHTML('beforeend', row);
        });
      }

      showToast(`What-If stress test (+${percent}% demand) calculated successfully!`, 'primary');
    })
    .catch(err => {
      console.error(err);
      showToast('Error running simulation.', 'danger');
    });
}

// ============================================================
// 6. ALERT RESOLUTION (AJAX)
// ============================================================
function resolveAlert(alertId) {
  if (!confirm(`Resolve alert #${alertId}? This will log an audit event.`)) return;

  fetch(`/api/alerts/${alertId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        const row = document.getElementById(`alertRow_${alertId}`);
        if (row) {
          row.style.opacity = '0.5';
          const badge = row.querySelector('.alert-status-badge');
          if (badge) {
            badge.className = 'badge bg-secondary';
            badge.textContent = 'RESOLVED';
          }
          const btn = row.querySelector('.resolve-btn');
          if (btn) btn.remove();
        }
      } else {
        showToast(data.error || 'Failed to resolve alert', 'danger');
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Network error resolving alert.', 'danger');
    });
}

// ============================================================
// 7. REDISTRIBUTION APPROVE & REJECT (AJAX)
// ============================================================
function approveRedistribution(redistId) {
  if (!confirm(`Are you sure you want to APPROVE redistribution proposal #${redistId}? Medicine stocks will be updated.`)) return;

  fetch(`/api/redistribution/${redistId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'success');
        setTimeout(() => window.location.reload(), 1200);
      } else {
        showToast(data.error || 'Failed to approve redistribution', 'danger');
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Error approving transfer.', 'danger');
    });
}

function rejectRedistribution(redistId) {
  if (!confirm(`Are you sure you want to REJECT proposal #${redistId}?`)) return;

  fetch(`/api/redistribution/${redistId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast(data.message, 'info');
        setTimeout(() => window.location.reload(), 1200);
      } else {
        showToast(data.error || 'Failed to reject redistribution', 'danger');
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Error rejecting transfer.', 'danger');
    });
}

// ============================================================
// 8. FEDERATED LEARNING ROUND SIMULATION (INNOVATION 7)
// ============================================================
function triggerFederatedRound() {
  const btn = document.getElementById('btnStartFederatedRound');
  const spinner = document.getElementById('federatedSpinner');
  if (btn) btn.disabled = true;
  if (spinner) spinner.classList.remove('d-none');

  showToast('Initiating Federated Round: Dispatching local training parameters to 5 PHC edge nodes...', 'primary');

  setTimeout(() => {
    fetch('/api/federated/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast(`Round ${data.details.round_number} Completed! Global accuracy reached ${data.details.accuracy}% (+${data.details.accuracy_gain}%).`, 'success');
          setTimeout(() => window.location.reload(), 1500);
        } else {
          showToast('Failed to trigger federated round.', 'danger');
          if (btn) btn.disabled = false;
          if (spinner) spinner.classList.add('d-none');
        }
      })
      .catch(err => {
        console.error(err);
        showToast('Error executing federated round.', 'danger');
        if (btn) btn.disabled = false;
        if (spinner) spinner.classList.add('d-none');
      });
  }, 1000);
}

// ============================================================
// 9. CLIENT FILTERING UTILITIES
// ============================================================
function filterTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const table = document.getElementById(tableId);
  if (!input || !table) return;

  input.addEventListener('keyup', function () {
    const filter = input.value.toLowerCase();
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const text = row.textContent.toLowerCase();
      if (text.includes(filter)) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    }
  });
}
