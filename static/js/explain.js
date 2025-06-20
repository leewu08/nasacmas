// Explain: SHAP Bar & Force plot
document.addEventListener('DOMContentLoaded', () => {
  const names = window.SHAP_FEATURES;
  const vals  = window.SHAP_VALUES;

  // SHAP Bar
  Plotly.newPlot('shap-bar', [{
    x: vals, y: names, type:'bar', orientation:'h'
  }], { margin:{l:200} });

  // Force in Modal
  const modal = document.getElementById('forceModal');
  modal.addEventListener('shown.bs.modal', () => {
    const expl = new shapjs.Decomposition({
      values: vals, features: names, plot_type: 'force'
    });
    expl.render('#force-plot');
  });
});
