/**
 * Dr. Health — hierarchical health hub.
 *
 * Renders a card menu of every health data section, then drills down into a
 * dedicated sub-page per section with a sticky header and inline add/edit.
 *
 * Deliberately avoids optional chaining (?.) and nullish coalescing (??) so it
 * parses on older Android WebView / Chrome builds.
 */
(function () {
    'use strict';

    // ---------- Field schemas ----------
    // `type` drives the editor widget: text | textarea | date | select | list
    const LIST_SECTIONS = {
        conditions: {
            title: 'Conditions',
            icon: 'fa-notes-medical',
            desc: 'Diagnoses and ongoing issues',
            primary: 'name',
            fields: [
                { key: 'name', label: 'Condition', type: 'text', required: true },
                { key: 'status', label: 'Status', type: 'select', options: ['active', 'investigating', 'resolved'] },
                { key: 'diagnosed_date', label: 'Diagnosed', type: 'date' },
                { key: 'details', label: 'Details', type: 'textarea' }
            ]
        },
        symptoms: {
            title: 'Symptoms',
            icon: 'fa-head-side-cough',
            desc: 'What you have been feeling',
            primary: 'description',
            fields: [
                { key: 'description', label: 'Symptom', type: 'text', required: true },
                { key: 'severity', label: 'Severity', type: 'select', options: ['mild', 'moderate', 'severe'] },
                { key: 'frequency', label: 'Frequency', type: 'text' },
                { key: 'onset', label: 'Started', type: 'text' },
                { key: 'triggers', label: 'Triggers (one per line)', type: 'list' }
            ]
        },
        medications: {
            title: 'Medications',
            icon: 'fa-pills',
            desc: 'Prescribed drugs and doses',
            primary: 'name',
            fields: [
                { key: 'name', label: 'Medication', type: 'text', required: true },
                { key: 'dose', label: 'Dose', type: 'text' },
                { key: 'frequency', label: 'Frequency', type: 'text' },
                { key: 'purpose', label: 'Purpose', type: 'text' },
                { key: 'prescribed_date', label: 'Prescribed', type: 'date' }
            ]
        },
        supplements: {
            title: 'Supplements',
            icon: 'fa-leaf',
            desc: 'Vitamins, herbs and minerals',
            primary: 'name',
            fields: [
                { key: 'name', label: 'Supplement', type: 'text', required: true },
                { key: 'dose', label: 'Dose', type: 'text' },
                { key: 'frequency', label: 'Frequency', type: 'text' },
                { key: 'purpose', label: 'Purpose', type: 'text' },
                { key: 'prescribed_date', label: 'Started', type: 'date' }
            ]
        },
        test_results: {
            title: 'Lab & Test Results',
            icon: 'fa-flask-vial',
            desc: 'Blood work and other measurements',
            primary: 'test_name',
            grouped: true,
            fields: [
                { key: 'test_name', label: 'Test name', type: 'text', required: true },
                { key: 'value', label: 'Value', type: 'text' },
                { key: 'reference_range', label: 'Reference range', type: 'text' },
                { key: 'date', label: 'Date', type: 'date' },
                { key: 'notes', label: 'Notes', type: 'textarea' }
            ]
        },
        action_plans: {
            title: 'Action Plans',
            icon: 'fa-list-check',
            desc: 'What you are working on',
            primary: 'title',
            fields: [
                { key: 'title', label: 'Plan', type: 'text', required: true },
                { key: 'steps', label: 'Steps (one per line)', type: 'list' },
                { key: 'status', label: 'Status', type: 'select', options: ['active', 'completed', 'paused'] },
                { key: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high'] }
            ]
        },
        follow_ups: {
            title: 'Follow-ups',
            icon: 'fa-calendar-check',
            desc: 'Things to chase up',
            primary: 'title',
            fields: [
                { key: 'title', label: 'Follow-up', type: 'text', required: true },
                { key: 'steps', label: 'Steps (one per line)', type: 'list' },
                { key: 'due_date', label: 'Due', type: 'date' },
                { key: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high'] }
            ]
        },
        questions_for_doctor: {
            title: 'Questions for Doctor',
            icon: 'fa-circle-question',
            desc: 'Ask these at your next visit',
            primary: 'question',
            fields: [
                { key: 'question', label: 'Question', type: 'textarea', required: true },
                { key: 'context', label: 'Why you are asking', type: 'textarea' },
                { key: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high'] }
            ]
        },
        provider_notes: {
            title: 'Provider Notes',
            icon: 'fa-user-doctor',
            desc: 'What your clinicians told you',
            primary: 'note',
            fields: [
                { key: 'provider', label: 'Provider', type: 'text' },
                { key: 'note', label: 'Note', type: 'textarea', required: true },
                { key: 'date', label: 'Date', type: 'date' }
            ]
        },
        conversation_insights: {
            title: 'Insights',
            icon: 'fa-lightbulb',
            desc: 'Learned from your conversations',
            primary: 'insight',
            fields: [
                { key: 'insight', label: 'Insight', type: 'textarea', required: true },
                { key: 'category', label: 'Category', type: 'text' }
            ]
        }
    };

    const OBJECT_SECTIONS = {
        personal: {
            title: 'Personal Details',
            icon: 'fa-id-card',
            desc: 'Age, gender, blood type',
            fields: [
                { key: 'age', label: 'Age', type: 'text' },
                { key: 'gender', label: 'Gender', type: 'text' },
                { key: 'location', label: 'Location', type: 'text' },
                { key: 'blood_type', label: 'Blood type', type: 'text' }
            ]
        },
        diet: {
            title: 'Diet',
            icon: 'fa-utensils',
            desc: 'Preferences and restrictions',
            fields: [
                { key: 'preferences', label: 'Preferences', type: 'list' },
                { key: 'restrictions', label: 'Restrictions', type: 'list' },
                { key: 'daily_foods', label: 'Daily foods', type: 'list' },
                { key: 'cooking_methods', label: 'Cooking methods', type: 'list' },
                { key: 'notes', label: 'Notes', type: 'list' }
            ]
        },
        lifestyle: {
            title: 'Lifestyle',
            icon: 'fa-person-running',
            desc: 'Exercise, sleep, stress, habits',
            fields: [
                { key: 'exercise', label: 'Exercise', type: 'list' },
                { key: 'stress_factors', label: 'Stress factors', type: 'list' },
                { key: 'habits', label: 'Habits', type: 'list' }
            ]
        }
    };

    const GROUPS = [
        {
            group: 'Emergency & Identity',
            items: [
                { id: 'vitals', kind: 'vitals', title: 'Emergency Card', icon: 'fa-kit-medical', desc: 'Shown to paramedics offline' },
                { id: 'personal', kind: 'object', title: 'Personal Details', icon: 'fa-id-card' }
            ]
        },
        {
            group: 'Medical Record',
            items: [
                { id: 'conditions', kind: 'list' },
                { id: 'symptoms', kind: 'list' },
                { id: 'medications', kind: 'list' },
                { id: 'supplements', kind: 'list' },
                { id: 'test_results', kind: 'list' }
            ]
        },
        {
            group: 'Lifestyle',
            items: [
                { id: 'diet', kind: 'object' },
                { id: 'lifestyle', kind: 'object' }
            ]
        },
        {
            group: 'Plans & Care Team',
            items: [
                { id: 'action_plans', kind: 'list' },
                { id: 'follow_ups', kind: 'list' },
                { id: 'questions_for_doctor', kind: 'list' },
                { id: 'provider_notes', kind: 'list' },
                { id: 'conversation_insights', kind: 'list' }
            ]
        },
        {
            group: 'Tools',
            items: [
                { id: 'interactions', kind: 'interactions', title: 'Drug Interactions', icon: 'fa-triangle-exclamation', desc: 'Check meds and supplements' },
                { id: 'ai_summary', kind: 'summary', title: 'What the AI Sees', icon: 'fa-robot', desc: 'Your health context' },
                { id: 'settings', kind: 'settings', title: 'Settings', icon: 'fa-gear', desc: 'Upload retention' }
            ]
        }
    ];

    // ---------- Helpers ----------
    function esc(value) {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function meta(id) {
        if (LIST_SECTIONS[id]) return LIST_SECTIONS[id];
        if (OBJECT_SECTIONS[id]) return OBJECT_SECTIONS[id];
        return null;
    }

    function toText(value) {
        if (value === null || value === undefined) return '';
        if (Array.isArray(value)) return value.map(toText).filter(Boolean).join(', ');
        if (typeof value === 'object') {
            const parts = [];
            for (const k in value) {
                if (Object.prototype.hasOwnProperty.call(value, k)) {
                    parts.push(k.replace(/_/g, ' ') + ': ' + toText(value[k]));
                }
            }
            return parts.join('; ');
        }
        return String(value);
    }

    function labelFor(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    }

    const HIDDEN_KEYS = ['added_at', 'updated_at', 'source', 'id'];

    function itemTitle(sectionId, item) {
        const schema = LIST_SECTIONS[sectionId];
        if (schema && schema.primary && item[schema.primary]) return toText(item[schema.primary]);
        for (const k in item) {
            if (HIDDEN_KEYS.indexOf(k) === -1 && item[k]) return toText(item[k]);
        }
        return '(untitled)';
    }

    function itemSubtitle(sectionId, item) {
        const schema = LIST_SECTIONS[sectionId];
        if (!schema) return '';
        const bits = [];
        for (let i = 0; i < schema.fields.length; i++) {
            const f = schema.fields[i];
            if (f.key === schema.primary) continue;
            const v = toText(item[f.key]);
            if (v) bits.push(v);
            if (bits.length >= 2) break;
        }
        return bits.join(' · ');
    }

    // ---------- Module ----------
    const DrHealthHub = {
        profile: null,
        root: null,
        route: { view: 'index', section: null },
        openIndex: null,
        editIndex: null,
        adding: false,
        filter: '',
        busy: false,

        init(rootEl) {
            this.root = rootEl;
            this.render();
        },

        setProfile(profile) {
            this.profile = profile;
            if (this.root) this.render();
        },

        async reload() {
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile');
                const data = await resp.json();
                if (data && data.profile) this.profile = data.profile;
            } catch (e) {
                /* keep previous profile on network failure */
            }
            this.render();
        },

        go(view, section) {
            this.route = { view: view, section: section || null };
            this.openIndex = null;
            this.editIndex = null;
            this.adding = false;
            this.filter = '';
            this.render();
            const scroller = this.root ? this.root.querySelector('.hub-scroll') : null;
            if (scroller) scroller.scrollTop = 0;
        },

        count(id) {
            if (!this.profile) return null;
            if (LIST_SECTIONS[id]) {
                const arr = this.profile[id];
                return Array.isArray(arr) ? arr.length : 0;
            }
            if (OBJECT_SECTIONS[id]) {
                const obj = this.profile[id] || {};
                let filled = 0;
                const fields = OBJECT_SECTIONS[id].fields;
                for (let i = 0; i < fields.length; i++) {
                    const v = obj[fields[i].key];
                    if (Array.isArray(v) ? v.length : (v !== null && v !== undefined && v !== '')) filled++;
                }
                return filled;
            }
            return null;
        },

        // ---------- Rendering ----------
        render() {
            if (!this.root) return;
            if (this.route.view === 'index') {
                this.root.innerHTML = this.indexHtml();
                this.wireIndex();
            } else {
                this.root.innerHTML = this.sectionHtml(this.route.section);
                this.wireSection(this.route.section);
            }
        },

        indexHtml() {
            const name = this.profile && this.profile.name ? this.profile.name : 'Your health record';
            let html = '';
            html += '<div class="hub-subheader">';
            html += '<div class="hub-sub-title"><i class="fas fa-clipboard-list"></i> Health</div>';
            html += '<button class="hub-icon-btn" id="hub-refresh" title="Refresh"><i class="fas fa-rotate"></i></button>';
            html += '</div>';
            html += '<div class="hub-scroll">';
            html += '<div class="hub-hero"><div class="hub-hero-name">' + esc(name) + '</div>';
            html += '<div class="hub-hero-sub">Tap a section to view or edit</div></div>';

            for (let g = 0; g < GROUPS.length; g++) {
                const grp = GROUPS[g];
                html += '<div class="hub-group-label">' + esc(grp.group) + '</div>';
                html += '<div class="hub-cards">';
                for (let i = 0; i < grp.items.length; i++) {
                    const entry = grp.items[i];
                    const m = meta(entry.id);
                    const title = entry.title || (m ? m.title : labelFor(entry.id));
                    const icon = entry.icon || (m ? m.icon : 'fa-circle');
                    const desc = entry.desc || (m ? m.desc : '');
                    const n = this.count(entry.id);
                    html += '<button class="hub-card" data-section="' + esc(entry.id) + '">';
                    html += '<span class="hub-card-icon"><i class="fas ' + esc(icon) + '"></i></span>';
                    html += '<span class="hub-card-body">';
                    html += '<span class="hub-card-title">' + esc(title) + '</span>';
                    html += '<span class="hub-card-desc">' + esc(desc) + '</span>';
                    html += '</span>';
                    if (n !== null) {
                        html += '<span class="hub-badge' + (n ? '' : ' empty') + '">' + n + '</span>';
                    }
                    html += '<i class="fas fa-chevron-right hub-chevron"></i>';
                    html += '</button>';
                }
                html += '</div>';
            }
            html += '</div>';
            return html;
        },

        wireIndex() {
            const self = this;
            const cards = this.root.querySelectorAll('.hub-card');
            for (let i = 0; i < cards.length; i++) {
                cards[i].addEventListener('click', function () {
                    const id = this.getAttribute('data-section');
                    const kind = self.kindOf(id);
                    self.go(kind, id);
                });
            }
            const refresh = this.root.querySelector('#hub-refresh');
            if (refresh) {
                refresh.addEventListener('click', () => {
                    refresh.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                    self.reload();
                });
            }
        },

        kindOf(id) {
            for (let g = 0; g < GROUPS.length; g++) {
                for (let i = 0; i < GROUPS[g].items.length; i++) {
                    if (GROUPS[g].items[i].id === id) return GROUPS[g].items[i].kind;
                }
            }
            return 'list';
        },

        sectionHtml(id) {
            const kind = this.kindOf(id);
            const entry = this.entryOf(id);
            const m = meta(id);
            const title = (entry && entry.title) || (m ? m.title : labelFor(id));
            const icon = (entry && entry.icon) || (m ? m.icon : 'fa-circle');

            let html = '';
            html += '<div class="hub-subheader">';
            html += '<button class="hub-icon-btn" id="hub-back" title="Back"><i class="fas fa-chevron-left"></i></button>';
            html += '<div class="hub-sub-title"><i class="fas ' + esc(icon) + '"></i> ' + esc(title) + '</div>';
            if (kind === 'list') {
                html += '<button class="hub-icon-btn primary" id="hub-add" title="Add"><i class="fas fa-plus"></i></button>';
            } else {
                html += '<span class="hub-icon-spacer"></span>';
            }
            html += '</div>';

            if (kind === 'list') {
                const arr = (this.profile && Array.isArray(this.profile[id])) ? this.profile[id] : [];
                if (arr.length > 6) {
                    html += '<div class="hub-filterbar"><input type="search" id="hub-filter" placeholder="Filter ' +
                        esc(String(title).toLowerCase()) + '" value="' + esc(this.filter) + '"></div>';
                }
            }

            html += '<div class="hub-scroll">';
            if (kind === 'list') html += this.listBody(id);
            else if (kind === 'object') html += this.objectBody(id);
            else if (kind === 'vitals') html += this.vitalsBody();
            else if (kind === 'interactions') html += '<div id="hub-tool" class="hub-tool"><em>Checking…</em></div>';
            else if (kind === 'summary') html += '<div id="hub-tool" class="hub-tool"><em>Loading…</em></div>';
            else if (kind === 'settings') html += this.settingsBody();
            html += '</div>';
            html += '<div class="hub-status" id="hub-status"></div>';
            return html;
        },

        entryOf(id) {
            for (let g = 0; g < GROUPS.length; g++) {
                for (let i = 0; i < GROUPS[g].items.length; i++) {
                    if (GROUPS[g].items[i].id === id) return GROUPS[g].items[i];
                }
            }
            return null;
        },

        // ---------- List sections ----------
        listBody(id) {
            const schema = LIST_SECTIONS[id];
            const arr = (this.profile && Array.isArray(this.profile[id])) ? this.profile[id] : [];
            let html = '';

            if (this.adding) html += this.formHtml(id, {}, -1);

            const rows = [];
            for (let i = 0; i < arr.length; i++) {
                const item = arr[i] || {};
                if (this.filter) {
                    const hay = JSON.stringify(item).toLowerCase();
                    if (hay.indexOf(this.filter.toLowerCase()) === -1) continue;
                }
                rows.push({ item: item, index: i });
            }

            if (!rows.length && this.adding) {
                return html;
            }

            if (!rows.length) {
                html += '<div class="hub-empty"><i class="fas ' + esc(schema.icon) + '"></i>';
                html += '<p>Nothing recorded yet.</p>';
                html += '<button class="hub-btn primary" id="hub-empty-add"><i class="fas fa-plus"></i> Add ' +
                    esc(this.singular(schema.title)) + '</button></div>';
                return html;
            }

            if (schema.grouped) {
                html += this.groupedRows(id, rows);
            } else {
                for (let r = 0; r < rows.length; r++) {
                    html += this.rowHtml(id, rows[r].item, rows[r].index);
                }
            }
            return html;
        },

        singular(title) {
            return String(title).replace(/s$/, '').toLowerCase();
        },

        groupedRows(id, rows) {
            const schema = LIST_SECTIONS[id];
            const buckets = {};
            const order = [];
            for (let r = 0; r < rows.length; r++) {
                const key = toText(rows[r].item[schema.primary]) || '(unnamed)';
                if (!buckets[key]) { buckets[key] = []; order.push(key); }
                buckets[key].push(rows[r]);
            }
            order.sort((a, b) => a.localeCompare(b));

            let html = '';
            for (let i = 0; i < order.length; i++) {
                const key = order[i];
                const group = buckets[key];
                group.sort((a, b) => String(b.item.date || '').localeCompare(String(a.item.date || '')));
                const latest = group[0].item;
                html += '<div class="hub-tgroup">';
                html += '<div class="hub-tgroup-head">';
                html += '<span class="hub-tgroup-name">' + esc(key) + '</span>';
                html += '<span class="hub-tgroup-latest">' + esc(toText(latest.value)) + '</span>';
                html += '<span class="hub-tgroup-count">' + group.length + '</span>';
                html += '</div>';
                for (let j = 0; j < group.length; j++) {
                    html += this.rowHtml(id, group[j].item, group[j].index, true);
                }
                html += '</div>';
            }
            return html;
        },

        rowHtml(id, item, index, compact) {
            const open = this.openIndex === index;
            const editing = this.editIndex === index;
            if (editing) return this.formHtml(id, item, index);

            const schema = LIST_SECTIONS[id];
            let html = '<div class="hub-row' + (open ? ' open' : '') + '" data-index="' + index + '">';
            html += '<button class="hub-row-head" data-toggle="' + index + '">';
            html += '<span class="hub-row-main">';
            if (compact) {
                html += '<span class="hub-row-title">' + esc(toText(item.date) || 'No date') + '</span>';
                html += '<span class="hub-row-sub">' + esc(toText(item.value)) +
                    (item.reference_range ? ' · ref ' + esc(toText(item.reference_range)) : '') + '</span>';
            } else {
                html += '<span class="hub-row-title">' + esc(itemTitle(id, item)) + '</span>';
                const sub = itemSubtitle(id, item);
                if (sub) html += '<span class="hub-row-sub">' + esc(sub) + '</span>';
            }
            html += '</span>';
            if (item.status) {
                html += '<span class="hub-pill ' + esc(String(item.status)) + '">' + esc(item.status) + '</span>';
            }
            html += '<i class="fas fa-chevron-' + (open ? 'up' : 'down') + ' hub-chevron"></i>';
            html += '</button>';

            if (open) {
                html += '<div class="hub-row-body">';
                const seen = {};
                for (let i = 0; i < schema.fields.length; i++) {
                    const f = schema.fields[i];
                    seen[f.key] = true;
                    const v = toText(item[f.key]);
                    if (!v) continue;
                    html += '<div class="hub-field"><span class="hub-field-label">' + esc(f.label) +
                        '</span><span class="hub-field-value">' + esc(v) + '</span></div>';
                }
                for (const k in item) {
                    if (!Object.prototype.hasOwnProperty.call(item, k)) continue;
                    if (seen[k] || HIDDEN_KEYS.indexOf(k) !== -1) continue;
                    const v = toText(item[k]);
                    if (!v) continue;
                    html += '<div class="hub-field"><span class="hub-field-label">' + esc(labelFor(k)) +
                        '</span><span class="hub-field-value">' + esc(v) + '</span></div>';
                }
                if (item.added_at) {
                    html += '<div class="hub-added">Recorded ' + esc(String(item.added_at).slice(0, 10)) + '</div>';
                }
                html += '<div class="hub-row-actions">';
                html += '<button class="hub-btn" data-edit="' + index + '"><i class="fas fa-pen"></i> Edit</button>';
                html += '<button class="hub-btn danger" data-delete="' + index + '"><i class="fas fa-trash"></i> Delete</button>';
                html += '</div></div>';
            }
            html += '</div>';
            return html;
        },

        formHtml(id, item, index) {
            const schema = LIST_SECTIONS[id];
            const isNew = index === -1;
            let html = '<div class="hub-form" data-index="' + index + '">';
            html += '<div class="hub-form-title">' + (isNew ? 'Add ' : 'Edit ') + esc(this.singular(schema.title)) + '</div>';
            for (let i = 0; i < schema.fields.length; i++) {
                html += this.inputHtml(schema.fields[i], item[schema.fields[i].key]);
            }
            html += '<div class="hub-row-actions">';
            html += '<button class="hub-btn primary" data-save="' + index + '"><i class="fas fa-check"></i> Save</button>';
            html += '<button class="hub-btn" data-cancel="1">Cancel</button>';
            html += '</div></div>';
            return html;
        },

        inputHtml(field, value) {
            const id = 'hf-' + field.key;
            let html = '<label class="hub-input-label" for="' + id + '">' + esc(field.label) +
                (field.required ? ' *' : '') + '</label>';
            if (field.type === 'textarea') {
                html += '<textarea class="hub-input" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="textarea" rows="3">' + esc(toText(value)) + '</textarea>';
            } else if (field.type === 'list') {
                const lines = Array.isArray(value) ? value.map(toText).join('\n') : toText(value);
                html += '<textarea class="hub-input" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="list" rows="4">' + esc(lines) + '</textarea>';
            } else if (field.type === 'select') {
                html += '<select class="hub-input" id="' + id + '" data-key="' + esc(field.key) + '" data-type="text">';
                html += '<option value=""></option>';
                for (let i = 0; i < field.options.length; i++) {
                    const opt = field.options[i];
                    const sel = String(value || '') === opt ? ' selected' : '';
                    html += '<option value="' + esc(opt) + '"' + sel + '>' + esc(opt) + '</option>';
                }
                html += '</select>';
            } else {
                const t = field.type === 'date' ? 'date' : 'text';
                html += '<input class="hub-input" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="text" type="' + t + '" value="' + esc(toText(value)) + '">';
            }
            return html;
        },

        readForm(formEl) {
            const out = {};
            const inputs = formEl.querySelectorAll('[data-key]');
            for (let i = 0; i < inputs.length; i++) {
                const el = inputs[i];
                const key = el.getAttribute('data-key');
                const type = el.getAttribute('data-type');
                const raw = el.value;
                if (type === 'list') {
                    const lines = String(raw || '').split('\n');
                    const clean = [];
                    for (let j = 0; j < lines.length; j++) {
                        const t = lines[j].trim();
                        if (t) clean.push(t);
                    }
                    out[key] = clean;
                } else {
                    out[key] = String(raw || '').trim();
                }
            }
            return out;
        },

        // ---------- Object sections ----------
        objectBody(id) {
            const schema = OBJECT_SECTIONS[id];
            const obj = (this.profile && this.profile[id]) ? this.profile[id] : {};
            let html = '<div class="hub-form" data-object="' + esc(id) + '">';
            html += '<div class="hub-form-hint">Changes save straight to your record.</div>';
            for (let i = 0; i < schema.fields.length; i++) {
                html += this.inputHtml(schema.fields[i], obj[schema.fields[i].key]);
            }
            html += '<div class="hub-row-actions">';
            html += '<button class="hub-btn primary" id="hub-obj-save"><i class="fas fa-check"></i> Save</button>';
            html += '</div></div>';

            if (id === 'lifestyle') {
                const sleep = obj.sleep || {};
                const sleepText = toText(sleep);
                if (sleepText) {
                    html += '<div class="hub-note"><strong>Sleep</strong><br>' + esc(sleepText) + '</div>';
                }
            }
            return html;
        },

        // ---------- Vitals ----------
        vitalsBody() {
            let html = '<div class="hub-note">';
            html += 'Your emergency card is stored on this phone so it works without internet.';
            html += '</div>';
            html += '<div class="hub-row-actions" style="padding:0 14px;">';
            html += '<button class="hub-btn primary" id="hub-open-vitals"><i class="fas fa-kit-medical"></i> Open emergency card</button>';
            html += '</div>';
            return html;
        },

        // ---------- Settings ----------
        settingsBody() {
            const settings = (this.profile && this.profile.upload_settings) ? this.profile.upload_settings : {};
            const days = settings.retention_days ? settings.retention_days : 365;
            let html = '<div class="hub-form">';
            html += '<label class="hub-input-label" for="hub-retention">Keep uploaded documents for (days)</label>';
            html += '<input class="hub-input" id="hub-retention" type="number" min="1" max="3650" value="' + esc(days) + '">';
            html += '<div class="hub-row-actions"><button class="hub-btn primary" id="hub-settings-save"><i class="fas fa-check"></i> Save</button></div>';
            html += '</div>';
            const docs = (this.profile && Array.isArray(this.profile.uploaded_documents)) ? this.profile.uploaded_documents : [];
            html += '<div class="hub-note"><strong>' + docs.length + '</strong> document(s) currently stored.</div>';
            return html;
        },

        // ---------- Wiring ----------
        wireSection(id) {
            const self = this;
            const kind = this.kindOf(id);

            const back = this.root.querySelector('#hub-back');
            if (back) back.addEventListener('click', () => self.go('index'));

            const filter = this.root.querySelector('#hub-filter');
            if (filter) {
                filter.addEventListener('input', function () {
                    self.filter = this.value;
                    const scroller = self.root.querySelector('.hub-scroll');
                    if (scroller) scroller.innerHTML = self.listBody(id);
                    self.wireList(id);
                });
            }

            if (kind === 'list') {
                const add = this.root.querySelector('#hub-add');
                if (add) {
                    add.addEventListener('click', () => {
                        self.adding = true;
                        self.openIndex = null;
                        self.editIndex = null;
                        self.render();
                    });
                }
                this.wireList(id);
            } else if (kind === 'object') {
                const save = this.root.querySelector('#hub-obj-save');
                if (save) save.addEventListener('click', () => self.saveObject(id));
            } else if (kind === 'vitals') {
                const open = this.root.querySelector('#hub-open-vitals');
                if (open) {
                    open.addEventListener('click', () => {
                        if (typeof window.openEmergency === 'function') window.openEmergency();
                    });
                }
            } else if (kind === 'interactions') {
                this.loadInteractions();
            } else if (kind === 'summary') {
                this.loadSummary();
            } else if (kind === 'settings') {
                const save = this.root.querySelector('#hub-settings-save');
                if (save) save.addEventListener('click', () => self.saveSettings());
            }
        },

        wireList(id) {
            const self = this;
            const root = this.root;

            const emptyAdd = root.querySelector('#hub-empty-add');
            if (emptyAdd) {
                emptyAdd.addEventListener('click', () => {
                    self.adding = true;
                    self.render();
                });
            }

            const toggles = root.querySelectorAll('[data-toggle]');
            for (let i = 0; i < toggles.length; i++) {
                toggles[i].addEventListener('click', function () {
                    const idx = parseInt(this.getAttribute('data-toggle'), 10);
                    self.openIndex = self.openIndex === idx ? null : idx;
                    self.editIndex = null;
                    self.render();
                });
            }

            const edits = root.querySelectorAll('[data-edit]');
            for (let i = 0; i < edits.length; i++) {
                edits[i].addEventListener('click', function () {
                    self.editIndex = parseInt(this.getAttribute('data-edit'), 10);
                    self.adding = false;
                    self.render();
                });
            }

            const dels = root.querySelectorAll('[data-delete]');
            for (let i = 0; i < dels.length; i++) {
                dels[i].addEventListener('click', function () {
                    const idx = parseInt(this.getAttribute('data-delete'), 10);
                    self.deleteItem(id, idx);
                });
            }

            const cancels = root.querySelectorAll('[data-cancel]');
            for (let i = 0; i < cancels.length; i++) {
                cancels[i].addEventListener('click', () => {
                    self.adding = false;
                    self.editIndex = null;
                    self.render();
                });
            }

            const saves = root.querySelectorAll('[data-save]');
            for (let i = 0; i < saves.length; i++) {
                saves[i].addEventListener('click', function () {
                    const idx = parseInt(this.getAttribute('data-save'), 10);
                    const form = this.closest('.hub-form');
                    if (form) self.saveItem(id, idx, form);
                });
            }
        },

        status(text, isError) {
            const el = this.root ? this.root.querySelector('#hub-status') : null;
            if (!el) return;
            el.textContent = text || '';
            el.className = 'hub-status' + (isError ? ' error' : '') + (text ? ' show' : '');
        },

        // ---------- Persistence ----------
        async saveItem(id, index, formEl) {
            if (this.busy) return;
            const schema = LIST_SECTIONS[id];
            const values = this.readForm(formEl);

            for (let i = 0; i < schema.fields.length; i++) {
                const f = schema.fields[i];
                if (f.required) {
                    const v = values[f.key];
                    const empty = Array.isArray(v) ? !v.length : !v;
                    if (empty) {
                        this.status(f.label + ' is required.', true);
                        return;
                    }
                }
            }

            this.busy = true;
            this.status('Saving…');
            try {
                const isNew = index === -1;
                const body = isNew
                    ? { category: id, item: values }
                    : { category: id, index: index, updates: values };
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                    method: isNew ? 'POST' : 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not save.', true);
                    this.busy = false;
                    return;
                }
                if (data.profile) this.profile = data.profile;
                this.adding = false;
                this.editIndex = null;
                this.openIndex = null;
                this.busy = false;
                this.render();
                this.status('Saved.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while saving.', true);
            }
        },

        async deleteItem(id, index) {
            if (this.busy) return;
            if (!window.confirm('Delete this entry? This cannot be undone.')) return;
            this.busy = true;
            this.status('Deleting…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category: id, index: index })
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not delete.', true);
                    this.busy = false;
                    return;
                }
                if (data.profile) this.profile = data.profile;
                this.openIndex = null;
                this.busy = false;
                this.render();
                this.status('Deleted.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while deleting.', true);
            }
        },

        async saveObject(id) {
            if (this.busy) return;
            const form = this.root.querySelector('[data-object="' + id + '"]');
            if (!form) return;
            const values = this.readForm(form);
            const payload = {};
            payload[id] = values;

            this.busy = true;
            this.status('Saving…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not save.', true);
                    this.busy = false;
                    return;
                }
                if (data.profile) this.profile = data.profile;
                this.busy = false;
                this.status('Saved.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while saving.', true);
            }
        },

        async saveSettings() {
            if (this.busy) return;
            const input = this.root.querySelector('#hub-retention');
            if (!input) return;
            this.busy = true;
            this.status('Saving…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ upload_settings: { retention_days: input.value } })
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not save.', true);
                    this.busy = false;
                    return;
                }
                if (data.profile) this.profile = data.profile;
                this.busy = false;
                this.status('Saved.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while saving.', true);
            }
        },

        async loadInteractions() {
            const el = this.root.querySelector('#hub-tool');
            if (!el) return;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/interactions');
                const data = await resp.json();
                const list = (data && Array.isArray(data.interactions)) ? data.interactions : [];
                if (!list.length) {
                    el.innerHTML = '<div class="hub-note ok"><i class="fas fa-circle-check"></i> No interactions found between your recorded medications and supplements.</div>';
                    return;
                }
                let html = '';
                for (let i = 0; i < list.length; i++) {
                    const it = list[i];
                    html += '<div class="hub-note warn"><strong>' + esc(toText(it.pair || it.drugs || '')) + '</strong><br>' +
                        esc(toText(it.description || it.warning || it)) + '</div>';
                }
                el.innerHTML = html;
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not check interactions.</div>';
            }
        },

        async loadSummary() {
            const el = this.root.querySelector('#hub-tool');
            if (!el) return;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/summary');
                const data = await resp.json();
                const text = (data && data.summary) ? data.summary : '';
                el.innerHTML = text
                    ? '<pre class="hub-pre">' + esc(text) + '</pre>'
                    : '<div class="hub-note">No health context stored yet. Add some information first.</div>';
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not load summary.</div>';
            }
        }
    };

    window.DrHealthHub = DrHealthHub;
})();
