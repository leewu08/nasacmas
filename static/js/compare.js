// static/js/compare.js

document.addEventListener('DOMContentLoaded', () => {
  // 데이터 받기 (서버에서 window.*로 등록되어 있어야 함)
  const scatter = window.SCATTER_DATA || [];
  const heatmap = window.HEATMAP_DATA || [];

  // ✅ Scatter plot (Prediction vs Actual)
  Plotly.newPlot('scatter-plot', [
    {
      x: scatter.map(r => r.y_true),
      y: scatter.map(r => r.y_pred),
      mode: 'markers',
      name: 'Prediction',
      marker: { color: 'dodgerblue', size: 6 }
    },
    {
      x: [0, 350],
      y: [0, 350],
      mode: 'lines',
      name: 'Ideal',
      line: { dash: 'dash', color: 'orange' }
    }
  ], {
    xaxis: { title: 'True RUL' },
    yaxis: { title: 'Predicted RUL' },
    margin: { t: 40 }
  });

  // ✅ Heatmap (MAE per unit)
  const unitIds = heatmap.map(r => r[0]);
  const maeVals = heatmap.map(r => r[1]);

  const hasValid = maeVals.some(v => v !== 0 && !isNaN(v));
  const zvals = hasValid ? [maeVals] : [[0.001]];

  Plotly.newPlot('heatmap-plot', [{
    x: hasValid ? unitIds : ['No Data'],
    y: ['MAE'],
    z: zvals,
    type: 'heatmap',
    colorscale: 'RdBu',
    showscale: true
  }], {
    yaxis: { showticklabels: false },
    margin: { t: 30 }
  });
});
