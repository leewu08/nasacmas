
document.addEventListener('DOMContentLoaded', () => {
  const sensorSelect = document.getElementById('sensorSelect');
  const ctx = document.getElementById('sensorTrendChart')?.getContext('2d');
  if (!sensorSelect || !ctx) return;

  const renderSensorChart = (sensor, time, values) => {
    if (window.sensorChart) window.sensorChart.destroy();
    window.sensorChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: time,
        datasets: [{
          label: sensor,
          data: values,
          borderColor: 'rgba(75, 192, 192, 1)',
          tension: 0.2
        }]
      }
    });
  };

  const fd = parseInt(sensorSelect.dataset.fd);
  const unit = parseInt(sensorSelect.dataset.unit);

  const fetchAndRender = (sensor) => {
    fetch(`/sensors?fd=${fd}&unit=${unit}`)
      .then(res => res.json())
      .then(data => {
        renderSensorChart(sensor, data.time, data.values[sensor]);
      });
  };

  sensorSelect.addEventListener('change', e => {
    fetchAndRender(e.target.value);
  });

  fetchAndRender(sensorSelect.value);
});