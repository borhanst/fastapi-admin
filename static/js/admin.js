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
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    }
  });

  // Theme presets store
  Alpine.store('themes', {
    current: localStorage.getItem('theme-preset') || 'editorial',

    apply(preset) {
      this.current = preset;
      localStorage.setItem('theme-preset', preset);
      document.documentElement.setAttribute('data-preset', preset);
      window.location.reload();
    },

    init() {
      document.documentElement.setAttribute('data-preset', this.current);
    }
  });

  // Array input component
  Alpine.data('arrayInput', (initialItems = []) => ({
    items: Array.isArray(initialItems) ? [...initialItems] : [],
    add() {
      this.items.push('');
    },
    remove(index) {
      this.items.splice(index, 1);
    }
  }));

  // Slug widget component
  Alpine.data('slugWidget', (sourceField, targetField) => ({
    slug: '',
    manualEdit: false,
    init() {
      const source = document.getElementById(sourceField);
      if (source) {
        source.addEventListener('input', () => {
          if (!this.manualEdit) {
            this.slug = this.generateSlug(source.value);
          }
        });
      }
    },
    generateSlug(text) {
      return text.toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
    },
    onManualEdit(value) {
      this.manualEdit = value.length > 0;
      this.slug = this.generateSlug(value);
    },
    regenerate() {
      const source = document.getElementById(sourceField);
      if (source) {
        this.manualEdit = false;
        this.slug = this.generateSlug(source.value);
      }
    }
  }));

  // Image upload component
  Alpine.data('imageUpload', (existingUrl) => ({
    existingUrl: existingUrl || '',
    previewUrl: '',
    action: existingUrl ? 'keep' : '',
    onFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.previewUrl = URL.createObjectURL(file);
        this.action = 'replace';
      }
    },
    clear() {
      this.previewUrl = '';
      this.existingUrl = '';
      this.action = 'clear';
    }
  }));

  // File upload component
  Alpine.data('fileUpload', (existingUrl) => ({
    existingUrl: existingUrl || '',
    action: existingUrl ? 'keep' : '',
    onFileSelect(event) {
      if (event.target.files[0]) {
        this.action = 'replace';
      }
    },
    clear() {
      this.existingUrl = '';
      this.action = 'clear';
    }
  }));

  // Tag input component
  Alpine.data('tagInput', (initialTags = []) => ({
    tags: Array.isArray(initialTags) ? [...initialTags] : [],
    newTag: '',
    add() {
      if (this.newTag.trim() && !this.tags.includes(this.newTag.trim())) {
        this.tags.push(this.newTag.trim());
        this.newTag = '';
      }
    },
    remove(index) {
      this.tags.splice(index, 1);
    }
  }));

  // Relation picker component
  Alpine.data('relationPicker', (initialId, initialLabel, searchUrl) => ({
    selectedId: initialId || '',
    searchQuery: initialLabel || '',
    results: [],
    open: false,
    search() {
      if (this.searchQuery.length < 1) {
        this.results = [];
        return;
      }
      fetch(searchUrl + '?q=' + encodeURIComponent(this.searchQuery))
        .then(r => r.json())
        .then(data => { this.results = data; this.open = true; });
    },
    select(item) {
      this.selectedId = item.id;
      this.searchQuery = item.label;
      this.open = false;
    },
    clear() {
      this.selectedId = '';
      this.searchQuery = '';
      this.results = [];
    }
  }));

  // Multi-relation component
  Alpine.data('multiRelation', (initialIds = [], searchUrl) => ({
    selectedIds: Array.isArray(initialIds) ? [...initialIds] : [],
    selectedItems: [],
    searchQuery: '',
    results: [],
    open: false,
    search() {
      if (this.searchQuery.length < 1) {
        this.results = [];
        return;
      }
      fetch(searchUrl + '?q=' + encodeURIComponent(this.searchQuery))
        .then(r => r.json())
        .then(data => { this.results = data; this.open = true; });
    },
    add(item) {
      if (!this.selectedIds.includes(item.id)) {
        this.selectedIds.push(item.id);
        this.selectedItems.push(item);
      }
      this.searchQuery = '';
      this.results = [];
      this.open = false;
    },
    remove(index) {
      this.selectedIds.splice(index, 1);
      this.selectedItems.splice(index, 1);
    }
  }));
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
