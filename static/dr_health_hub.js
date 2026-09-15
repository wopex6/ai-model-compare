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
        },
        diary: {
            title: 'Diary',
            icon: 'fa-book-open',
            desc: 'Daily voice or text notes',
            primary: 'title',
            fields: [
                { key: 'title', label: 'Title (you can leave this)', type: 'text' },
                { key: 'date', label: 'Date', type: 'date' },
                { key: 'mood', label: 'Mood', type: 'select', options: ['happy', 'calm', 'sad', 'angry', 'anxious', 'neutral', 'tired'] },
                { key: 'content', label: 'Entry - what happened or how you feel', type: 'textarea', required: true },
                { key: 'tags', label: 'Tags - one per line (e.g. sleep, work, pain)', type: 'list' }
            ]
        }
    };

    const OBJECT_SECTIONS = {
        personal: {
            title: 'Personal Details',
            icon: 'fa-id-card',
            desc: 'Age, gender, blood type',
            hint: 'Single source for your details. The emergency card is built from this - nothing is entered twice.',
            fields: [
                { key: 'name', label: 'Full name', type: 'text' },
                { key: 'age', label: 'Age', type: 'text' },
                { key: 'gender', label: 'Gender', type: 'text' },
                { key: 'location', label: 'Location', type: 'text' },
                { key: 'blood_type', label: 'Blood type', type: 'text' },
                { key: 'allergies', label: 'Allergies - one per line', type: 'list' },
                { key: 'medical_history', label: 'Medical history - major illnesses, surgeries, family history', type: 'textarea' },
                { key: 'doctors', label: 'Doctors - name, specialty, phone; one per line', type: 'textarea' },
                { key: 'ec_name', label: 'Emergency contact name', type: 'text' },
                { key: 'ec_rel', label: 'Emergency contact relationship', type: 'text' },
                { key: 'ec_phone', label: 'Emergency contact phone', type: 'text' }
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
            group: 'Advice & Reminders',
            items: [
                { id: 'advice', kind: 'advice', title: 'Advice & Insights', icon: 'fa-lightbulb', desc: 'What your records show' },
                { id: 'reminders', kind: 'reminders', title: 'Reminders', icon: 'fa-bell', desc: 'Due and upcoming' },
                { id: 'digest', kind: 'digest', title: 'Review', icon: 'fa-newspaper', desc: 'Your periodic summary' }
            ]
        },
        {
            group: 'Emergency & Identity',
            items: [
                { id: 'vitals', kind: 'vitals', title: 'Emergency Card', icon: 'fa-kit-medical', desc: 'Read-only card from Personal Details, works offline' },
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
            group: 'Notes',
            items: [
                { id: 'diary', kind: 'list' }
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

    function micHelpText() {
        const ua = navigator.userAgent || '';
        const platform = navigator.platform || '';
        const maxTouch = navigator.maxTouchPoints || 0;
        const isIOS = /iPad|iPhone|iPod/i.test(ua) || (platform === 'MacIntel' && maxTouch > 1);
        const isAndroid = /Android/i.test(ua);
        const isStandalone = 'standalone' in navigator && navigator.standalone;
        if (isIOS) {
            if (isStandalone) return 'iPhone: a home-screen PWA cannot use the microphone. Use the iOS keyboard microphone icon to dictate into the Entry field, or open Dr. Health in Safari.';
            return 'iPhone: if Safari/Chrome does not appear in Settings → Privacy & Security → Microphone, use the iOS keyboard microphone icon to dictate into the Entry field.';
        }
        if (isAndroid) return 'Microphone access blocked. Android: Settings → Apps → (this browser/PWA) → Permissions → Microphone → Allow.';
        return 'Microphone access blocked. Please allow microphone access in your browser/PWA settings.';
    }

    const HIDDEN_KEYS = ['added_at', 'updated_at', 'source', 'id',
        'verified_by_user', 'confidence', 'completed_at'];

    // Mirrors the vocabulary in ai_compare/health_insights.py.
    const SOURCE_LABELS = {
        user_entered: 'You entered this',
        document_extracted: 'From your report',
        ai_inferred: 'AI interpretation',
        clinician_report: 'From your clinician',
        unknown: 'Recorded before sources were tracked'
    };

    const SOURCE_SHORT = {
        user_entered: 'You',
        document_extracted: 'Report',
        ai_inferred: 'AI',
        clinician_report: 'Clinician',
        unknown: 'Legacy'
    };

    function sourceOf(item) {
        const raw = item && item.source ? String(item.source) : 'user_entered';
        return SOURCE_LABELS[raw] ? raw : 'user_entered';
    }

    function needsConfirming(item) {
        const src = sourceOf(item);
        return (src === 'ai_inferred' || src === 'unknown') && !(item && item.verified_by_user);
    }

    function provenanceBadge(item) {
        const src = sourceOf(item);
        const confirmed = item && item.verified_by_user;
        const cls = 'hub-prov ' + src + (confirmed ? ' confirmed' : '');
        let text = SOURCE_SHORT[src];
        if (src === 'ai_inferred' || src === 'unknown') text += confirmed ? ' \u2713' : ' ?';
        return '<span class="' + cls + '" title="' + esc(SOURCE_LABELS[src]) + '">' + esc(text) + '</span>';
    }

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
        overview: null,
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
            this.loadOverview();
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
            this.loadOverview();
        },

        // Deterministic overview: observations, reminders and any cached advice.
        // Cheap by design — this endpoint never calls a model.
        async loadOverview() {
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/overview');
                const data = await resp.json();
                if (data && data.overview) {
                    this.overview = data.overview;
                    if (this.route.view === 'index') this.render();
                }
            } catch (e) {
                /* the hub stays usable without the overview */
            }
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
            if (id === 'reminders') {
                if (!this.overview) return null;
                const c = this.overview.reminder_counts || {};
                return c.total || 0;
            }
            if (id === 'advice') {
                if (!this.overview) return null;
                const obs = this.overview.observations || [];
                const sug = (this.overview.advice && this.overview.advice.suggestions) || [];
                return obs.length + sug.length;
            }
            if (id === 'digest') return null;
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

            // Red flags are the only thing allowed to interrupt the user here.
            const flags = (this.overview && this.overview.red_flags) ? this.overview.red_flags : [];
            for (let f = 0; f < flags.length; f++) {
                html += '<div class="hub-note error"><strong><i class="fas fa-triangle-exclamation"></i> ' +
                    esc(flags[f].title) + '</strong><br>' + esc(flags[f].detail);
                if (flags[f].action) html += '<br><em>' + esc(flags[f].action) + '</em>';
                html += '</div>';
            }

            const overdue = (this.overview && this.overview.reminder_counts)
                ? (this.overview.reminder_counts.overdue || 0) : 0;
            if (overdue) {
                html += '<div class="hub-note warn"><strong><i class="fas fa-bell"></i> ' + overdue +
                    ' reminder(s) overdue</strong><br>Open Reminders to catch up.</div>';
            }
            if (this.overview && this.overview.digest_due) {
                html += '<div class="hub-note"><strong><i class="fas fa-newspaper"></i> Your review is ready</strong>' +
                    '<br>Open Review for a summary of what changed.</div>';
            }

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
            } else if (kind === 'advice') {
                html += '<button class="hub-icon-btn primary" id="hub-advice-refresh" title="Regenerate advice"><i class="fas fa-rotate"></i></button>';
            } else if (kind === 'reminders') {
                html += '<button class="hub-icon-btn" id="hub-reminders-ics" title="Add to calendar"><i class="fas fa-calendar-plus"></i></button>';
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
            else if (kind === 'advice') html += this.adviceBody();
            else if (kind === 'reminders') html += this.remindersBody();
            else if (kind === 'digest') html += '<div id="hub-tool" class="hub-tool"><em>Building your review…</em></div>';
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
            html += provenanceBadge(item);
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
                html += '<div class="hub-added">' + esc(SOURCE_LABELS[sourceOf(item)]) +
                    (item.added_at ? ' \u00b7 recorded ' + esc(String(item.added_at).slice(0, 10)) : '') + '</div>';
                if (needsConfirming(item)) {
                    html += '<div class="hub-note warn">The AI worked this out from your documents or ' +
                        'conversations. Confirm it so future advice is built on facts.</div>';
                }
                html += '<div class="hub-row-actions">';
                if (needsConfirming(item)) {
                    html += '<button class="hub-btn primary" data-verify="' + index + '"><i class="fas fa-check-double"></i> Confirm</button>';
                }
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
            if (id === 'diary' && isNew) {
                const today = new Date();
                const m = today.getMonth() + 1;
                const d = today.getDate();
                const iso = today.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (d < 10 ? '0' + d : d);
                if (!item.date) item.date = iso;
                if (!item.title) item.title = 'Diary entry - ' + item.date;
            }
            let html = '<div class="hub-form" data-index="' + index + '">';
            html += '<div class="hub-form-title">' + (isNew ? 'Add ' : 'Edit ') + esc(this.singular(schema.title)) + '</div>';
            for (let i = 0; i < schema.fields.length; i++) {
                html += this.inputHtml(schema.fields[i], item[schema.fields[i].key]);
            }
            if (id === 'diary') {
                const _ua = navigator.userAgent || '';
                const _isIOS = /iPad|iPhone|iPod/i.test(_ua) ||
                    (navigator.platform === 'MacIntel' && (navigator.maxTouchPoints || 0) > 1);
                if (_isIOS) {
                    // No web speech API on iOS — the keyboard mic icon dictates
                    // straight into the Entry field instead.
                    html += '<div class="hub-mic-bar" style="margin:8px 0 12px; padding:10px; background:#f0f4ff; border-radius:8px; font-size:0.85rem; color:#555;">' +
                        '<i class="fas fa-microphone"></i> Tip: tap into the Entry field, then use the microphone key on the keyboard to dictate.</div>';
                } else {
                    html += '<div class="hub-mic-bar" style="margin:8px 0 12px; padding:10px; background:#f0f4ff; border-radius:8px;">';
                    html += '<label class="hub-input-label" for="hf-diary-lang" style="display:inline-block; margin-right:8px;">Voice language</label>';
                    html += '<select class="hub-input" id="hf-diary-lang" style="width:auto; display:inline-block; min-width:120px; margin-right:8px;">';
                    html += '<option value="yue-Hant-HK">Cantonese (HK)</option>';
                    html += '<option value="en-GB">English</option>';
                    html += '</select>';
                    html += '<button class="hub-btn" id="hf-diary-mic" type="button"><i class="fas fa-microphone"></i> Record</button>';
                    html += '</div>';
                }
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
            html += '<div class="hub-form-hint">' + esc(schema.hint || 'Changes save straight to your record.') + '</div>';
            for (let i = 0; i < schema.fields.length; i++) {
                const value = (id === 'personal' && schema.fields[i].key === 'name')
                    ? (this.profile && this.profile.name)
                    : obj[schema.fields[i].key];
                html += this.inputHtml(schema.fields[i], value);
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

        // ---------- Advice & Insights ----------
        // Tier 1 observations are computed facts; Tier 2 suggestions are AI wording.
        // They are rendered in separate blocks so the user can always tell them apart.
        adviceBody() {
            const ov = this.overview;
            if (!ov) return '<div class="hub-tool"><em>Loading…</em></div>';

            const observations = ov.observations || [];
            const advice = ov.advice || {};
            const suggestions = advice.suggestions || [];
            const questions = advice.questions_for_doctor || [];
            let html = '';

            if (!observations.length && !suggestions.length && !questions.length) {
                html += '<div class="hub-empty"><i class="fas fa-lightbulb"></i>';
                html += '<p>' + esc(advice.reason || 'Nothing to show yet. Add test results or conditions first.') + '</p>';
                html += '</div>';
                return html + this.disclaimerHtml(ov.disclaimer);
            }

            if (observations.length) {
                html += '<div class="hub-group-label">From your records</div>';
                for (let i = 0; i < observations.length; i++) {
                    html += this.observationHtml(observations[i]);
                }
            }

            if (suggestions.length) {
                html += '<div class="hub-group-label">AI suggestions to discuss</div>';
                for (let i = 0; i < suggestions.length; i++) {
                    const s = suggestions[i];
                    html += '<div class="hub-note ai"><span class="hub-prov ai_inferred">AI</span> <strong>' +
                        esc(s.title) + '</strong><br>' + esc(s.detail);
                    if (s.cites && s.cites.length) {
                        html += '<div class="hub-cites">Based on: ' + esc(s.cites.join(', ')) + '</div>';
                    }
                    html += '</div>';
                }
            }

            if (questions.length) {
                html += '<div class="hub-group-label">Questions for your doctor</div>';
                for (let i = 0; i < questions.length; i++) {
                    const q = questions[i];
                    html += '<div class="hub-note"><strong>' + esc(q.question) + '</strong>';
                    if (q.context) html += '<br>' + esc(q.context);
                    html += '<div class="hub-row-actions"><button class="hub-btn" data-save-question="' + i +
                        '"><i class="fas fa-plus"></i> Save to my list</button></div></div>';
                }
            }

            if (advice.generated_at) {
                html += '<div class="hub-added" style="padding:0 14px 8px;">AI wording generated ' +
                    esc(String(advice.generated_at).slice(0, 16).replace('T', ' ')) +
                    (advice.model ? ' using ' + esc(advice.model) : '') + '.</div>';
            } else if (advice.reason) {
                html += '<div class="hub-note">' + esc(advice.reason) + '</div>';
            }
            if (typeof ov.remaining_generations === 'number') {
                html += '<div class="hub-added" style="padding:0 14px 8px;">' +
                    ov.remaining_generations + ' AI refresh(es) left today.</div>';
            }

            return html + this.disclaimerHtml(ov.disclaimer);
        },

        observationHtml(o) {
            const cls = o.severity === 'urgent' ? 'error' : (o.severity === 'watch' ? 'warn' : 'ok');
            const icon = o.severity === 'urgent' ? 'fa-triangle-exclamation'
                : (o.severity === 'watch' ? 'fa-circle-exclamation' : 'fa-circle-info');
            let html = '<div class="hub-note ' + cls + '">';
            html += '<span class="hub-prov computed">Fact</span> <strong><i class="fas ' + esc(icon) + '"></i> ' +
                esc(o.title) + '</strong><br>' + esc(o.detail);
            if (o.action) html += '<br><em>' + esc(o.action) + '</em>';
            if (o.evidence && o.evidence.length) {
                const bits = [];
                for (let i = 0; i < o.evidence.length && i < 6; i++) {
                    const e = o.evidence[i];
                    bits.push(toText(e.value) + (e.date ? ' (' + e.date + ')' : ''));
                }
                html += '<div class="hub-cites">Evidence: ' + esc(bits.join(', ')) + '</div>';
            }
            html += '</div>';
            return html;
        },

        disclaimerHtml(text) {
            if (!text) return '';
            return '<div class="hub-disclaimer"><i class="fas fa-circle-info"></i> ' + esc(text) + '</div>';
        },

        // ---------- Reminders ----------
        remindersBody() {
            const ov = this.overview;
            if (!ov) return '<div class="hub-tool"><em>Loading…</em></div>';
            if (ov.settings && !ov.settings.reminders_enabled) {
                return '<div class="hub-empty"><i class="fas fa-bell-slash"></i>' +
                    '<p>Reminders are turned off in Settings.</p></div>';
            }

            const reminders = ov.reminders || [];
            if (!reminders.length) {
                return '<div class="hub-empty"><i class="fas fa-bell"></i>' +
                    '<p>Nothing due. Reminders appear from follow-up dates, "recheck in 3 months" notes ' +
                    'in your reports, and medications with a frequency.</p></div>';
            }

            const buckets = [
                { key: 'overdue', label: 'Overdue' },
                { key: 'due_today', label: 'Due today' },
                { key: 'upcoming', label: 'Coming up' },
                { key: 'recurring', label: 'Ongoing' },
                { key: 'no_date', label: 'No date set' }
            ];

            let html = '';
            for (let b = 0; b < buckets.length; b++) {
                const group = [];
                for (let i = 0; i < reminders.length; i++) {
                    if (reminders[i].status === buckets[b].key) group.push(reminders[i]);
                }
                if (!group.length) continue;
                html += '<div class="hub-group-label">' + esc(buckets[b].label) + ' (' + group.length + ')</div>';
                for (let i = 0; i < group.length; i++) {
                    html += this.reminderHtml(group[i]);
                }
            }
            return html;
        },

        reminderHtml(r) {
            const cls = r.status === 'overdue' ? 'error' : (r.status === 'due_today' ? 'warn' : '');
            let when = '';
            if (r.due_date) {
                when = r.due_date;
                if (r.status === 'overdue') when += ' · ' + Math.abs(r.days_until) + ' day(s) late';
                else if (r.status === 'upcoming') when += ' · in ' + r.days_until + ' day(s)';
            } else if (r.recurrence) {
                when = r.recurrence;
            }

            let html = '<div class="hub-note ' + cls + '">';
            html += '<strong>' + esc(r.title) + '</strong>';
            if (when) html += ' <span class="hub-when">' + esc(when) + '</span>';
            if (r.detail) html += '<br>' + esc(r.detail);
            if (r.source_category && r.source_index !== null && r.source_index !== undefined
                && r.status !== 'recurring') {
                html += '<div class="hub-row-actions">';
                html += '<button class="hub-btn" data-reminder-done="' + esc(r.id) + '"><i class="fas fa-check"></i> Done</button>';
                html += '<button class="hub-btn" data-reminder-snooze="' + esc(r.id) + '"><i class="fas fa-clock"></i> Snooze 7d</button>';
                html += '</div>';
            }
            html += '</div>';
            return html;
        },

        findReminder(id) {
            const reminders = (this.overview && this.overview.reminders) ? this.overview.reminders : [];
            for (let i = 0; i < reminders.length; i++) {
                if (reminders[i].id === id) return reminders[i];
            }
            return null;
        },

        // ---------- Vitals ----------
        vitalsBody() {
            let html = '<div class="hub-note">';
            html += 'A read-only card for paramedics, built from Personal Details and your current ' +
                'conditions and medications. A copy is kept on this phone so it works without internet.';
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
            html += '<div class="hub-row-actions"><button class="hub-btn primary" id="hub-settings-save"><i class="fas fa-check"></i> Save Settings</button></div>';
            html += '</div>';

            html += '<div class="hub-form" style="margin-top:20px; border-top:1px solid #e3e7ea; padding-top:16px;">';
            html += '<div class="hub-form-title">Change password</div>';
            html += '<label class="hub-input-label" for="hub-current-password">Current password</label>';
            html += '<input class="hub-input" id="hub-current-password" type="password">';
            html += '<label class="hub-input-label" for="hub-new-password">New password</label>';
            html += '<input class="hub-input" id="hub-new-password" type="password">';
            html += '<label class="hub-input-label" for="hub-confirm-password">Confirm new password</label>';
            html += '<input class="hub-input" id="hub-confirm-password" type="password">';
            html += '<div class="hub-row-actions"><button class="hub-btn primary" id="hub-change-password"><i class="fas fa-check"></i> Change password</button></div>';
            html += '</div>';

            const s = (this.overview && this.overview.settings) ? this.overview.settings : {};
            html += '<div class="hub-form" style="margin-top:20px; border-top:1px solid #e3e7ea; padding-top:16px;">';
            html += '<div class="hub-form-title">Advice &amp; reminders</div>';
            html += '<label class="hub-check"><input type="checkbox" id="hub-ai-enabled"' +
                (s.ai_enabled === false ? '' : ' checked') + '> Let AI write suggestions from my records</label>';
            html += '<label class="hub-check"><input type="checkbox" id="hub-reminders-enabled"' +
                (s.reminders_enabled === false ? '' : ' checked') + '> Show reminders</label>';
            html += '<label class="hub-input-label" for="hub-digest-frequency">Periodic review</label>';
            html += '<select class="hub-input" id="hub-digest-frequency">';
            const freqs = [['weekly', 'Weekly'], ['monthly', 'Monthly'], ['off', 'Off']];
            for (let i = 0; i < freqs.length; i++) {
                html += '<option value="' + freqs[i][0] + '"' +
                    (String(s.digest_frequency || 'weekly') === freqs[i][0] ? ' selected' : '') +
                    '>' + freqs[i][1] + '</option>';
            }
            html += '</select>';
            html += '<label class="hub-input-label" for="hub-advice-locale">Advice language</label>';
            html += '<select class="hub-input" id="hub-advice-locale">';
            html += '<option value="en"' + (String(s.locale || 'en') === 'en' ? ' selected' : '') + '>English</option>';
            html += '<option value="zh-HK"' + (String(s.locale) === 'zh-HK' ? ' selected' : '') + '>繁體中文 (香港)</option>';
            html += '</select>';
            html += '<div class="hub-row-actions"><button class="hub-btn primary" id="hub-advice-settings-save"><i class="fas fa-check"></i> Save preferences</button></div>';
            html += '<div class="hub-form-hint">Your records are sent to an AI provider only when advice is generated. ' +
                'Turn the first option off to keep everything on-device rules only.</div>';
            html += '</div>';

            const docs = (this.profile && Array.isArray(this.profile.uploaded_documents)) ? this.profile.uploaded_documents : [];
            html += '<div class="hub-note"><strong>' + docs.length + '</strong> document(s) currently stored.</div>';
            return html;
        },

        async saveAdviceSettings() {
            if (this.busy) return;
            const ai = this.root.querySelector('#hub-ai-enabled');
            const rem = this.root.querySelector('#hub-reminders-enabled');
            const freq = this.root.querySelector('#hub-digest-frequency');
            const loc = this.root.querySelector('#hub-advice-locale');
            if (!ai || !rem || !freq || !loc) return;
            this.busy = true;
            this.status('Saving…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/advice-settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ai_enabled: ai.checked,
                        reminders_enabled: rem.checked,
                        digest_frequency: freq.value,
                        locale: loc.value
                    })
                });
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not save preferences.', true);
                    return;
                }
                this.status('Preferences saved.');
                this.loadOverview();
            } catch (e) {
                this.busy = false;
                this.status('Network error while saving.', true);
            }
        },

        // ---------- Advice & reminder actions ----------
        async refreshAdvice() {
            if (this.busy) return;
            this.busy = true;
            this.status('Asking the AI to review your records…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/advice?refresh=1');
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not generate advice.', true);
                    return;
                }
                await this.loadOverview();
                this.render();
                const advice = data.advice || {};
                this.status(advice.reason ? advice.reason : 'Advice updated.', !!advice.reason);
            } catch (e) {
                this.busy = false;
                this.status('Network error while generating advice.', true);
            }
        },

        async actOnReminder(id, action) {
            if (this.busy) return;
            const reminder = this.findReminder(id);
            if (!reminder) return;
            this.busy = true;
            this.status(action === 'complete' ? 'Marking done…' : 'Snoozing…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/reminder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: action,
                        source_category: reminder.source_category,
                        source_index: reminder.source_index,
                        days: 7
                    })
                });
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not update reminder.', true);
                    return;
                }
                await this.reload();
                this.render();
                this.status(action === 'complete' ? 'Marked done.' : 'Snoozed 7 days.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while updating reminder.', true);
            }
        },

        async verifyItem(id, index) {
            if (this.busy) return;
            this.busy = true;
            this.status('Confirming…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category: id, index: index, verified: true })
                });
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not confirm.', true);
                    return;
                }
                if (this.profile && Array.isArray(this.profile[id]) && this.profile[id][index]) {
                    this.profile[id][index] = data.item;
                }
                this.render();
                this.status('Confirmed. Future advice will treat this as a fact.');
                this.loadOverview();
            } catch (e) {
                this.busy = false;
                this.status('Network error while confirming.', true);
            }
        },

        async saveQuestion(questionIndex) {
            const advice = (this.overview && this.overview.advice) ? this.overview.advice : {};
            const list = advice.questions_for_doctor || [];
            const q = list[questionIndex];
            if (!q) return;
            if (this.busy) return;
            this.busy = true;
            this.status('Saving question…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/item', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        category: 'questions_for_doctor',
                        item: { question: q.question, context: q.context, priority: q.priority }
                    })
                });
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not save.', true);
                    return;
                }
                if (data.profile) this.profile = data.profile;
                this.status('Added to Questions for Doctor.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while saving.', true);
            }
        },

        async downloadReminderCalendar() {
            this.status('Preparing calendar file…');
            try {
                const token = localStorage.getItem('authToken');
                const resp = await fetch('/api/health-profile/reminders.ics', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                if (!resp.ok) {
                    this.status('Could not build the calendar file.', true);
                    return;
                }
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'dr-health-reminders.ics';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(url), 1000);
                this.status('Calendar file downloaded. Open it to add the dates.');
            } catch (e) {
                this.status('Could not download the calendar file.', true);
            }
        },

        async loadDigest() {
            const el = this.root.querySelector('#hub-tool');
            if (!el) return;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/digest?mark_seen=1');
                const data = await resp.json();
                const d = (data && data.digest) ? data.digest : null;
                if (!d) {
                    el.innerHTML = '<div class="hub-note error">Could not build your review.</div>';
                    return;
                }
                let html = '<div class="hub-note"><strong>' +
                    esc(d.period === 'monthly' ? 'Monthly review' : 'Weekly review') + '</strong><br>' +
                    esc(d.period_start) + ' to ' + esc(d.period_end) + '</div>';

                if (d.added_total) {
                    const bits = [];
                    for (const k in d.added) {
                        if (Object.prototype.hasOwnProperty.call(d.added, k)) {
                            bits.push(d.added[k] + ' ' + labelFor(k).toLowerCase());
                        }
                    }
                    html += '<div class="hub-note ok"><strong>New in this period</strong><br>' +
                        esc(bits.join(', ')) + '</div>';
                } else {
                    html += '<div class="hub-note"><strong>New in this period</strong><br>Nothing was added.</div>';
                }

                const flags = d.red_flags || [];
                for (let i = 0; i < flags.length; i++) html += this.observationHtml(flags[i]);

                const due = d.reminders_due || [];
                if (due.length) {
                    html += '<div class="hub-group-label">Needs attention</div>';
                    for (let i = 0; i < due.length; i++) html += this.reminderHtml(due[i]);
                }

                const obs = d.observations || [];
                if (obs.length) {
                    html += '<div class="hub-group-label">From your records</div>';
                    for (let i = 0; i < obs.length; i++) {
                        if (obs[i].severity === 'urgent') continue;
                        html += this.observationHtml(obs[i]);
                    }
                }

                const sug = d.suggestions || [];
                if (sug.length) {
                    html += '<div class="hub-group-label">AI suggestions</div>';
                    for (let i = 0; i < sug.length; i++) {
                        html += '<div class="hub-note ai"><span class="hub-prov ai_inferred">AI</span> <strong>' +
                            esc(sug[i].title) + '</strong><br>' + esc(sug[i].detail) + '</div>';
                    }
                }

                el.innerHTML = html + this.disclaimerHtml(d.disclaimer);
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not build your review.</div>';
            }
        },

        async savePassword() {
            if (this.busy) return;
            const current = this.root.querySelector('#hub-current-password');
            const newPass = this.root.querySelector('#hub-new-password');
            const confirm = this.root.querySelector('#hub-confirm-password');
            if (!current || !newPass || !confirm) return;
            if (!current.value || !newPass.value) {
                this.status('All password fields are required.', true);
                return;
            }
            if (newPass.value !== confirm.value) {
                this.status('New passwords do not match.', true);
                return;
            }
            this.busy = true;
            this.status('Changing password…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ currentPassword: current.value, newPassword: newPass.value })
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not change password.', true);
                    this.busy = false;
                    return;
                }
                current.value = '';
                newPass.value = '';
                confirm.value = '';
                this.busy = false;
                this.status('Password changed.');
            } catch (e) {
                this.busy = false;
                this.status('Network error.', true);
            }
        },

        async recordDiary(formEl) {
            const ua = navigator.userAgent || '';
            const platform = navigator.platform || '';
            const maxTouch = navigator.maxTouchPoints || 0;
            const isIOS = /iPad|iPhone|iPod/i.test(ua) || (platform === 'MacIntel' && maxTouch > 1);
            if (isIOS) {
                this.status(micHelpText(), true);
                return;
            }
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                this.status('Voice input is not supported in this browser.', true);
                return;
            }
            // Scope to the form that owns the mic button — several diary forms
            // can be open at once (add + edit), all sharing #hf-content ids, so
            // a root-wide query can write the transcript into the wrong form.
            const scope = formEl || this.root;
            const lang = scope.querySelector('#hf-diary-lang');
            const target = scope.querySelector('#hf-content');
            if (!target) return;

            // No getUserMedia pre-check: it is a second permission prompt on top
            // of SpeechRecognition's own, and on Android the extra activity can
            // bounce the user out of the app.  A denial surfaces via onerror.
            const rec = new SpeechRecognition();
            rec.lang = lang ? lang.value : 'yue-Hant-HK';
            rec.continuous = false;
            rec.interimResults = false;
            rec.onstart = () => { this.status('Listening…'); };
            rec.onerror = (e) => {
                const msg = e.error === 'service-not-allowed' || e.error === 'not-allowed'
                    ? micHelpText()
                    : (e.error === 'language-not-supported'
                        ? 'This language is not supported by your browser. Try English.'
                        : 'Voice input error: ' + e.error);
                this.status(msg, true);
            };
            rec.onresult = (e) => {
                if (e.results && e.results[0] && e.results[0][0]) {
                    target.value = (target.value ? target.value + ' ' : '') + e.results[0][0].transcript;
                    this.status('Voice recorded.');
                }
            };
            try { rec.start(); } catch (e) { this.status('Could not start voice input: ' + e.message, true); }
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
            } else if (kind === 'settings') {
                const save = this.root.querySelector('#hub-settings-save');
                if (save) save.addEventListener('click', () => self.saveSettings());
                const change = this.root.querySelector('#hub-change-password');
                if (change) change.addEventListener('click', () => self.savePassword());
                const adviceSave = this.root.querySelector('#hub-advice-settings-save');
                if (adviceSave) adviceSave.addEventListener('click', () => self.saveAdviceSettings());
            } else if (kind === 'interactions') {
                this.loadInteractions();
            } else if (kind === 'summary') {
                this.loadSummary();
            } else if (kind === 'digest') {
                this.loadDigest();
            } else if (kind === 'advice') {
                const refresh = this.root.querySelector('#hub-advice-refresh');
                if (refresh) refresh.addEventListener('click', () => self.refreshAdvice());
                const questions = this.root.querySelectorAll('[data-save-question]');
                for (let i = 0; i < questions.length; i++) {
                    questions[i].addEventListener('click', function () {
                        self.saveQuestion(parseInt(this.getAttribute('data-save-question'), 10));
                    });
                }
                if (!this.overview) {
                    this.loadOverview().then(() => { if (self.route.section === 'advice') self.render(); });
                }
            } else if (kind === 'reminders') {
                const ics = this.root.querySelector('#hub-reminders-ics');
                if (ics) ics.addEventListener('click', () => self.downloadReminderCalendar());
                const dones = this.root.querySelectorAll('[data-reminder-done]');
                for (let i = 0; i < dones.length; i++) {
                    dones[i].addEventListener('click', function () {
                        self.actOnReminder(this.getAttribute('data-reminder-done'), 'complete');
                    });
                }
                const snoozes = this.root.querySelectorAll('[data-reminder-snooze]');
                for (let i = 0; i < snoozes.length; i++) {
                    snoozes[i].addEventListener('click', function () {
                        self.actOnReminder(this.getAttribute('data-reminder-snooze'), 'snooze');
                    });
                }
                if (!this.overview) {
                    this.loadOverview().then(() => { if (self.route.section === 'reminders') self.render(); });
                }
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

            const verifies = root.querySelectorAll('[data-verify]');
            for (let i = 0; i < verifies.length; i++) {
                verifies[i].addEventListener('click', function () {
                    self.verifyItem(id, parseInt(this.getAttribute('data-verify'), 10));
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

            if (id === 'diary') {
                const mics = this.root.querySelectorAll('#hf-diary-mic');
                for (let i = 0; i < mics.length; i++) {
                    mics[i].addEventListener('click', function () {
                        self.recordDiary(this.closest('.hub-form'));
                    });
                }
            }
        },

        status(text, isError) {
            const el = this.root ? this.root.querySelector('#hub-status') : null;
            if (!el) return;
            const icon = isError ? 'fa-exclamation-circle' : 'fa-check-circle';
            el.innerHTML = text ? '<i class="fas ' + icon + '"></i> ' + esc(text) : '';
            el.className = 'hub-status' + (isError ? ' error' : '') + (text ? ' show' : '');
        },

        // ---------- Persistence ----------
        async saveItem(id, index, formEl) {
            if (this.busy) return;
            const schema = LIST_SECTIONS[id];
            const values = this.readForm(formEl);

            if (id === 'diary') {
                if (!values.date) {
                    const today = new Date();
                    const m = today.getMonth() + 1;
                    const d = today.getDate();
                    values.date = today.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (d < 10 ? '0' + d : d);
                }
                if (!values.title) values.title = 'Diary entry - ' + values.date;
            }

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
            if (id === 'personal' && 'name' in values) {
                payload.name = values.name;
                delete values.name;
            }
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
