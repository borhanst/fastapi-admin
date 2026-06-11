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
