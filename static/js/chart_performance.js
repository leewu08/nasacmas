document.addEventListener('DOMContentLoaded', () => {
  const ctx = document.getElementById('performanceChart');
  if (!ctx) return;

  // 글로벌 변수에서 데이터 꺼내기
  const history = window.PERF_HISTORY || [];
  const labels = history.map(d => d.time);
  const dataPoints = history.map(d => d.dv_avg);

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'DV 평균',
        data: dataPoints,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
});
