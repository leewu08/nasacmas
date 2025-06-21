// Performance: Tabulator + Chart.js
document.addEventListener('DOMContentLoaded', () => {
  // Table
  new Tabulator('#perf-table', {
    data: window.PERF_DATA,
    layout:'fitColumns',
    columns:[
      {title:'Scenario', field:'index'},
      {title:'Val MSE', field:'val_mse', formatter:'money', formatterParams:{precision:2}},
      {title:'Test MSE',field:'test_mse',formatter:'money', formatterParams:{precision:2}},
    ],
  });

  // Trend Chart
  const hist = window.HISTORY;
  const labels = Object.keys(hist);
  const trainLoss = labels.map(k=>hist[k].loss);
  const valLoss   = labels.map(k=>hist[k].val_loss);

  new Chart(document.getElementById('perf-trend'), {
    type:'line',
    data:{labels, datasets:[
      { label:'Train Loss', data:trainLoss, fill:false },
      { label:'Val Loss',   data:valLoss,   fill:false }
    ]},
    options:{scales:{y:{beginAtZero:false}}}
  });
});
