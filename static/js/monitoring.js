console.log(window.UNITS_DATA);

document.addEventListener('DOMContentLoaded', () => {
  const units = window.UNITS_DATA;
  const select = document.getElementById('unit-select');
  const gaugeDiv = document.getElementById('gauge-chart');
  const timelineDiv = document.getElementById('rul-timeline');
  const sliderEl = document.getElementById('slider');
  const fdSelect = document.getElementById('fd-select');
  const clusterSelect = document.getElementById('cluster-select');
  let sliderInitialized = false;

  // ✅ 시나리오 바꿀 때 클러스터 초기화
  if (fdSelect && clusterSelect) {
    fdSelect.addEventListener('change', () => {
      clusterSelect.value = 'all';
      fdSelect.form.submit();
    });
  }

  // 🟢 게이지 렌더
  function renderGauge(val) {
    if (val === undefined || val === null || isNaN(val)) {
      console.warn("⚠️ RUL 값이 NaN이거나 없음:", val);
      val = 0;
    }
    Plotly.react(gaugeDiv, [{
      type: 'indicator',
      mode: 'gauge+number',
      value: val,
      gauge: {
        axis: { range: [0, 300] },
        bar: {
          color: val < 50 ? 'red'
               : val < 100 ? 'yellow'
               : 'green'
        }
      }
    }], { margin: { t: 0, b: 0 } });
  }

  // 🟢 타임라인 렌더
  function renderTimeline(hist, idx) {
    if (!hist || !hist[idx] || hist.length === 0 || isNaN(hist[idx].rul)) {
      console.warn("⚠️ 유효하지 않은 히스토리 인덱스:", idx, hist[idx]);
      return;
    }
    const x = hist.map(d => new Date(d.time));
    const y = hist.map(d => d.rul);
    Plotly.react(timelineDiv, [{ x, y, mode: 'lines' }], { margin: { t: 0 } });
    renderGauge(y[idx]);
  }

  // 🟢 슬라이더 설정
  function setupSlider(histLength, initialIdx) {
    const maxIdx = Math.max(histLength - 1, 0);
    if (sliderInitialized) {
      sliderEl.noUiSlider.updateOptions({
        range: { min: 0, max: maxIdx },
        start: [initialIdx]
      });
      return;
    }
    noUiSlider.create(sliderEl, {
      start: [initialIdx],
      range: { min: 0, max: maxIdx },
      step: 1,
      tooltips: true
    }).on('update', ([value]) => {
      const idx = parseInt(value, 10);
      const rec = units.find(u => String(u.unit) === select.value);
      if (rec && Array.isArray(rec.history)) {
        const modified = { ...rec.history[idx], torque: rec.history[idx].torque * 1.1 };

        fetch('/predict_rul', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(modified)
        })
        .then(r => r.json())
        .then(data => {
          renderGauge(data.rul);
          renderTimeline(rec.history, idx);
        });
      }
    });
    sliderInitialized = true;
  }

  // 🟢 유닛 렌더링
  function renderForUnit(unitId) {
    const rec = units.find(u => String(u.unit) === String(unitId));
    if (!rec) return;
    const rulValue = Number(rec.predicted_rul ?? rec.RUL ?? 0);
    renderGauge(rulValue);
    const hist = rec.history || [];
    renderTimeline(hist, 0);
    setupSlider(hist.length, 0);  // ✅ hist.length 그대로 전달, 내부에서 -1 처리함
  }

  // 🔵 최초 렌더링
  if (units.length) {
    select.value = String(units[0].unit);
    renderForUnit(select.value);
  }

  // 🔵 유닛 변경 시 렌더
  select.addEventListener('change', () => {
    renderForUnit(select.value);
  });

  // 🔵 실시간 데이터 갱신
  function fetchRealTimeData() {
    fetch('/get_real_time_data')
      .then(r => r.json())
      .then(data => {
        if (String(data.unit) === select.value) {
          renderGauge(data.RUL);
          if (Array.isArray(data.history)) {
            renderTimeline(data.history, 0);
            setupSlider(data.history.length, 0);
          }
        }
      })
      .catch(e => console.error('실시간 데이터 오류:', e));
  }

  setInterval(fetchRealTimeData, 10000);
});
