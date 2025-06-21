document.addEventListener('DOMContentLoaded', () => {
  const ctx = document.getElementById('performanceChart');
  if (ctx) {
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: {{ history | map(attribute='time') | list }},
        datasets: [{
          label: 'DV 평균',
          data: {{ history | map(attribute='dv_avg') | list }},
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
  }
});
