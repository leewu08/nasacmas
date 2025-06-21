// 📁 static/js/chart_compare.js

document.addEventListener('DOMContentLoaded', () => {
  const scatterCanvas = document.getElementById('scatterPlot');
  if (scatterCanvas && window.scatterData) {
    const ctx = scatterCanvas.getContext('2d');
    new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'RUL Scatter',
          data: window.scatterData,
          backgroundColor: 'rgba(54, 162, 235, 0.6)'
        }]
      },
      options: {
        scales: {
          x: { title: { display: true, text: 'Unit' } },
          y: { title: { display: true, text: 'RUL' } }
        }
      }
    });
  }

  const heatmapCanvas = document.getElementById('heatmap');
  if (heatmapCanvas && window.heatmapData) {
    const ctx = heatmapCanvas.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: window.heatmapData.map(item => item[0]),
        datasets: [{
          label: 'MAE by Unit',
          data: window.heatmapData.map(item => item[1]),
          backgroundColor: 'rgba(255, 99, 132, 0.5)'
        }]
      }
    });
  }
});
