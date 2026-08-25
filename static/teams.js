/**
 * Teams UI client
 * Handles listing/creating/updating/deleting teams and running deliberations.
 * Authentication is done via the JWT stored by the main app in localStorage.
 */
(function () {
    'use strict';

    // Main chat app stores token as authToken; some standalone pages use auth_token.
    const LS = window.localStorage;
    function getToken() {
        return LS.getItem('authToken') || LS.getItem('auth_token') || null;
    }

    // --- DOM refs ---
    const els = {
        grid: document.getElementById('character-grid'),
        coordinator: document.getElementById('team-coordinator'),
        name: document.getElementById('team-name'),
        description: document.getElementById('team-description'),
        batch: document.getElementById('team-batch'),
        saveBtn: document.getElementById('save-team-btn'),
        cancelBtn: document.getElementById('cancel-edit-btn'),
        editorTitle: document.getElementById('editor-title'),
        teamList: document.getElementById('team-list'),
        runCard: document.getElementById('run-card'),
        runTeamName: document.getElementById('run-team-name'),
        deliberateMessage: document.getElementById('deliberate-message'),
        runBtn: document.getElementById('run-deliberate-btn'),
        revealAttr: document.getElementById('reveal-attribution'),
        history: document.getElementById('conversation-history'),
        clearHistoryBtn: document.getElementById('clear-history-btn'),
        toast: document.getElementById('toast'),
    };

    let availableCharacters = [];
    let teams = [];
    let editingTeamId = null;
    let selectedMembers = new Set();
    let conversationHistory = {}; // keyed by teamId

    function authHeaders() {
        const t = getToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': t ? `Bearer ${t}` : '',
        };
    }

    function redirectToLogin() {
        window.location.href = '/login';
    }

    // --- Toast ---
    let toastTimer;
    function showToast(msg, type) {
        els.toast.textContent = msg;
        els.toast.className = 'toast show ' + (type || '');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => els.toast.classList.remove('show'), 3500);
    }

    // --- API ---
    async function api(path, opts) {
        opts = opts || {};
        opts.headers = Object.assign({}, authHeaders(), opts.headers || {});
        const res = await fetch(path, opts);
        if (res.status === 401) { redirectToLogin(); return; }
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || `Request failed (${res.status})`);
        }
        return data;
    }

    async function loadData() {
        const data = await api('/api/teams');
        if (!data) return;
        availableCharacters = data.available_characters || [];
        teams = data.teams || [];
        renderCharacters();
        renderTeams();
        if (!getToken()) redirectToLogin();
    }

    // --- Character picker ---
    function renderCharacters() {
        els.grid.innerHTML = '';
        // Team members can be any character except the coordinator itself.
        // Team-only agents (e.g. the built-in deliberation thinkers) are selectable here.
        const members = availableCharacters.filter(c => !c.is_coordinator);
        if (!members.length) {
            els.grid.innerHTML = '<div class="empty-state">No characters available.</div>';
            return;
        }
        // Coordinator dropdown: any routable character or the main coordinator;
        // team-only thinkers are not natural synthesizers.
        els.coordinator.innerHTML = availableCharacters
            .filter(c => c.is_coordinator || !c.team_only)
            .map(c => `<option value="${esc(c.id)}">${esc(c.display_name)}</option>`)
            .join('');

        members.forEach(c => {
            const card = document.createElement('div');
            card.className = 'character-card' + (selectedMembers.has(c.id) ? ' selected' : '');
            card.dataset.id = c.id;
            card.innerHTML = `
                <div class="icon"><i class="fas fa-user-astronaut"></i></div>
                <div class="name">${esc(c.display_name)}</div>
                <div class="domain">${esc(c.domain)}${c.team_only ? ' <span style="color:#888">(team-only)</span>' : ''}</div>
                <div class="check"><i class="fas fa-check-circle"></i></div>
            `;
            card.addEventListener('click', () => {
                if (selectedMembers.has(c.id)) selectedMembers.delete(c.id);
                else selectedMembers.add(c.id);
                card.classList.toggle('selected', selectedMembers.has(c.id));
                updateCoordinatorOptions();
            });
            els.grid.appendChild(card);
        });
    }

    function updateCoordinatorOptions() {
        const current = els.coordinator.value;
        const allowed = availableCharacters.filter(
            c => c.is_coordinator || (!c.team_only && !selectedMembers.has(c.id))
        );
        els.coordinator.innerHTML = allowed
            .map(c => `<option value="${esc(c.id)}">${esc(c.display_name)}</option>`)
            .join('');
        // restore if still valid
        if (allowed.some(c => c.id === current)) els.coordinator.value = current;
    }

    // --- Team list ---
    function renderTeams() {
        els.teamList.innerHTML = '';
        if (!teams.length) {
            els.teamList.innerHTML = '<div class="empty-state">No teams yet. Create one on the left.</div>';
            return;
        }
        teams.forEach(team => {
            const item = document.createElement('div');
            item.className = 'team-item' + (team.is_builtin ? ' built-in' : '');
            const chips = team.members.map(m => `<span class="chip">${esc(m.display_name)}</span>`).join('');
            item.innerHTML = `
                <div class="meta">
                    <div class="name">${esc(team.name)} ${team.is_builtin ? '<span class="badge">built-in</span>' : ''}</div>
                    ${team.description ? `<div style="font-size:.85rem;color:#666;margin-top:4px;">${esc(team.description)}</div>` : ''}
                    <div class="chips">${chips}</div>
                    <div style="font-size:.75rem;color:#888;margin-top:6px;">Coordinator: ${esc(team.coordinator_name)} · ${team.batch ? 'Batched' : 'Sequential'}</div>
                </div>
                <div class="actions">
                    <button class="action-btn" title="Run deliberation" data-run="${team.id}"><i class="fas fa-play"></i></button>
                    ${!team.is_builtin ? `
                        <button class="action-btn" title="Edit" data-edit="${team.id}"><i class="fas fa-pen"></i></button>
                        <button class="action-btn danger" title="Delete" data-delete="${team.id}"><i class="fas fa-trash"></i></button>
                    ` : ''}
                </div>
            `;
            item.querySelector('[data-run]').addEventListener('click', () => startRun(team));
            const editBtn = item.querySelector('[data-edit]');
            if (editBtn) editBtn.addEventListener('click', () => loadTeamIntoEditor(team));
            const delBtn = item.querySelector('[data-delete]');
            if (delBtn) delBtn.addEventListener('click', () => deleteTeam(team.id, team.name));
            els.teamList.appendChild(item);
        });
    }

    // --- Editor ---
    function resetEditor() {
        editingTeamId = null;
        els.editorTitle.textContent = 'Create Team';
        els.name.value = '';
        els.description.value = '';
        els.batch.value = '1';
        selectedMembers.clear();
        renderCharacters();
        updateCoordinatorOptions();
        els.coordinator.value = 'coordinator';
        els.saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Team';
        els.cancelBtn.style.display = 'none';
    }

    function loadTeamIntoEditor(team) {
        editingTeamId = team.id;
        els.editorTitle.textContent = 'Edit Team';
        els.name.value = team.name;
        els.description.value = team.description || '';
        els.batch.value = team.batch ? '1' : '0';
        selectedMembers = new Set(team.member_ids || []);
        renderCharacters();
        updateCoordinatorOptions();
        if (team.coordinator_id) els.coordinator.value = team.coordinator_id;
        els.saveBtn.innerHTML = '<i class="fas fa-save"></i> Update Team';
        els.cancelBtn.style.display = 'inline-flex';
        document.getElementById('editor-card').scrollIntoView({ behavior: 'smooth' });
    }

    async function saveTeam() {
        const name = els.name.value.trim();
        if (!name) { showToast('Team name is required.', 'error'); return; }
        if (name.length > 80) { showToast('Team name must be 80 characters or fewer.', 'error'); return; }
        const description = els.description.value.trim();
        if (description.length > 500) { showToast('Description must be 500 characters or fewer.', 'error'); return; }
        if (selectedMembers.size < 2) { showToast('Pick at least 2 members.', 'error'); return; }

        const payload = {
            name: name,
            description: description,
            member_ids: Array.from(selectedMembers),
            coordinator_id: els.coordinator.value,
            batch: els.batch.value === '1',
        };

        els.saveBtn.disabled = true;
        try {
            if (editingTeamId) {
                const res = await api(`/api/teams/${editingTeamId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload),
                });
                if (!res || !res.success) throw new Error(res.error || 'Update failed');
                showToast('Team updated.', 'success');
            } else {
                const res = await api('/api/teams', {
                    method: 'POST',
                    body: JSON.stringify(payload),
                });
                if (!res || !res.success) throw new Error(res.error || 'Create failed');
                showToast('Team created.', 'success');
            }
            resetEditor();
            await loadData();
        } catch (err) {
            showToast(err.message, 'error');
        } finally {
            els.saveBtn.disabled = false;
        }
    }

    async function deleteTeam(id, name) {
        if (!confirm(`Delete team "${name}"?`)) return;
        try {
            const res = await api(`/api/teams/${id}`, { method: 'DELETE' });
            if (!res || !res.success) throw new Error(res.error || 'Delete failed');
            showToast('Team deleted.', 'success');
            if (editingTeamId === id) resetEditor();
            if (els.runCard.dataset.teamId === id) hideRunCard();
            await loadData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // --- Run deliberation ---
    let currentRunTeamId = null;

    function startRun(team) {
        currentRunTeamId = team.id;
        els.runCard.style.display = 'block';
        els.runCard.dataset.teamId = team.id;
        els.runTeamName.textContent = team.name;
        els.deliberateMessage.value = '';
        renderHistory();
        els.runCard.scrollIntoView({ behavior: 'smooth' });
        els.deliberateMessage.focus();
    }

    function hideRunCard() {
        currentRunTeamId = null;
        els.runCard.style.display = 'none';
    }

    async function runDeliberation() {
        const message = els.deliberateMessage.value.trim();
        if (!message) { showToast('Enter a message first.', 'error'); return; }
        if (!currentRunTeamId) return;

        // Optimistically add the user question to the history so the UI feels responsive.
        appendExchange({ question: message, response: null, meta: null, contributions: null, timestamp: Date.now() });
        els.deliberateMessage.value = '';

        els.runBtn.disabled = true;
        els.runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Thinking…';
        try {
            const res = await api(`/api/teams/${currentRunTeamId}/deliberate`, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    reveal_attribution: els.revealAttr.checked,
                }),
            });
            if (!res) return;
            if (!res.success) {
                markLastExchangeAsFailed(res.reason || 'Deliberation failed.');
                showToast(res.reason || 'Deliberation failed.', 'error');
                return;
            }
            updateLastExchange({
                response: res.response || 'No response returned.',
                meta: res,
                contributions: res.contributions || [],
                attribution_revealed: !!res.attribution_revealed,
            });
        } catch (err) {
            markLastExchangeAsFailed(err.message);
            showToast(err.message, 'error');
        } finally {
            els.runBtn.disabled = false;
            els.runBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Ask Team';
        }
    }

    function historyForCurrentTeam() {
        return conversationHistory[currentRunTeamId] || [];
    }

    function appendExchange(exchange) {
        if (!currentRunTeamId) return;
        if (!conversationHistory[currentRunTeamId]) {
            conversationHistory[currentRunTeamId] = [];
        }
        conversationHistory[currentRunTeamId].push(exchange);
        renderHistory();
    }

    function updateLastExchange(update) {
        if (!currentRunTeamId) return;
        const hist = conversationHistory[currentRunTeamId];
        if (!hist || !hist.length) return;
        Object.assign(hist[hist.length - 1], update);
        renderHistory();
    }

    function markLastExchangeAsFailed(reason) {
        updateLastExchange({ response: '', error: reason || 'Failed' });
    }

    function clearHistory() {
        if (!currentRunTeamId) return;
        delete conversationHistory[currentRunTeamId];
        renderHistory();
    }

    function renderHistory() {
        const hist = historyForCurrentTeam();
        els.clearHistoryBtn.style.display = hist.length ? 'inline-flex' : 'none';
        els.history.innerHTML = '';
        if (!hist.length) {
            els.history.innerHTML = '<div class="history-empty">Ask the team a question to start the conversation.</div>';
            return;
        }
        hist.forEach((ex, idx) => {
            // User question
            const userBubble = document.createElement('div');
            userBubble.className = 'message-bubble user';
            userBubble.textContent = ex.question;
            els.history.appendChild(userBubble);

            // Assistant response (or loading/error state)
            const assistantBubble = document.createElement('div');
            assistantBubble.className = 'message-bubble assistant';
            if (ex.error) {
                assistantBubble.innerHTML = `<div style="color:var(--danger)"><i class="fas fa-exclamation-circle"></i> ${esc(ex.error)}</div>`;
            } else if (ex.response === null) {
                assistantBubble.innerHTML = '<div><i class="fas fa-spinner fa-spin"></i> Thinking…</div>';
            } else {
                assistantBubble.innerHTML = renderAssistantContent(ex);
            }
            els.history.appendChild(assistantBubble);
        });
        els.history.scrollTop = els.history.scrollHeight;
    }

    function renderAssistantContent(ex) {
        const data = ex.meta || {};
        let html = `<div class="response-text">${esc(ex.response)}</div>`;
        html += `
            <div class="response-meta">
                <span><i class="fas fa-eye-slash"></i> Blind synthesis: ${data.blind ? 'yes' : 'no'}</span>
                <span><i class="fas fa-users"></i> Members: ${(data.participating_agents || []).join(', ')}</span>
                <span><i class="fas fa-bolt"></i> Gather: ${data.gather_mode || '—'}</span>
                ${data.ai_calls ? `<span><i class="fas fa-phone"></i> AI calls: ${data.ai_calls}</span>` : ''}
            </div>
        `;
        const contribs = ex.contributions || [];
        if (ex.attribution_revealed && contribs.length) {
            html += '<div class="contributions">';
            html += '<h3 style="font-size:1rem;margin:0 0 10px;">Member takes</h3>';
            contribs.forEach(c => {
                html += `
                    <div class="contribution">
                        <div class="author">${esc(c.display_name || c.agent_id || 'Member')}</div>
                        <div>${esc(c.content || '')}</div>
                    </div>
                `;
            });
            html += '</div>';
        }
        return html;
    }

    // --- Utilities ---
    function esc(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // --- Events ---
    els.saveBtn.addEventListener('click', saveTeam);
    els.cancelBtn.addEventListener('click', resetEditor);
    els.runBtn.addEventListener('click', runDeliberation);
    els.clearHistoryBtn.addEventListener('click', clearHistory);
    els.deliberateMessage.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runDeliberation(); }
    });

    loadData();
})();
