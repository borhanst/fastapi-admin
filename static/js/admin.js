/* admin.js — Alpine.js stores and components */

// Theme store for dark mode
document.addEventListener('alpine:init', function() {
  Alpine.store('theme', {
    dark: localStorage.getItem('theme') === 'dark',

    toggle() {
      this.dark = !this.dark;
      localStorage.setItem('theme', this.dark ? 'dark' : 'light');
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    },

    init() {
      // Apply stored theme on load
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    }
  });
});

// Initialize flatpickr on date/datetime/time inputs
function initFlatpickr() {
  if (typeof flatpickr === 'undefined') return;

  document.querySelectorAll('input[type="datetime-local"]').forEach(function(el) {
    if (el._flatpickr) return;
    flatpickr(el, {
      enableTime: true,
      dateFormat: 'Y-m-dTH:i',
      time_24hr: true,
      allowInput: true,
      onChange: function(selectedDates, dateStr) {
        el.value = dateStr;
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });

  document.querySelectorAll('input[type="date"]').forEach(function(el) {
    if (el._flatpickr) return;
    flatpickr(el, {
      enableTime: false,
      dateFormat: 'Y-m-d',
      allowInput: true,
      onChange: function(selectedDates, dateStr) {
        el.value = dateStr;
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });

  document.querySelectorAll('input[type="time"]').forEach(function(el) {
    if (el._flatpickr) return;
    flatpickr(el, {
      enableTime: true,
      noCalendar: true,
      dateFormat: 'H:i',
      time_24hr: true,
      allowInput: true,
      onChange: function(selectedDates, dateStr) {
        el.value = dateStr;
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', initFlatpickr);
document.addEventListener('htmx:afterSwap', initFlatpickr);
