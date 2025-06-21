// Scheduler: FullCalendar 이벤트 등록 only
document.addEventListener('DOMContentLoaded', () => {
  const calendarEl = document.getElementById('calendar');
  const initialEvents = window.CAL_EVENTS || [];

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    events: initialEvents,
    selectable: true,
    select(info) {
      const title = prompt('Event Title:');
      if (title) {
        const evt = { title, start: info.startStr };
        fetch('/schedule/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(evt)
        }).then(() => calendar.addEvent(evt));
      }
      calendar.unselect();
    }
  });

  calendar.render();
});
