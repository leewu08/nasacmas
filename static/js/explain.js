document.addEventListener('DOMContentLoaded', () => {
  const features = window.SHAP_FEATURES;
  const rawVals  = window.SHAP_VALUES;
  const values   = Array.isArray(rawVals[0]) ? rawVals[0] : rawVals;  // 2D 방지

  if (!features || !values) {
    console.error("❌ SHAP data가 없습니다");
    return;
  }

  // ✅ 상위 20개 피쳐 추출
  const indexed = values.map((v, i) => [Math.abs(v), i]);
  indexed.sort((a, b) => b[0] - a[0]);
  const topN     = indexed.slice(0, 20).map(([_, i]) => i);
  const topNames = topN.map(i => features[i]);
  const topVals  = topN.map(i => values[i]);

  // ✅ Bar chart
  Plotly.newPlot('shap-bar', [{
    x: topVals,
    y: topNames,
    type: 'bar',
    orientation: 'h'
  }], {
    margin: { l: 200 }
  });

  // ✅ Force plot (Modal에서)
  const modal = document.getElementById('forceModal');
  modal.addEventListener('shown.bs.modal', () => {
    const target = document.getElementById('force-plot');
    if (!target) {
      console.error("❌ force-plot div 없음");
      return;
    }
    target.innerHTML = ''; // 초기화

    const expl = new shapjs.Decomposition({
      values: values,
      features: features,
      plot_type: 'force'
    });
    expl.render('#force-plot');
  });
});

// ✅ 셀렉트 유닛 변경
function onUnitChange() {
  const unit = document.getElementById('unit-select').value;
  window.location.href = `/explain/${unit}`;
}
