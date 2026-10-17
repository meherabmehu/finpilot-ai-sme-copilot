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
if (chat) chat.scrollTop = chat.scrollHeight;
window.addEventListener('pageshow', event => { if (event.persisted && location.pathname.startsWith('/b/')) location.reload(); });
