// Dashboard: 게이지 + 타임라인 + 슬라이더 초기화
document.addEventListener('DOMContentLoaded', () => {
  const units = window.UNITS_DATA; // Flask에서 `units`를 global로 할당
  const select = document.getElementById('unit-select');
  const gaugeDiv = document.getElementById('gauge-chart');
  const timelineDiv = document.getElementById('rul-timeline');
  const sliderEl = document.getElementById('slider');

  function renderGauge(val) {
    Plotly.newPlot(gaugeDiv, [{
      type: 'indicator', mode: 'gauge+number',
      value: val,
      gauge: {
        axis: { range: [0, 300] },
        bar: { color: val < 50 ? 'red' : val < 100 ? 'yellow' : 'green' }
      }
    }], {margin:{t:0,b:0}});
  }

  function renderTimeline(unit) {
    // 서버로부터 AJAX로 과거 RUL 추이 불러올 수도 있음
    // 여기서는 전역 데이터 예시
    const hist = units.find(u => u.unit === unit).history || [];
    const trace = { x: hist.map(d => new Date(d.time)), y: hist.map(d => d.rul), mode:'lines' };
    Plotly.newPlot(timelineDiv, [trace], {margin:{t:0}});
  }

  // 슬라이더 초기화
  noUiSlider.create(sliderEl, {
    start: [0], range: { min: 0, max: 20 }, step: 1
  }).on('update', ([v]) => {
    // 필요시 타임라인 윈도우 이동 로직
    const unit = parseInt(select.value);
    renderTimeline(unit);
  });

  // 초기 렌더
  renderGauge(units[0].RUL);
  renderTimeline(units[0].unit);

  // 유닛 변경 시
  select.addEventListener('change', () => {
    const u = parseInt(select.value);
    const rec = units.find(x => x.unit === u);
    renderGauge(rec.RUL);
    renderTimeline(u);
  });
});
