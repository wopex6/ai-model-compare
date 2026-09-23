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
            desc: 'Identity, alerts and contacts for the emergency card',
            hint: 'Identity, alerts and contacts live here. Medications are a separate list under Health → Medications — they still appear on the emergency card.',
            fields: [
                { heading: 'Who you are' },
                { key: 'name', label: 'Full name', type: 'text' },
                { key: 'date_of_birth', label: 'Date of birth', type: 'dob',
                  hint: 'Type it (15/3/1954 or 15 Mar 1954) or open the calendar and pick year, month and day separately.' },
                { key: 'age', label: 'Age (if no date of birth)', type: 'text' },
                { key: 'gender', label: 'Sex / gender', type: 'text' },
                { key: 'weight', label: 'Weight', type: 'text', hint: 'Include the unit, e.g. 72 kg. Used for drug doses on scene.' },
                { key: 'height', label: 'Height', type: 'text' },
                { key: 'blood_type', label: 'Blood type', type: 'text' },
                { key: 'language', label: 'Language / communication needs', type: 'text',
                  hint: 'e.g. Cantonese, Auslan, hard of hearing.' },
                { key: 'location', label: 'Suburb / area', type: 'text' },
                { heading: 'Tell a paramedic first' },
                { key: 'allergies', label: 'Allergies — one per line', type: 'list' },
                { key: 'anaphylaxis', label: 'Anaphylaxis and where the adrenaline pen is', type: 'textarea',
                  hint: 'e.g. Has had anaphylaxis to peanuts. EpiPen in the kitchen drawer / bag.' },
                { key: 'advance_care', label: 'Advance care / not for CPR', type: 'textarea',
                  hint: 'Leave blank if there is no plan. Shown at the top of the unlocked emergency card.' },
                { key: 'implants', label: 'Implants and devices — one per line', type: 'list',
                  hint: 'Pacemaker, ICD, insulin pump, stents, cochlear implant, metal joints.' },
                { key: 'pregnancy', label: 'Pregnancy / due date', type: 'text',
                  hint: 'Leave blank if not applicable.' },
                { key: 'medical_history', label: 'Other medical history', type: 'textarea',
                  hint: 'Major illnesses, surgeries, family history — not a second copy of conditions.' },
                { heading: 'Who to call' },
                { key: 'gp_name', label: 'Usual GP', type: 'text' },
                { key: 'gp_phone', label: 'GP phone', type: 'tel' },
                { key: 'doctors', label: 'Other doctors — name, specialty, phone; one per line', type: 'textarea' },
                { key: 'ec_name', label: 'Emergency contact name', type: 'text' },
                { key: 'ec_rel', label: 'Emergency contact relationship', type: 'text' },
                { key: 'ec_phone', label: 'Emergency contact phone', type: 'tel' }
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
                { id: 'digest', kind: 'digest', title: 'Review', icon: 'fa-newspaper', desc: 'Your periodic summary' },
                { id: 'visit', kind: 'visit', title: 'GP visit brief', icon: 'fa-briefcase-medical', desc: 'One page for your appointment' }
            ]
        },
        {
            group: 'Emergency & Identity',
            items: [
                { id: 'vitals', kind: 'vitals', title: 'Emergency Card', icon: 'fa-kit-medical', desc: 'Opens the card. Edit Personal Details, Medications and Conditions to change it' },
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

    // Day-first, matching parse_date() on the server (HK / AU).
    const DOB_MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    function parseDob(text) {
        const raw = String(text || '').trim();
        if (!raw) return null;
        let m = raw.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
        if (m) return dobParts(Number(m[1]), Number(m[2]), Number(m[3]));
        m = raw.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
        if (m) return dobParts(Number(m[3]), Number(m[2]), Number(m[1]));
        m = raw.match(/^(\d{1,2})\s+([A-Za-z]{3,})\.?\s+(\d{4})$/);
        if (m) {
            const month = dobMonthNum(m[2]);
            if (month) return dobParts(Number(m[3]), month, Number(m[1]));
        }
        m = raw.match(/^([A-Za-z]{3,})\.?\s+(\d{1,2}),?\s+(\d{4})$/);
        if (m) {
            const month = dobMonthNum(m[1]);
            if (month) return dobParts(Number(m[3]), month, Number(m[2]));
        }
        return null;
    }
    function dobMonthNum(name) {
        const key = String(name || '').slice(0, 3).toLowerCase();
        for (let i = 0; i < DOB_MONTHS.length; i++) {
            if (DOB_MONTHS[i].toLowerCase() === key) return i + 1;
        }
        return 0;
    }
    function dobParts(year, month, day) {
        if (year < 1800 || year > 3000 || month < 1 || month > 12 || day < 1 || day > 31) return null;
        const dim = daysInMonth(year, month);
        if (day > dim) return null;
        return { year: year, month: month, day: day };
    }
    function daysInMonth(year, month) {
        return new Date(year, month, 0).getDate();
    }
    function pad2(n) {
        return (n < 10 ? '0' : '') + n;
    }
    function isoDob(p) {
        return p.year + '-' + pad2(p.month) + '-' + pad2(p.day);
    }

    function labelFor(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    }




    // Render the AI-context text block as readable cards: "Label: a; b" lines
    // become titled sections with one item per line; [bracketed] metadata
    // shows as small chips.
    function aiCtxItem(s) {
        return esc(s).replace(/\[([^\]]+)\]/g, '<span class="ai-ctx-tag">$1</span>');
    }
    function aiContextHtml(text) {
        let html = '<div class="ai-ctx">';
        for (const raw of text.split('\n')) {
            const line = raw.trim();
            if (!line) continue;
            const banner = line.match(/^-+\s*(.*?)\s*-+$/);
            if (banner) {
                html += '<div class="ai-ctx-banner">' + esc(banner[1]) + '</div>';
                continue;
            }
            const m = line.match(/^([A-Z][A-Za-z ()/—-]{1,60}?):\s*(.*)$/);
            if (!m) {
                html += '<div class="ai-ctx-text">' + aiCtxItem(line) + '</div>';
                continue;
            }
            html += '<div class="ai-ctx-sec"><div class="ai-ctx-head">' + esc(m[1]) + '</div>';
            const items = m[2].split(';').map(x => x.trim()).filter(Boolean);
            if (items.length > 1) {
                html += '<ul>';
                for (const it of items) html += '<li>' + aiCtxItem(it) + '</li>';
                html += '</ul>';
            } else {
                html += '<div class="ai-ctx-text">' + aiCtxItem(m[2]) + '</div>';
            }
            html += '</div>';
        }
        return html + '</div>';
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
        navStack: [],
        explainResult: null,

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
                    if (typeof HealthReview !== 'undefined' && HealthReview.maybeNotify) {
                        HealthReview.maybeNotify(this.overview);
                    }
                    if (this.route.view === 'index') this.render();
                }
            } catch (e) {
                /* the hub stays usable without the overview */
            }
        },

        go(view, section, opts) {
            opts = opts || {};
            if (view === 'vitals' || section === 'vitals') {
                if (typeof window.openEmergency === 'function') {
                    window.openEmergency();
                    return;
                }
            }
            const destSection = section || null;
            // Leaving the index: remember the scroll position so Back lands
            // where the user was instead of jumping to the top.
            const before = this.root ? this.root.querySelector('.hub-scroll') : null;
            if (before && this.route && this.route.view === 'index') {
                this._indexScroll = before.scrollTop;
            }
            if (!opts.skipPush &&
                (this.route.view !== view || this.route.section !== destSection)) {
                this.pushReturn({
                    kind: 'hub',
                    view: this.route.view,
                    section: this.route.section
                });
                try { history.pushState({ hubNav: true }, ''); } catch (e) {}
            }
            this.route = { view: view, section: destSection };
            this.openIndex = null;
            this.editIndex = null;
            this.adding = false;
            this.filter = '';
            this.render();
            const scroller = this.root ? this.root.querySelector('.hub-scroll') : null;
            if (scroller) scroller.scrollTop = (view === 'index' && this._indexScroll) ? this._indexScroll : 0;
        },

        pushReturn(frame) {
            if (!frame) return;
            const last = this.navStack.length ? this.navStack[this.navStack.length - 1] : null;
            if (last && last.kind === frame.kind && last.view === frame.view &&
                last.section === frame.section) return;
            this.navStack.push(frame);
        },

        // Always the previous screen: form → list, list → wherever we came
        // from (hub, emergency card, or another section). Never skip a level.
        backOneLevel() {
            if (this.adding || this.editIndex !== null) {
                this.adding = false;
                this.editIndex = null;
                this.render();
                return;
            }
            const prev = this.navStack.pop();
            if (!prev || prev.kind === 'hub' && prev.view === 'index' && !prev.section) {
                this.go('index', null, { skipPush: true });
                return;
            }
            if (prev.kind === 'emergency') {
                this.go(prev.view || 'index', prev.section, { skipPush: true });
                if (typeof window.openEmergency === 'function') window.openEmergency();
                return;
            }
            this.go(prev.view, prev.section, { skipPush: true });
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
            if (id === 'digest' || id === 'visit') return null;
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
            else if (kind === 'visit') html += '<div id="hub-tool" class="hub-tool"><em>Preparing your visit brief…</em></div>';
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
                if (id === 'medications' || id === 'supplements') {
                    const dose = toText(item.dose) || toText(item.dosage);
                    const freq = toText(item.frequency);
                    html += '<span class="hub-row-sub hub-row-meds">';
                    html += '<span><em>Dose</em> ' + esc(dose || '\u2014') + '</span>';
                    html += '<span><em>Frequency</em> ' + esc(freq || '\u2014') + '</span>';
                    html += '</span>';
                } else {
                    const sub = itemSubtitle(id, item);
                    if (sub) html += '<span class="hub-row-sub">' + esc(sub) + '</span>';
                }
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
                if (id === 'test_results') {
                    html += '<button class="hub-btn" data-explain="' + index + '"><i class="fas fa-comment-medical"></i> Explain this result</button>';
                }
                html += '<button class="hub-btn danger" data-delete="' + index + '"><i class="fas fa-trash"></i> Delete</button>';
                html += '</div>';
                if (id === 'test_results' && this.explainResult && this.explainResult.index === index) {
                    html += this.explainHtml(this.explainResult.explanation);
                }
                html += '</div>';
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
            if (id === 'diary' && window.HealthDictation && !HealthDictation.pillAvailable()) {
                // No pill on this device — point at the OS voice typing.
                html += '<div class="hub-mic-bar" style="margin:8px 0 12px; padding:10px; background:#f0f4ff; border-radius:8px; font-size:0.85rem; color:#555;">' +
                    '<i class="fas fa-microphone"></i> Tip: tap into the Entry field. ' + esc(HealthDictation.osDictationHint()) + '</div>';
            }
            html += '<div class="hub-row-actions">';
            html += '<button class="hub-btn primary" data-save="' + index + '"><i class="fas fa-check"></i> Save</button>';
            html += '</div></div>';
            return html;
        },

        inputHtml(field, value) {
            if (field.heading) {
                return '<div class="hub-form-group">' + esc(field.heading) + '</div>';
            }
            const id = 'hf-' + field.key;
            let html = '<label class="hub-input-label" for="' + id + '">' + esc(field.label) +
                (field.required ? ' *' : '') + '</label>';
            if (field.hint) {
                html += '<div class="hub-field-hint">' + esc(field.hint) + '</div>';
            }
            if (field.type === 'textarea') {
                html += '<textarea class="hub-input" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="textarea" rows="3">' + esc(toText(value)) + '</textarea>';
            } else if (field.type === 'list') {
                const lines = Array.isArray(value) ? value.map(toText).join('\n') : toText(value);
                html += '<textarea class="hub-input" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="list" rows="4">' + esc(lines) + '</textarea>';
            } else if (field.type === 'dob') {
                html += '<div class="hub-dob" data-dob="1">';
                html += '<div class="hub-dob-row">';
                html += '<input class="hub-input hub-dob-text" id="' + id + '" data-key="' + esc(field.key) +
                    '" data-type="text" type="text" autocomplete="off" autocapitalize="off" ' +
                    'placeholder="15/3/1954 or 15 Mar 1954" value="' + esc(toText(value)) + '">';
                html += '<button type="button" class="hub-btn hub-dob-toggle" aria-expanded="false" ' +
                    'title="Open calendar with separate year and month">' +
                    '<i class="fas fa-calendar-alt"></i></button>';
                html += '</div>';
                html += '<div class="hub-dob-picker">';
                html += '<label class="hub-input-label">Year</label>' +
                    '<select class="hub-input hub-dob-year"></select>';
                html += '<label class="hub-input-label">Month</label>' +
                    '<select class="hub-input hub-dob-month"></select>';
                html += '<label class="hub-input-label">Day</label>' +
                    '<select class="hub-input hub-dob-day"></select>';
                html += '<div class="hub-row-actions">';
                html += '<button type="button" class="hub-btn primary hub-dob-apply">Use this date</button>';
                html += '<button type="button" class="hub-btn hub-dob-cancel">Cancel</button>';
                html += '</div></div></div>';
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
                const t = (field.type === 'date' || field.type === 'tel' || field.type === 'number')
                    ? field.type : 'text';
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
                const field = schema.fields[i];
                if (field.heading) {
                    html += '<div class="hub-form-group">' + esc(field.heading) + '</div>';
                    continue;
                }
                const value = (id === 'personal' && field.key === 'name')
                    ? (this.profile && this.profile.name)
                    : obj[field.key];
                html += this.inputHtml(field, value);
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

        explainHtml(exp) {
            if (!exp) return '';
            let html = '<div class="hub-note ai">';
            html += '<span class="hub-prov ai_inferred">AI</span> <strong>About ' +
                esc(exp.test_name || 'this result') + '</strong>';
            if (exp.value) html += ' — ' + esc(String(exp.value));
            if (exp.date) html += ' <span class="hub-when">' + esc(String(exp.date)) + '</span>';
            const sug = exp.suggestions || [];
            const qs = exp.questions_for_doctor || [];
            if (exp.reason && !sug.length && !qs.length) {
                html += '<br>' + esc(exp.reason);
            }
            for (let i = 0; i < sug.length; i++) {
                html += '<br><strong>' + esc(sug[i].title) + '</strong><br>' + esc(sug[i].detail);
                if (sug[i].cites && sug[i].cites.length) {
                    html += '<div class="hub-cites">Based on: ' + esc(sug[i].cites.join(', ')) + '</div>';
                }
            }
            for (let i = 0; i < qs.length; i++) {
                html += '<br>' + esc(qs[i].question || '');
                if (qs[i].context) html += '<br>' + esc(qs[i].context);
            }
            html += '</div>';
            html += this.disclaimerHtml(exp.disclaimer);
            return html;
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
        // The Emergency Card hub tile opens the real card (openEmergency).
        // This body is only a fallback if that function is missing.
        vitalsBody() {
            let html = '<div class="hub-note">';
            html += 'This card is assembled from Personal Details, Medications and Conditions. Edit those pages to add or update it.';
            html += '</div>';
            html += '<div class="hub-row-actions" style="padding:0 14px 14px;">';
            html += '<button class="hub-btn primary" id="hub-open-vitals">Open emergency card</button>';
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
            html += '<label class="hub-check"><input type="checkbox" id="hub-notifications-enabled"' +
                (s.notifications_enabled === true ? ' checked' : '') + '> Notify me when a reminder is due</label>';
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
            html += '<div class="hub-form" style="margin-top:20px; border-top:1px solid #e3e7ea; padding-top:16px;">';
            html += '<div class="hub-form-title">Stored documents</div>';
            html += '<div id="hub-docs"><div class="hub-note"><strong>' + docs.length + '</strong> document(s) stored — loading details…</div></div>';
            html += '<div class="hub-row-actions"><button class="hub-btn" id="hub-export"><i class="fas fa-download"></i> Download my whole record (zip)</button></div>';
            html += '<div class="hub-form-hint">Documents marked "keep" are never auto-deleted. The export is also your backup.</div>';
            html += '</div>';
            return html;
        },

        async loadDocuments() {
            const el = this.root.querySelector('#hub-docs');
            if (!el) return;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/documents');
                const data = await resp.json();
                const docs = (data && Array.isArray(data.documents)) ? data.documents.slice() : [];
                docs.sort((a, b) => new Date(b.uploaded_at || 0) - new Date(a.uploaded_at || 0));
                if (!docs.length) {
                    el.innerHTML = '<div class="hub-note">No documents stored.</div>';
                    return;
                }
                let html = '';
                for (let i = 0; i < docs.length; i++) {
                    const d = docs[i];
                    html += '<div class="hub-note' + (d.expiring_soon ? ' warn' : '') + '">';
                    html += '<strong>' + esc(d.original_name || d.stored_name || 'Document') + '</strong>';
                    const up = d.uploaded_at ? new Date(d.uploaded_at) : null;
                    if (up && !isNaN(up)) {
                        html += '<br>' + esc(up.toLocaleDateString() + ' ' +
                            up.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
                    }
                    if (d.keep_forever) {
                        html += '<br>Kept forever.';
                    } else if (d.expires_at) {
                        html += '<br>Deleted after ' + esc(String(d.expires_at).slice(0, 10)) +
                            (d.expiring_soon ? ' — expiring soon' : '');
                    }
                    html += '<br><label class="hub-check"><input type="checkbox" data-doc-keep="' +
                        esc(d.stored_name || '') + '"' + (d.keep_forever ? ' checked' : '') +
                        '> Keep this document</label>';
                    html += '</div>';
                }
                el.innerHTML = html;
                const self = this;
                const boxes = el.querySelectorAll('[data-doc-keep]');
                for (let i = 0; i < boxes.length; i++) {
                    boxes[i].addEventListener('change', function () {
                        self.setDocKeep(this.getAttribute('data-doc-keep'), this.checked);
                    });
                }
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not load document list.</div>';
            }
        },

        async setDocKeep(storedName, keep) {
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/documents', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ stored_name: storedName, keep_forever: !!keep })
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not update the document.', true);
                } else {
                    this.status(keep ? 'Document will be kept.' : 'Document follows the retention period.');
                }
            } catch (e) {
                this.status('Network error while updating the document.', true);
            }
        },

        async exportRecord() {
            if (this.busy) return;
            this.busy = true;
            this.status('Preparing your export…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/export');
                this.busy = false;
                if (!resp.ok) {
                    let msg = 'Could not build the export.';
                    try { const d = await resp.json(); if (d && d.error) msg = d.error; } catch (e) {}
                    this.status(msg, true);
                    return;
                }
                const blob = await resp.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'health-profile-export.zip';
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(() => URL.revokeObjectURL(url), 10000);
                this.status('Export downloaded.');
            } catch (e) {
                this.busy = false;
                this.status('Network error while exporting.', true);
            }
        },

        async saveAdviceSettings() {
            if (this.busy) return;
            const ai = this.root.querySelector('#hub-ai-enabled');
            const rem = this.root.querySelector('#hub-reminders-enabled');
            const nfy = this.root.querySelector('#hub-notifications-enabled');
            const freq = this.root.querySelector('#hub-digest-frequency');
            const loc = this.root.querySelector('#hub-advice-locale');
            if (!ai || !rem || !nfy || !freq || !loc) return;
            // Enabling alerts needs the OS/browser permission first; without it
            // the toggle would silently do nothing.
            if (nfy.checked && typeof Notification !== 'undefined' &&
                    Notification.permission === 'default') {
                try { await Notification.requestPermission(); } catch (e) {}
            }
            if (nfy.checked && (typeof Notification === 'undefined' ||
                    Notification.permission !== 'granted')) {
                this.status('Notifications are blocked by the browser — enable them in the browser/OS settings first.', true);
                return;
            }
            this.busy = true;
            this.status('Saving…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/advice-settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ai_enabled: ai.checked,
                        reminders_enabled: rem.checked,
                        notifications_enabled: nfy.checked,
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

        async explainTest(index) {
            if (this.busy) return;
            this.busy = true;
            this.status('Explaining this result…');
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/explain-test', {
                    method: 'POST',
                    body: JSON.stringify({ index: index })
                });
                const data = await resp.json();
                this.busy = false;
                if (!resp.ok || !data.success) {
                    this.status((data && data.error) ? data.error : 'Could not explain this result.', true);
                    return;
                }
                this.explainResult = { index: index, explanation: data.explanation || {} };
                this.openIndex = index;
                this.render();
                const exp = this.explainResult.explanation;
                this.status(exp.reason ? exp.reason : 'Explanation ready.', !!exp.reason);
            } catch (e) {
                this.busy = false;
                this.status('Network error while explaining this result.', true);
            }
        },

        async actOnReminder(id, action) {
            if (this.busy) return;
            const reminder = this.findReminder(id);
            if (!reminder) return;
            this.busy = true;
            this.status(action === 'complete' ? 'Marking done…' : 'Snoozing…');
            try {
                const r = await HealthReview.actOnReminder(
                    (u, i) => AuthHelper.authenticatedFetch(u, i), reminder, action, 7);
                this.busy = false;
                if (!r.ok) {
                    this.status((r.data && r.data.error) ? r.data.error : 'Could not update reminder.', true);
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

                const changes = d.recent_changes || [];
                if (changes.length) {
                    html += '<div class="hub-group-label">What changed</div>';
                    for (let i = 0; i < changes.length && i < 20; i++) {
                        const c = changes[i];
                        const when = String(c.when || '').slice(0, 10);
                        html += '<div class="hub-note">' + esc(when) + ' — ' +
                            esc(labelFor(c.category || '').toLowerCase()) + ': ' +
                            esc(c.name || 'item') + ' <em>' + esc(c.event || '') + '</em>' +
                            (c.detail ? '<br><span style="opacity:.7">' + esc(c.detail) + '</span>' : '') +
                            '</div>';
                    }
                }

                const expiring = d.expiring_documents || [];
                if (expiring.length) {
                    html += '<div class="hub-group-label">Documents nearing expiry</div>';
                    for (let i = 0; i < expiring.length; i++) {
                        const doc = expiring[i];
                        html += '<div class="hub-note warn"><i class="fas fa-file-circle-exclamation"></i> ' +
                            esc(doc.original_name || doc.stored_name || 'Document') +
                            ' is deleted in ' + esc(String(doc.days_until_expiry)) + ' day(s). ' +
                            'Open Settings to keep it.</div>';
                    }
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

        visitLine(label, value) {
            if (value === null || value === undefined || value === '') return '';
            if (Array.isArray(value) && !value.length) return '';
            return '<div class="hub-field"><span class="hub-field-label">' + esc(label) +
                '</span><span class="hub-field-value">' + esc(Array.isArray(value) ? value.join(', ') : value) +
                '</span></div>';
        },

        visitText(brief) {
            const lines = [];
            lines.push('GP visit brief' + (brief.name ? ' — ' + brief.name : ''));
            if (brief.date_of_birth) lines.push('Date of birth: ' + brief.date_of_birth);
            if (brief.age) lines.push('Age: ' + brief.age);
            if (brief.language) lines.push('Language: ' + brief.language);
            if (brief.gp_name) lines.push('GP: ' + brief.gp_name + (brief.gp_phone ? ' ' + brief.gp_phone : ''));
            const allergies = brief.allergies || [];
            lines.push('Allergies:');
            if (allergies.length) {
                for (let i = 0; i < allergies.length; i++) lines.push('  - ' + allergies[i]);
            } else {
                lines.push('  none recorded');
            }
            const conds = brief.conditions || [];
            lines.push('Conditions:');
            if (conds.length) {
                for (let i = 0; i < conds.length; i++) lines.push('  - ' + conds[i]);
            } else {
                lines.push('  none recorded');
            }
            const meds = brief.medications || [];
            if (meds.length) {
                lines.push('Current medications:');
                for (let i = 0; i < meds.length; i++) {
                    const m = meds[i];
                    lines.push('  - ' + (m.label || m.name || '') +
                        (m.dose && String(m.label || '').indexOf(m.dose) === -1 ? ' ' + m.dose : '') +
                        (m.frequency && String(m.label || '').indexOf(m.frequency) === -1 ? ' ' + m.frequency : ''));
                }
            }
            const thinners = brief.anticoagulants || [];
            if (thinners.length) lines.push('Blood thinners: ' + thinners.join(', '));
            const tests = brief.abnormal_tests || [];
            if (tests.length) {
                lines.push('Recent results outside range:');
                for (let i = 0; i < tests.length; i++) {
                    const t = tests[i];
                    lines.push('  - ' + t.test_name + ': ' + t.value +
                        (t.reference_range ? ' (ref ' + t.reference_range + ')' : '') +
                        (t.flag ? ' [' + t.flag + ']' : '') +
                        (t.date ? ' ' + t.date : ''));
                }
            }
            const back = brief.normalised_tests || [];
            if (back.length) {
                lines.push('Back in range (previously abnormal):');
                for (let i = 0; i < back.length; i++) {
                    const t = back[i];
                    lines.push('  - ' + t.test_name + ': ' + t.value +
                        (t.reference_range ? ' (ref ' + t.reference_range + ')' : '') +
                        (t.date ? ' ' + t.date : ''));
                }
            }
            const qs = brief.questions_for_doctor || [];
            if (qs.length) {
                lines.push('Questions to ask:');
                for (let i = 0; i < qs.length; i++) {
                    lines.push('  - ' + qs[i].question);
                }
            }
            if (brief.advance_care) lines.push('Advance care: ' + brief.advance_care);
            lines.push('');
            lines.push('Prepared from my Dr. Health record. Not a medical document.');
            return lines.join('\n');
        },

        async loadVisitBrief() {
            const el = this.root.querySelector('#hub-tool');
            if (!el) return;
            try {
                const resp = await AuthHelper.authenticatedFetch('/api/health-profile/visit-brief');
                const data = await resp.json();
                const brief = (data && data.brief) ? data.brief : null;
                if (!brief) {
                    el.innerHTML = '<div class="hub-note error">Could not build a visit brief.</div>';
                    return;
                }
                let html = '<div class="hub-note">Show or copy this at your appointment. It is assembled from current medications, conditions and recent labs — not a second record.</div>';
                html += this.visitLine('Name', brief.name);
                html += this.visitLine('Date of birth', brief.date_of_birth);
                html += this.visitLine('Age', brief.age);
                html += this.visitLine('Language', brief.language);
                html += this.visitLine('GP', [brief.gp_name, brief.gp_phone].filter(Boolean).join(' · '));
                html += '<div class="hub-group-label">Allergies</div>';
                const allergies = brief.allergies || [];
                if (allergies.length) {
                    for (let i = 0; i < allergies.length; i++) {
                        html += '<div class="hub-note warn"><i class="fas fa-triangle-exclamation"></i> ' + esc(allergies[i]) + '</div>';
                    }
                } else {
                    html += '<div class="hub-note">none recorded</div>';
                }
                html += '<div class="hub-group-label">Conditions</div>';
                const conds = brief.conditions || [];
                if (conds.length) {
                    for (let i = 0; i < conds.length; i++) {
                        html += '<div class="hub-note">' + esc(conds[i]) + '</div>';
                    }
                } else {
                    html += '<div class="hub-note">none recorded</div>';
                }
                const meds = brief.medications || [];
                if (meds.length) {
                    html += '<div class="hub-group-label">Current medications</div>';
                    for (let i = 0; i < meds.length; i++) {
                        const m = meds[i] || {};
                        html += '<div class="hub-note"><strong>' + esc(m.name || '') + '</strong>';
                        if (m.dose || m.frequency) {
                            html += '<br>' + esc([m.dose, m.frequency].filter(Boolean).join(' · '));
                        }
                        html += '</div>';
                    }
                }
                if (brief.anticoagulants && brief.anticoagulants.length) {
                    html += '<div class="hub-note warn"><strong>Blood thinners</strong><br>' +
                        esc(brief.anticoagulants.join(', ')) + '</div>';
                }
                const tests = brief.abnormal_tests || [];
                if (tests.length) {
                    html += '<div class="hub-group-label">Results outside range</div>';
                    for (let i = 0; i < tests.length; i++) {
                        const t = tests[i];
                        html += '<div class="hub-note"><strong>' + esc(t.test_name) + '</strong> ' +
                            esc(t.value || '') +
                            (t.reference_range ? ' · ref ' + esc(t.reference_range) : '') +
                            (t.flag ? ' · ' + esc(t.flag) : '') +
                            (t.date ? '<br><span class="hub-when">' + esc(t.date) + '</span>' : '') +
                            '</div>';
                    }
                }
                const back = brief.normalised_tests || [];
                if (back.length) {
                    html += '<div class="hub-group-label">Back in range</div>';
                    for (let i = 0; i < back.length; i++) {
                        const t = back[i];
                        html += '<div class="hub-note ok"><strong>' + esc(t.test_name) + '</strong> ' +
                            esc(t.value || '') +
                            (t.reference_range ? ' · ref ' + esc(t.reference_range) : '') +
                            ' — normal now (was out of range before)' +
                            (t.date ? '<br><span class="hub-when">' + esc(t.date) + '</span>' : '') +
                            '</div>';
                    }
                }
                const qs = brief.questions_for_doctor || [];
                if (qs.length) {
                    html += '<div class="hub-group-label">Questions to ask</div>';
                    for (let i = 0; i < qs.length; i++) {
                        html += '<div class="hub-note"><strong>' + esc(qs[i].question) + '</strong>';
                        if (qs[i].context) html += '<br>' + esc(qs[i].context);
                        html += '</div>';
                    }
                }
                if (brief.advance_care) {
                    html += '<div class="hub-note warn"><strong>Advance care</strong><br>' +
                        esc(brief.advance_care) + '</div>';
                }
                html += '<div class="hub-row-actions" style="padding:8px 14px 14px;">';
                html += '<button class="hub-btn primary" id="hub-visit-copy"><i class="fas fa-copy"></i> Copy</button>';
                html += '</div>';
                html += this.disclaimerHtml('Prepared from your current record. Not a medical document.');
                el.innerHTML = html;
                const copyBtn = el.querySelector('#hub-visit-copy');
                const text = this.visitText(brief);
                if (copyBtn) {
                    copyBtn.addEventListener('click', function () {
                        const done = function () { copyBtn.textContent = 'Copied'; };
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(text).then(done).catch(function () {
                                window.prompt('Copy this visit brief:', text);
                            });
                        } else {
                            window.prompt('Copy this visit brief:', text);
                        }
                    });
                }
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not build a visit brief.</div>';
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

        // Dictation lives in static/health_dictation.js, shared with the
        // health website.  Kept as a delegate for existing callers.
        wireMicPills(rootEl) {
            if (window.HealthDictation) HealthDictation.wire(rootEl);
        },

        // Native <input type="date"> is a poor fit for a 70-year-old DOB:
        // some phones force the spinner and make you walk month by month.
        // This picker has independent year / month / day lists. The text
        // field stays free-typed either way.
        wireDobPicker() {
            const wrap = this.root ? this.root.querySelector('[data-dob]') : null;
            if (!wrap) return;
            const input = wrap.querySelector('.hub-dob-text');
            const toggle = wrap.querySelector('.hub-dob-toggle');
            const picker = wrap.querySelector('.hub-dob-picker');
            const yearEl = wrap.querySelector('.hub-dob-year');
            const monthEl = wrap.querySelector('.hub-dob-month');
            const dayEl = wrap.querySelector('.hub-dob-day');
            const apply = wrap.querySelector('.hub-dob-apply');
            const cancel = wrap.querySelector('.hub-dob-cancel');
            if (!input || !toggle || !picker || !yearEl || !monthEl || !dayEl) return;

            function fillYears(selected) {
                const now = new Date().getFullYear();
                const start = now - 120;
                let html = '';
                for (let y = now; y >= start; y--) {
                    html += '<option value="' + y + '"' + (y === selected ? ' selected' : '') + '>' + y + '</option>';
                }
                if (selected && (selected > now || selected < start)) {
                    html = '<option value="' + selected + '" selected>' + selected + '</option>' + html;
                }
                yearEl.innerHTML = html;
            }
            function fillMonths(selected) {
                let html = '';
                for (let i = 0; i < DOB_MONTHS.length; i++) {
                    const n = i + 1;
                    html += '<option value="' + n + '"' + (n === selected ? ' selected' : '') + '>' +
                        DOB_MONTHS[i] + '</option>';
                }
                monthEl.innerHTML = html;
            }
            function fillDays(year, month, selected) {
                const dim = daysInMonth(year, month);
                let html = '';
                for (let d = 1; d <= dim; d++) {
                    html += '<option value="' + d + '"' + (d === selected ? ' selected' : '') + '>' + d + '</option>';
                }
                dayEl.innerHTML = html;
                if (selected > dim) dayEl.value = String(dim);
            }
            function currentParts() {
                return {
                    year: Number(yearEl.value),
                    month: Number(monthEl.value),
                    day: Number(dayEl.value)
                };
            }
            function openPicker() {
                const parsed = parseDob(input.value) || {
                    year: new Date().getFullYear() - 70,
                    month: 1,
                    day: 1
                };
                fillYears(parsed.year);
                fillMonths(parsed.month);
                fillDays(parsed.year, parsed.month, parsed.day);
                picker.classList.add('is-open');
                toggle.setAttribute('aria-expanded', 'true');
            }
            function closePicker() {
                picker.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
            }

            toggle.addEventListener('click', function () {
                if (picker.classList.contains('is-open')) closePicker();
                else openPicker();
            });
            yearEl.addEventListener('change', function () {
                const p = currentParts();
                fillDays(p.year, p.month, p.day);
            });
            monthEl.addEventListener('change', function () {
                const p = currentParts();
                fillDays(p.year, p.month, p.day);
            });
            if (apply) {
                apply.addEventListener('click', function () {
                    const p = currentParts();
                    if (!dobParts(p.year, p.month, p.day)) return;
                    input.value = isoDob(p);
                    closePicker();
                });
            }
            if (cancel) cancel.addEventListener('click', closePicker);
        },

        // ---------- Wiring ----------
        wireSection(id) {
            const self = this;
            const kind = this.kindOf(id);

            const back = this.root.querySelector('#hub-back');
            if (back) back.addEventListener('click', () => {
                if (history.state && history.state.hubNav) {
                    history.back();
                    return;
                }
                self.backOneLevel();
            });

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
                this.wireDobPicker();
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
                const exp = this.root.querySelector('#hub-export');
                if (exp) exp.addEventListener('click', () => self.exportRecord());
                this.loadDocuments();
            } else if (kind === 'interactions') {
                this.loadInteractions();
            } else if (kind === 'summary') {
                this.loadSummary();
            } else if (kind === 'digest') {
                this.loadDigest();
            } else if (kind === 'visit') {
                this.loadVisitBrief();
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

            const explains = root.querySelectorAll('[data-explain]');
            for (let i = 0; i < explains.length; i++) {
                explains[i].addEventListener('click', function () {
                    self.explainTest(parseInt(this.getAttribute('data-explain'), 10));
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

            this.wireMicPills(this.root);
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
                if ((id === 'medications' || id === 'conditions') &&
                    typeof window.syncEmergencyFromServer === 'function') {
                    window.syncEmergencyFromServer().catch(function () {});
                }
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
                if (id === 'personal' && typeof window.syncEmergencyFromServer === 'function') {
                    window.syncEmergencyFromServer().catch(function () {});
                }
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
                    ? aiContextHtml(text)
                    : '<div class="hub-note">No health context stored yet. Add some information first.</div>';
            } catch (e) {
                el.innerHTML = '<div class="hub-note error">Could not load summary.</div>';
            }
        }
    };

    window.DrHealthHub = DrHealthHub;
})();
