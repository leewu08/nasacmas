// Sensors: 시계열 라인 + 이상치 마커
document.getElementById('load-btn').addEventListener('click', () => {
  const unit = document.getElementById('unit').value;
  fetch(`/sensors?unit=${unit}`)
    .then(res=>res.json())
    .then(data=>{
      const times = data.time.map(t=>new Date(t));
      const traces = Object.keys(data.values).map(k => ({
        x: times, y: data.values[k], name: k, mode: 'lines+markers'
      }));
      Plotly.newPlot('sensor-chart', traces, { margin:{t:0} });
    });
});
