/* htmx-config.js — HTMX configuration */
document.addEventListener('htmx:configRequest', function(evt) {
  evt.detail.headers['X-HTMX'] = 'true';
});

// Set default swap style
if (typeof htmx !== 'undefined') {
  htmx.config.defaultSwapStyle = 'innerHTML';
}
