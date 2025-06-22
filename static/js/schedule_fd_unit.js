document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('calendar');
  const fdSelect = document.getElementById('fd-select');
  const unitSelect = document.getElementById('unit-select');

  const allEvents = window.UNIT_EVENTS || [];

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    selectable: true,

    // ✅ 일정 선택 시 생성
    select(info) {
      const fd = fdSelect.value;
      const unit = unitSelect.value;

      if (unit === 'all') {
        alert("⚠️ 유닛을 먼저 선택하세요.");
        calendar.unselect();
        return;
      }

      const title = prompt('📌 일정 제목 입력:');
      if (title) {
        const newEvent = {
          title,
          start: info.startStr,
          end: info.endStr,
          fd: fd === 'all' ? null : parseInt(fd),
          unit: parseInt(unit)
        };

        fetch('/schedule/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newEvent)
        }).then(() => {
          calendar.addEvent({
            ...newEvent,
            extendedProps: {
              fd: newEvent.fd,
              unit: newEvent.unit
            }
          });
          allEvents.push(newEvent); // ✅ 메모리에도 추가
        });
      }

      calendar.unselect();
    },

    // ✅ 일정 클릭 시 수정 or 삭제
    eventClick(info) {
      const event = info.event;
      const newTitle = prompt('✏️ 수정할 제목 입력 (취소 시 삭제)', event.title);

      if (newTitle === null) {
        // ❌ 삭제
        if (confirm("🗑️ 일정을 삭제하시겠습니까?")) {
          fetch('/schedule/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: event.title,
              start: event.startStr,
              fd: parseInt(event.extendedProps.fd),
              unit: parseInt(event.extendedProps.unit)
            })
          }).then(() => {
            event.remove();
            // 🧹 allEvents에서도 제거
            const idx = allEvents.findIndex(e =>
              e.title === event.title &&
              e.start === event.startStr &&
              e.unit === parseInt(event.extendedProps.unit)
            );
            if (idx !== -1) allEvents.splice(idx, 1);
          });
        }
      } else {
        // ✏️ 수정
        fetch('/schedule/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: newTitle,
            start: event.startStr,
            end: event.endStr,
            fd: parseInt(event.extendedProps.fd),
            unit: parseInt(event.extendedProps.unit)
          })
        }).then(() => {
          event.setProp('title', newTitle);
          // 🧠 메모리 내 이벤트도 업데이트
          const evt = allEvents.find(e =>
            e.title === event.title &&
            e.start === event.startStr &&
            e.unit === parseInt(event.extendedProps.unit)
          );
          if (evt) evt.title = newTitle;
        });
      }
    }
  });

  // 🔁 필터링 함수 (FD/Unit 기준)
  function filterEvents() {
    const selectedFd = fdSelect.value;
    const selectedUnit = unitSelect.value;

    const filtered = allEvents.filter(e => {
      const matchFd = selectedFd === 'all' || String(e.fd ?? '') === selectedFd;
      const matchUnit = selectedUnit === 'all' || String(e.unit ?? '') === selectedUnit;
      return matchFd && matchUnit;
    });

    calendar.removeAllEvents();
    calendar.addEventSource(
      filtered.map(e => ({
        ...e,
        extendedProps: {
          fd: e.fd,
          unit: e.unit
        }
      }))
    );
  }

  fdSelect.addEventListener('change', filterEvents);
  unitSelect.addEventListener('change', filterEvents);

  calendar.render();
  filterEvents(); // 초기 필터링 적용
});
