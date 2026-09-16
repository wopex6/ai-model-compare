/*
 * Shared "quick check" prompt used by the health-profile website and the
 * Dr. Health PWA.
 *
 * The backend decides *what* to ask and *whether* it is polite to ask at all
 * (see ai_compare/health_freshness.py). This module owns the interaction:
 * fetching the queue, showing one question at a time, and posting the answer.
 *
 * One question at a time is the whole point. A list of twelve things to verify
 * gets ignored; a single yes/no with a visible "1 of 4" gets answered. The card
 * removes itself as soon as the queue is empty and never reappears within the
 * server-side cooldown.
 *
 * Markup is intentionally plain and class-prefixed so each page can style it to
 * look native; only the behaviour is shared.
 */
(function () {
    'use strict';

    // Fields worth correcting inline. Anything more belongs in the full editor.
    const EDIT_FIELDS = {
        medications: [['dose', 'Dose'], ['frequency', 'How often']],
        supplements: [['dose', 'Dose'], ['frequency', 'How often']],
        conditions: [['details', 'Details']],
        symptoms: [['severity', 'Severity'], ['frequency', 'How often']],
    };

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function ageText(entry) {
        if (entry.days_since == null) return 'Never confirmed';
        if (entry.days_since < 1) return 'Confirmed today';
        return 'Last confirmed ' + entry.days_since + ' day' +
            (entry.days_since === 1 ? '' : 's') + ' ago';
    }

    function create(container, opts) {
        const o = opts || {};
        const fetcher = o.fetcher || window.fetch.bind(window);
        const p = o.prefix || 'hr';
        let queue = [];
        let proposals = [];
        let state = { due: 0, nudge_due: false };

        async function call(method, body) {
            const init = { method: method };
            if (body) {
                init.headers = { 'Content-Type': 'application/json' };
                init.body = JSON.stringify(body);
            }
            const resp = await fetcher('/api/health-profile/review-queue', init);
            if (!resp.ok) throw new Error('review-queue ' + resp.status);
            return resp.json();
        }

        function absorb(data) {
            queue = data.queue || [];
            proposals = data.pending_changes || [];
            state = { due: data.due || 0, nudge_due: !!data.nudge_due };
            if (typeof o.onCount === 'function') o.onCount(state);
            render();
        }

        async function act(entry, action, extra) {
            const payload = Object.assign({ action: action }, extra || {});
            if (entry) {
                payload.category = entry.category;
                if (entry.kind === 'group') payload.group_key = entry.group_key;
                else payload.index = entry.index;
            }
            try {
                absorb(await call('POST', payload));
                if (typeof o.onUpdated === 'function') o.onUpdated(action, entry);
            } catch (err) {
                // A stale index means the profile moved under us; a reload is
                // the honest recovery rather than guessing at the new position.
                try { absorb(await call('GET')); } catch (e) { hide(); }
            }
        }

        function hide() {
            container.innerHTML = '';
            container.style.display = 'none';
        }

        function render() {
            const entry = queue[0];
            const showQ = !!(state.nudge_due && queue.length);
            if (!showQ && !proposals.length) return hide();
            const total = Math.max(state.due, queue.length);
            const canEdit = showQ && entry.kind === 'item' && EDIT_FIELDS[entry.category];

            let html = '<div class="' + p + '-card" data-priority="' +
                esc(showQ ? entry.priority : 'medium') + '">' +
                '<div class="' + p + '-head">' +
                    '<span class="' + p + '-title">Quick check</span>' +
                    (showQ ? '<span class="' + p + '-count">1 of ' + total + '</span>' : '') +
                    '<button type="button" class="' + p + '-close" data-act="dismiss" ' +
                        'title="Not now — ask again later">&times;</button>' +
                '</div>';
            if (showQ) {
                html +=
                    '<div class="' + p + '-q">' + esc(entry.question) + '</div>' +
                    (entry.detail ? '<div class="' + p + '-detail">' + esc(entry.detail) + '</div>' : '') +
                    '<div class="' + p + '-why">' + esc(ageText(entry)) + '</div>' +
                    '<div class="' + p + '-actions">' +
                        '<button type="button" class="' + p + '-btn ' + p + '-yes" data-act="confirm">Yes, unchanged</button>' +
                        (canEdit ? '<button type="button" class="' + p + '-btn" data-act="edit">Changed\u2026</button>' : '') +
                        (entry.actions.indexOf('stopped') >= 0
                            ? '<button type="button" class="' + p + '-btn" data-act="stopped">' +
                              (entry.category === 'conditions' || entry.category === 'symptoms' ? 'Resolved' : 'Stopped') +
                              '</button>' : '') +
                        '<button type="button" class="' + p + '-btn" data-act="snooze">Later</button>' +
                    '</div>' +
                    '<div class="' + p + '-edit" hidden></div>';
            }
            // AI-inferred corrections parked for review: they must never apply
            // silently, so each one asks before touching the stored value.
            proposals.slice(0, 3).forEach(function (prop, i) {
                html += '<div class="' + p + '-proposal">' +
                    '<div class="' + p + '-q">Update ' + esc(prop.label) + ' — ' +
                        esc(prop.field) + ': &ldquo;' + esc(prop.from || '(blank)') +
                        '&rdquo; &rarr; &ldquo;' + esc(prop.to) + '&rdquo;?</div>' +
                    '<div class="' + p + '-actions">' +
                        '<button type="button" class="' + p + '-btn ' + p + '-yes" data-paccept="' + i + '">Apply</button>' +
                        '<button type="button" class="' + p + '-btn" data-preject="' + i + '">Not correct</button>' +
                    '</div></div>';
            });
            html += '</div>';

            container.style.display = '';
            container.innerHTML = html;
            container.querySelectorAll('[data-act]').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    onAction(entry, btn.getAttribute('data-act'));
                });
            });
            container.querySelectorAll('[data-paccept]').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    actProposal(parseInt(btn.getAttribute('data-paccept'), 10), 'accept');
                });
            });
            container.querySelectorAll('[data-preject]').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    actProposal(parseInt(btn.getAttribute('data-preject'), 10), 'reject');
                });
            });
        }

        async function actProposal(index, action) {
            try {
                absorb(await call('POST', { action: action, proposal_index: index }));
                if (typeof o.onUpdated === 'function') o.onUpdated(action, null);
            } catch (err) {
                try { absorb(await call('GET')); } catch (e) { hide(); }
            }
        }

        function onAction(entry, action) {
            if (action === 'edit') return showEditor(entry);
            if (action === 'snooze') return act(entry, 'snooze', { days: 14 });
            if (action === 'dismiss') return act(null, 'dismiss');
            act(entry, action);
        }

        function showEditor(entry) {
            const box = container.querySelector('.' + p + '-edit');
            if (!box) return;
            const fields = EDIT_FIELDS[entry.category] || [];
            const values = entry.values || {};
            box.hidden = false;
            box.innerHTML = fields.map(function (f) {
                return '<label class="' + p + '-field">' + esc(f[1]) +
                    '<input type="text" data-field="' + esc(f[0]) + '" value="' + esc(values[f[0]] || '') + '"></label>';
            }).join('') +
                '<button type="button" class="' + p + '-btn ' + p + '-yes" data-save="1">Save</button>';

            box.querySelector('[data-save]').addEventListener('click', function () {
                const changes = {};
                box.querySelectorAll('[data-field]').forEach(function (input) {
                    const v = input.value.trim();
                    if (v) changes[input.getAttribute('data-field')] = v;
                });
                if (!Object.keys(changes).length) return act(entry, 'confirm');
                act(entry, 'changed', { changes: changes });
            });
            const first = box.querySelector('input');
            if (first) first.focus();
        }

        async function refresh() {
            try {
                absorb(await call('GET'));
            } catch (err) {
                hide();
            }
        }

        return { refresh: refresh, state: function () { return state; } };
    }

    // Ended items are retired rather than deleted, so every lifecycle list has
    // to be split into what is true now and what is history. Original indices
    // are carried through because the item endpoints address items by
    // position — renumbering here would delete the wrong row.
    const ENDED = ['stopped', 'resolved', 'completed', 'cancelled', 'dismissed', 'expired'];

    function partition(items) {
        const current = [], past = [];
        (items || []).forEach(function (item, idx) {
            const status = String((item && item.status) || '').toLowerCase();
            (ENDED.indexOf(status) >= 0 ? past : current).push({ item: item, idx: idx });
        });
        return { current: current, past: past };
    }

    // "stopped 12 Mar" plus the most recent field change, so a corrected dose
    // is visible without opening anything. Returns escaped HTML.
    function historyNote(item, isPast) {
        let out = '';
        if (isPast && item.ended_on) {
            out += ' <small class="hr-ended">(' + esc(item.status || 'ended') +
                   ' ' + esc(item.ended_on) + ')</small>';
        }
        const h = item.history || [];
        const last = h.length ? h[h.length - 1] : null;
        if (last && last.field !== 'status') {
            out += '<br><small class="hr-changed">' + esc(last.field) + ': ' +
                   esc(last.from) + ' \u2192 ' + esc(last.to) +
                   ' <span class="hr-when">' + esc(String(last.at || '').slice(0, 10)) +
                   '</span></small>';
        }
        return out;
    }

    // Retire or revive an item. Deliberately not a delete: the record is what
    // makes "I stopped that in March" answerable later.
    function setStatus(fetcher, category, index, status) {
        const ending = (status === 'stopped' || status === 'resolved');
        return fetcher('/api/health-profile/item', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: category,
                index: index,
                updates: {
                    status: status,
                    ended_on: ending ? new Date().toISOString().slice(0, 10) : '',
                },
            }),
        });
    }

    // Categories that carry a lifecycle, and the verb each one ends with.
    const END_STATUS = {
        medications: 'stopped', supplements: 'stopped',
        conditions: 'resolved', symptoms: 'resolved',
    };

    // One quiet system notification when reminders need attention — at most
    // once every 20 hours unless the count changes. The user opts in from
    // Settings; nothing here asks for permission on its own.
    function maybeNotify(overview) {
        try {
            const s = (overview && overview.settings) || {};
            if (!s.notifications_enabled) return;
            if (typeof Notification === 'undefined' ||
                Notification.permission !== 'granted') return;
            const c = (overview && overview.reminder_counts) || {};
            const n = (c.overdue || 0) + (c.due_today || 0);
            if (!n) return;
            const last = parseInt(localStorage.getItem('drHealth.lastNotify') || '0', 10);
            const lastN = parseInt(localStorage.getItem('drHealth.lastNotifyCount') || '0', 10);
            if (n === lastN && Date.now() - last < 20 * 3600 * 1000) return;
            const list = (overview && overview.reminders) || [];
            const top = list.find(function (r) { return r.status === 'overdue'; }) ||
                        list.find(function (r) { return r.status === 'due_today'; });
            const note = new Notification('Dr. Health', {
                body: n + ' reminder' + (n === 1 ? ' needs' : 's need') +
                      ' attention' + (top ? ' — ' + top.title : ''),
            });
            note.onclick = function () { try { window.focus(); } catch (e) {} };
            localStorage.setItem('drHealth.lastNotify', String(Date.now()));
            localStorage.setItem('drHealth.lastNotifyCount', String(n));
        } catch (e) { /* notifications are best-effort */ }
    }

    window.HealthReview = {
        mount: create,
        partition: partition,
        historyNote: historyNote,
        setStatus: setStatus,
        maybeNotify: maybeNotify,
        endStatusFor: function (category) { return END_STATUS[category] || ''; },
        hasLifecycle: function (category) { return !!END_STATUS[category]; },
    };
})();
