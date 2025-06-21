document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('calendar');
  const unitSelect = document.getElementById('unit-select');
  const allEvents = window.UNIT_EVENTS || [];

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    events: allEvents,
    selectable: true,
    select(info) {
      const selectedUnit = unitSelect.value;
      const title = prompt('일정 제목 입력:');

      if (title && selectedUnit !== "all") {
        const evt = {
          title,
          start: info.startStr,
          end: info.endStr, // ✅ 드래그 종료 시점 포함 (FullCalendar 내부에서 exclusive 처리)
          unit: parseInt(selectedUnit)
        };

        fetch('/schedule/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(evt)
        }).then(() => {
          calendar.addEvent(evt);
          allEvents.push(evt);  // ✅ 필터링을 위한 클라이언트 메모리에도 반영
        });
      } else {
        alert("유닛을 먼저 선택하세요!");
      }

      calendar.unselect();
    }
  });

  calendar.render();

  unitSelect.addEventListener('change', e => {
    const selected = e.target.value;
    const filtered = selected === "all"
      ? allEvents
      : allEvents.filter(ev => parseInt(ev.unit) === parseInt(selected));

    calendar.removeAllEvents();
    calendar.addEventSource(filtered);
  });
});
