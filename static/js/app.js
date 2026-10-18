if (window.Chart && matchMedia('(prefers-reduced-motion: reduce)').matches) Chart.defaults.animation = false;
document.querySelectorAll('[data-autosubmit]').forEach(select => select.addEventListener('change', () => select.form.requestSubmit()));
document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => { if (!confirm(form.dataset.confirm)) event.preventDefault(); }));
document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => { const input = document.querySelector('#question'); input.value = button.dataset.question; input.focus(); }));
document.querySelectorAll('details').forEach(detail => detail.addEventListener('toggle', () => { if (detail.open && detail.closest('.topbar')) document.querySelectorAll('.topbar details').forEach(other => { if (other !== detail) other.open = false; }); }));
const chartNode = document.querySelector('#chart-data');
if (chartNode && window.Chart) {
  const data = JSON.parse(chartNode.textContent);
  new Chart(document.querySelector('#revenueChart'), {type: 'bar', data: {labels: data.labels, datasets: [{label: 'Revenue', data: data.revenue, backgroundColor: '#3478f6', borderRadius: 4, maxBarThickness: 24}, {label: 'Expenses', data: data.expenses, backgroundColor: '#b9d0fc', borderRadius: 4, maxBarThickness: 24}]}, options: {responsive: true, maintainAspectRatio: false, plugins: {legend: {display: false}, tooltip: {padding: 12, backgroundColor: '#172a49'}}, scales: {x: {grid: {display: false}, border: {display: false}, ticks: {color: '#8b97aa', font: {size: 12}}}, y: {beginAtZero: true, border: {display: false}, grid: {color: '#f0f3f8'}, ticks: {maxTicksLimit: 5, color: '#8b97aa', callback: value => Intl.NumberFormat('en', {notation: 'compact'}).format(value)}}}}});
}
const forecastNode = document.querySelector('#forecast-data');
if (forecastNode && window.Chart) {
  const data = JSON.parse(forecastNode.textContent);
  new Chart(document.querySelector('#forecastChart'), {type: 'line', data: {labels: data.points.map(p => p.date), datasets: [{label: 'Projected cash balance', data: data.points.map(p => p.balance), borderColor: '#2469ee', backgroundColor: '#2469ee0d', fill: true, tension: .25, pointRadius: 2}, {label: 'Expected inflow', data: data.points.map(p => p.inflow), borderColor: '#1da780', tension: .25, pointRadius: 0}, {label: 'Expected outflow', data: data.points.map(p => p.outflow), borderColor: '#f18b77', tension: .25, pointRadius: 0}]}, options: {responsive: true, maintainAspectRatio: false, plugins: {legend: {position: 'top', labels: {usePointStyle: true, boxWidth: 8}}}, scales: {x: {grid: {display: false}, ticks: {maxTicksLimit: 7}}, y: {grid: {color: '#f0f3f8'}}}}});
}
const chat = document.querySelector('#chat-messages');
const survivalNode = document.querySelector('#survival-chart-data');
if (survivalNode && window.Chart) {
  const data = JSON.parse(survivalNode.textContent);
  const reserve = Number(JSON.parse(document.querySelector('#survival-reserve').textContent));
  new Chart(document.querySelector('#survivalChart'), {type: 'line', data: {
    labels: data.points.map(point => point.date), datasets: [
      {label: 'Cash on assumed receipt dates', data: data.points.map(point => point.balance), borderColor: '#075df5', backgroundColor: '#075df509', fill: true, tension: 0, pointRadius: data.points.map(point => Number(point.balance) < reserve ? 3 : 1), pointBackgroundColor: data.points.map(point => Number(point.balance) < reserve ? '#c82340' : '#075df5'), segment: {borderColor: context => Number(context.p1.parsed.y) < reserve ? '#c82340' : '#075df5'}},
      {label: 'Minimum reserve', data: data.points.map(() => reserve), borderColor: '#b21b36', borderDash: [5, 5], borderWidth: 1.5, pointRadius: 0}
    ]}, options: {responsive: true, maintainAspectRatio: false, animation: !matchMedia('(prefers-reduced-motion: reduce)').matches,
      plugins: {legend: {position: 'bottom', labels: {color: '#52627a', boxWidth: 12, font: {size: 12}}}, tooltip: {callbacks: {label: context => context.dataset.label + ': ' + Intl.NumberFormat('en', {maximumFractionDigits: 2}).format(context.parsed.y)}}},
      scales: {x: {grid: {display: false}, ticks: {maxTicksLimit: 5, color: '#52627a', callback: function(value) {return this.getLabelForValue(value).slice(5);}}}, y: {ticks: {color: '#52627a', maxTicksLimit: 5, callback: value => Intl.NumberFormat('en', {notation: 'compact'}).format(value)}, grid: {color: '#edf1f6'}}}}});
}
if (chat) chat.scrollTop = chat.scrollHeight;
window.addEventListener('pageshow', event => { if (event.persisted && location.pathname.startsWith('/b/')) location.reload(); });
