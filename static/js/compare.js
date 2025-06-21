document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('calendar');
  const unitSelect = document.getElementById('unit-select');
  const allEvents = window.UNIT_EVENTS || [];

  let calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    events: allEvents,
    selectable: true,
    select(info) {
      const title = prompt('일정 제목 입력:');
      const selectedUnit = unitSelect.value;
      if (title && selectedUnit !== "all") {
        const evt = { title, start: info.startStr, unit: parseInt(selectedUnit) };
        fetch(`/schedule/${evt.unit}/create`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(evt)
        }).then(() => {
          calendar.addEvent(evt);
        });
      } else {
        alert("unit을 먼저 선택하세요!");
      }
      calendar.unselect();
    }
  });

  calendar.render();

  unitSelect.addEventListener('change', e => {
    const selected = e.target.value;
    const filtered = selected === "all"
      ? allEvents
      : allEvents.filter(e => e.unit == selected);
    calendar.removeAllEvents();
    calendar.addEventSource(filtered);
  });
});
