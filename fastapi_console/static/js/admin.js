/* ═══════════════════════════════════════════════════════════════════════════
   FastAPI Admin — Alpine.js Stores & Components
   Warm Editorial Brutalism
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('alpine:init', () => {

  /* ── navGroup (sidebar collapsible sections) ─────────────────────── */

  Alpine.data('navGroup', (tag, defaultCollapsed) => ({
    collapsed: false,

    init() {
      const saved = localStorage.getItem('admin-nav-group:' + tag)
      if (saved !== null) {
        this.collapsed = saved === '1'
      } else {
        this.collapsed = defaultCollapsed
      }
      if (this.$el && this.$el.querySelector('.active')) {
        this.collapsed = false
      }
    },

    toggle() {
      this.collapsed = !this.collapsed
      localStorage.setItem('admin-nav-group:' + tag, this.collapsed ? '1' : '0')
    },
  }))

  /* ── Theme store ─────────────────────────────────────────────────── */

  Alpine.store('theme', {
    dark: JSON.parse(localStorage.getItem('admin_dark_mode') ?? 'false'),

    toggle() {
      this.dark = !this.dark;
      this._apply();
    },

    _apply() {
      localStorage.setItem('admin_dark_mode', JSON.stringify(this.dark));
      document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
    },

    init() {
      this._apply();
    },
  });

  /* ── Relation Picker ─────────────────────────────────────────────── */

  Alpine.data('relationPicker', (initialId, initialLabel, searchUrl) => ({
    selectedId: initialId || '',
    searchQuery: initialLabel || '',
    results: [],
    open: false,
    _debounce: null,

    async search() {
      clearTimeout(this._debounce);
      this._debounce = setTimeout(async () => {
        if (this.searchQuery.length < 1) {
          this.results = [];
          return;
        }
        try {
          const resp = await fetch(`${searchUrl}?q=${encodeURIComponent(this.searchQuery)}`);
          if (resp.ok) {
            this.results = await resp.json();
          }
        } catch (e) {
          console.error('Relation search error:', e);
        }
      }, 250);
    },

    select(result) {
      this.selectedId = result.id;
      this.searchQuery = result.label;
      this.results = [];
      this.open = false;
    },

    clear() {
      this.selectedId = '';
      this.searchQuery = '';
      this.results = [];
    },
  }));

  /* ── Multi-Relation ──────────────────────────────────────────────── */

  Alpine.data('multiRelation', (initialIds, searchUrl) => ({
    selectedIds: initialIds || [],
    selectedItems: [],
    searchQuery: '',
    results: [],
    open: false,
    _debounce: null,

    init() {
      if (this.selectedIds.length > 0) {
        this._loadSelected();
      }
    },

    async _loadSelected() {
      try {
        const ids = Array.isArray(this.selectedIds) ? this.selectedIds : JSON.parse(this.selectedIds);
        const resp = await fetch(`${searchUrl}?ids=${ids.join(',')}`);
        if (resp.ok) {
          this.selectedItems = await resp.json();
        }
      } catch (e) {
        console.error('Multi-relation load error:', e);
      }
    },

    async search() {
      clearTimeout(this._debounce);
      this._debounce = setTimeout(async () => {
        if (this.searchQuery.length < 1) {
          this.results = [];
          return;
        }
        try {
          const resp = await fetch(`${searchUrl}?q=${encodeURIComponent(this.searchQuery)}`);
          if (resp.ok) {
            const all = await resp.json();
            this.results = all.filter(r => !this.selectedIds.includes(r.id));
          }
        } catch (e) {
          console.error('Multi-relation search error:', e);
        }
      }, 250);
    },

    add(result) {
      if (!this.selectedIds.includes(result.id)) {
        this.selectedIds.push(result.id);
        this.selectedItems.push(result);
      }
      this.searchQuery = '';
      this.results = [];
    },

    remove(index) {
      this.selectedIds.splice(index, 1);
      this.selectedItems.splice(index, 1);
    },
  }));

  /* ── Slug Widget ─────────────────────────────────────────────────── */

  Alpine.data('slugWidget', (sourceField, name) => ({
    slug: '',
    manualEdit: false,

    init() {
      const source = document.getElementById(sourceField);
      if (source) {
        source.addEventListener('input', () => {
          if (!this.manualEdit) {
            this.slug = this._toSlug(source.value);
          }
        });
      }
      const input = document.getElementById(name);
      if (input) {
        this.slug = input.value || '';
      }
    },

    onManualEdit(value) {
      this.manualEdit = value.length > 0;
      this.slug = value;
    },

    regenerate() {
      const source = document.getElementById(sourceField);
      if (source) {
        this.slug = this._toSlug(source.value);
        this.manualEdit = false;
      }
    },

    _toSlug(str) {
      return str
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_]+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
    },
  }));

  /* ── Image Upload ────────────────────────────────────────────────── */

  Alpine.data('imageUpload', (existingUrl) => ({
    existingUrl: existingUrl || '',
    previewUrl: '',
    action: existingUrl ? 'keep' : 'none',

    onFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.action = 'replace';
      const reader = new FileReader();
      reader.onload = (e) => {
        this.previewUrl = e.target.result;
      };
      reader.readAsDataURL(file);
    },

    clear() {
      this.previewUrl = '';
      this.existingUrl = '';
      this.action = 'remove';
      const input = this.$refs.fileInput;
      if (input) input.value = '';
    },
  }));

  /* ── File Upload ─────────────────────────────────────────────────── */

  Alpine.data('fileUpload', (existingUrl) => ({
    existingUrl: existingUrl || '',
    fileName: '',
    action: existingUrl ? 'keep' : 'none',

    onFileSelect(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.fileName = file.name;
      this.action = 'replace';
    },

    clear() {
      this.fileName = '';
      this.action = 'remove';
      const input = this.$refs.fileInput;
      if (input) input.value = '';
    },
  }));

  /* ── Tag Input ───────────────────────────────────────────────────── */

  Alpine.data('tagInput', (initialTags) => ({
    tags: initialTags || [],
    newTag: '',

    add() {
      const tag = this.newTag.trim();
      if (tag && !this.tags.includes(tag)) {
        this.tags.push(tag);
      }
      this.newTag = '';
    },

    remove(index) {
      this.tags.splice(index, 1);
    },
  }));

  /* ── Row Selection ─────────────────────────────────────────────── */

  Alpine.data('rowSelect', () => ({
    selected: [],

    isSelected(id) {
      return this.selected.includes(id)
    },

    toggle(id) {
      if (this.isSelected(id)) {
        this.selected = this.selected.filter(i => i !== id)
      } else {
        this.selected.push(id)
      }
    },

    toggleAll() {
      const checkboxes = this.$root.querySelectorAll('input[name="ids[]"]')
      const allIds = Array.from(checkboxes).map(cb => cb.value)
      if (this.selected.length === allIds.length) {
        this.selected = []
      } else {
        this.selected = [...allIds]
      }
    },

    get allSelected() {
      const checkboxes = this.$root.querySelectorAll('input[name="ids[]"]')
      return checkboxes.length > 0 && this.selected.length === checkboxes.length
    },

    get someSelected() {
      return this.selected.length > 0 && !this.allSelected
    },
  }))

  /* ── Delete Confirm Modal ────────────────────────────────────────── */

  Alpine.data('deleteConfirm', () => ({
    open: false,

    openModal() {
      this.open = true
    },

    confirm() {
      this.open = false
      this.$nextTick(() => this.$refs.submitBtn.click())
    },

    cancel() {
      this.open = false
    },
  }))

  /* ── JSON Editor ─────────────────────────────────────────────────── */

  Alpine.data('jsonEditor', (textareaId) => ({
    editor: null,

    init() {
      const textarea = document.getElementById(textareaId);
      if (!textarea) return;

      const container = this.$refs.editorContainer;
      if (!container) return;

      if (typeof CodeMirror !== 'undefined') {
        this.editor = CodeMirror(container, {
          value: textarea.value || '{}',
          mode: 'application/json',
          theme: 'default',
          lineNumbers: true,
          lineWrapping: true,
          tabSize: 2,
          matchBrackets: true,
          autoCloseBrackets: true,
        });

        this.editor.on('change', () => {
          textarea.value = this.editor.getValue();
        });
      } else {
        /* Fallback: plain textarea */
        const fallback = document.createElement('textarea');
        fallback.id = textareaId + '_fallback';
        fallback.name = textarea.name;
        fallback.value = textarea.value;
        fallback.className = 'form-input w-full';
        fallback.style.minHeight = '200px';
        fallback.style.fontFamily = 'var(--font-mono)';
        fallback.style.resize = 'vertical';
        container.appendChild(fallback);
        textarea.type = 'hidden';
      }
    },
  }));

});

/* ── HTMX Loading Bar ────────────────────────────────────────────── */

(function() {
  var loadingBar = document.getElementById('loading-bar');
  if (!loadingBar) return;

  document.addEventListener('htmx:beforeRequest', function(e) {
    loadingBar.style.transform = 'scaleX(0.3)';
    loadingBar.style.transition = 'transform 300ms cubic-bezier(0.16, 1, 0.3, 1)';
  });

  document.addEventListener('htmx:afterRequest', function(e) {
    loadingBar.style.transform = 'scaleX(1)';
    loadingBar.style.transition = 'transform 150ms cubic-bezier(0.4, 0, 1, 1)';
    setTimeout(function() {
      loadingBar.style.transform = 'scaleX(0)';
    }, 150);
  });

  document.addEventListener('htmx:beforeSwap', function(e) {
    loadingBar.style.transform = 'scaleX(0.7)';
  });

  document.addEventListener('htmx:afterSwap', function(e) {
    loadingBar.style.transform = 'scaleX(1)';
    setTimeout(function() {
      loadingBar.style.transform = 'scaleX(0)';
    }, 100);
  });
})();
