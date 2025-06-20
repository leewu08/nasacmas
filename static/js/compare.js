// Compare: 산점도 + 히트맵
document.addEventListener('DOMContentLoaded', () => {
  const scatter = window.SCATTER_DATA;
  const heatmap = window.HEATMAP_DATA;

  // Scatter
  Plotly.newPlot('scatter-plot', [
    { x: scatter.map(r=>r.y_true), y: scatter.map(r=>r.y_pred),
      mode:'markers', marker:{size:6} },
    { x:[0,300], y:[0,300], mode:'lines', line:{dash:'dash'} }
  ], { xaxis:{title:'True RUL'}, yaxis:{title:'Pred RUL'} });

  // Heatmap
  Plotly.newPlot('heatmap-plot', [{
    x: heatmap.map(r=>r[0]), y:['MAE'],
    z:[heatmap.map(r=>r[1])], type:'heatmap', colorscale:'RdBu'
  }], { yaxis:{showticklabels:false} });
});
