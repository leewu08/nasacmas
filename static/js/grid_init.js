document.addEventListener('DOMContentLoaded', () => {
  const grid = GridStack.init({
    float: true,
    cellHeight: 80,
    disableOneColumnMode: false,
    resizable: { handles: 'e, se, s, sw, w' },
    draggable: true
  });

  const savedLayout = localStorage.getItem('user_layout');
  let isValid = false;

  if (savedLayout) {
    try {
      const parsed = JSON.parse(savedLayout);
      // id가 없는 항목이 하나라도 있으면 무효
      isValid = parsed.every(item => item.id && typeof item.id === 'string');
      if (isValid) {
        grid.removeAll();
        grid.load(parsed);
        console.log("✅ 사용자 layout 적용됨");
      } else {
        console.warn("⚠️ 유효하지 않은 layout: id 없는 항목 있음. 서버 layout 유지");
      }
    } catch (e) {
      console.warn("⚠️ 저장된 layout 파싱 실패. 서버 layout 유지", e);
    }
  }

  // 드래그/리사이즈 후 저장
  grid.on('change', function (e, items) {
    const layout = grid.save();
    localStorage.setItem('user_layout', JSON.stringify(layout));
    console.log("💾 layout 저장됨:", layout);
  });
});