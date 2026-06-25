/* htmx-config.js — HTMX configuration */
document.addEventListener('htmx:configRequest', function(evt) {
  evt.detail.headers['X-HTMX'] = 'true';

  var meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) {
    evt.detail.headers['X-CSRF-Token'] = meta.getAttribute('content');
  }
});

// Set default swap style
if (typeof htmx !== 'undefined') {
  htmx.config.defaultSwapStyle = 'innerHTML';
}
