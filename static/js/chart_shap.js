document.addEventListener('DOMContentLoaded', () => {
  const listItems = document.querySelectorAll('#shapFeatureList li');
  listItems.forEach(item => {
    item.style.display = 'flex';
    item.style.justifyContent = 'space-between';
    item.style.fontFamily = 'monospace';
  });
});
