/**
 * Shared Emergency Card renderer (PWA modal + home-screen Emergency icon).
 *
 * Reads the copy cached on this phone (drHealth.emergencyCard.v1). That cache
 * is written by the main Dr. Health app after login; this module never talks
 * to the network, so the home-screen icon still works without a password.
 *
 * Deliberately avoids optional chaining (?.) so it parses on older Android
 * WebView / Chrome builds.
 */
(function (root) {
    'use strict';

    const KEY = 'drHealth.emergencyCard.v1';

    function esc(s) {
        return (s == null ? '' : String(s))
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function telHref(n) {
        const d = String(n || '').replace(/[^\d+]/g, '');
        return d ? 'tel:' + d : '';
    }

    function listOf(x) {
        return Array.isArray(x) ? x : (x ? [x] : []);
    }

    function medLabel(m) {
        if (!m) return '';
        if (typeof m === 'string') return m;
        return m.label || [m.name, m.dose || m.dosage, m.frequency].filter(Boolean).join(' ');
    }

    function load() {
        try { return JSON.parse(localStorage.getItem(KEY) || 'null'); }
        catch (e) { return null; }
    }

    function hasData(card) {
        const v = card || {};
        return !!(v.name || v.date_of_birth || v.age || v.blood || v.weight ||
            v.gender || v.language || v.advance_care || v.anaphylaxis || v.pregnancy ||
            listOf(v.conditions).length || listOf(v.medications).length ||
            listOf(v.allergies).length || listOf(v.implants).length ||
            listOf(v.anticoagulants).length ||
            v.history || v.doctors || v.gp_name || v.gp_phone ||
            v.ec_name || v.ec_phone);
    }

    function section(title, text, extraClass) {
        if (!text) return '';
        const cls = extraClass ? 'emergency-section ' + extraClass : 'emergency-section';
        return '<div class="' + cls + '"><h3>' + esc(title) + '</h3><p>' +
            esc(String(text)).replace(/\n/g, '<br>') + '</p></div>';
    }

    function list(title, items) {
        items = listOf(items).filter(Boolean);
        if (!items.length) return '';
        return '<div class="emergency-section"><h3>' + esc(title) + '</h3><ul>' +
            items.map(function (i) { return '<li>' + esc(i) + '</li>'; }).join('') +
            '</ul></div>';
    }

    function medList(items) {
        items = listOf(items).filter(Boolean);
        let block = '<div class="emergency-section"><h3>Current medications</h3>';
        if (!items.length) {
            return block + '<p class="emergency-empty">None recorded. Add them under Health \u2192 Medications.</p></div>';
        }
        block += '<ul class="emergency-meds">';
        for (let i = 0; i < items.length; i++) {
            const m = items[i];
            if (typeof m === 'string') {
                block += '<li><span class="emergency-med-name">' + esc(m) + '</span></li>';
                continue;
            }
            const name = m.name || m.label || '';
            const dose = m.dose || m.dosage || '';
            const freq = m.frequency || '';
            block += '<li><span class="emergency-med-name">' + esc(name) + '</span>';
            block += '<span class="emergency-med-meta">';
            block += '<span><em>Dose</em> ' + esc(dose || '\u2014') + '</span>';
            block += '<span><em>Frequency</em> ' + esc(freq || '\u2014') + '</span>';
            block += '</span></li>';
        }
        return block + '</ul></div>';
    }

    function phoneBlock(title, name, rel, phone) {
        if (!name && !phone) return '';
        const href = telHref(phone);
        let block = '<div class="emergency-section"><h3>' + esc(title) + '</h3>';
        if (name) block += '<p class="big">' + esc(name) + '</p>';
        if (rel) block += '<p>' + esc(rel) + '</p>';
        if (phone && href) {
            block += '<p><a class="big" href="' + esc(href) + '">' + esc(phone) + '</a></p>';
        } else if (phone) {
            block += '<p class="big">' + esc(phone) + '</p>';
        }
        return block + '</div>';
    }

    function html(card, opts) {
        const o = opts || {};
        const v = card || {};
        let out = '';
        if (o.sourceNote === false) {
            /* caller supplies its own */
        } else {
            out += '<div class="emergency-source-note">This card is assembled from <strong>Personal Details</strong>, <strong>Medications</strong> and <strong>Conditions</strong>. Open those pages to add or update it. A copy stays on this phone for use without internet.</div>';
        }
        if (o.leadHtml) out += o.leadHtml;
        if (!hasData(v)) {
            out += '<div class="emergency-section"><p>' +
                (o.emptyText || 'Nothing on the card yet. Add identity and alerts in Personal Details, medicines in Medications, and diagnoses in Conditions.') +
                '</p></div>';
            return out;
        }
        out += section('Name', v.name);
        const identity = [
            v.date_of_birth ? ('DOB ' + v.date_of_birth) : '',
            v.age ? (v.age + ' yrs') : '',
            v.gender || '',
            v.weight ? ('Weight ' + v.weight) : '',
            v.height ? ('Height ' + v.height) : '',
            v.blood ? ('Blood ' + v.blood) : ''
        ].filter(Boolean).join(' \u00b7 ');
        out += section('Identity', identity);
        out += section('Advance care / not for CPR', v.advance_care, 'emergency-alert');
        out += list('Allergies', v.allergies);
        out += section('Anaphylaxis / adrenaline pen', v.anaphylaxis, v.anaphylaxis ? 'emergency-alert' : '');
        out += list('Blood thinners / antiplatelets', v.anticoagulants);
        out += medList(v.medications);
        out += list('Medical conditions', v.conditions);
        out += list('Implants and devices', v.implants);
        out += section('Pregnancy', v.pregnancy);
        out += section('Language / communication', v.language);
        out += phoneBlock('Usual GP', v.gp_name, '', v.gp_phone);
        out += phoneBlock('Emergency contact', v.ec_name, v.ec_rel, v.ec_phone);
        out += section('Other doctors', v.doctors);
        out += section('Other medical history', v.history);
        out += section('Suburb / area', v.location);
        return out;
    }

    function render(el, card, opts) {
        if (!el) return;
        el.innerHTML = html(card, opts);
    }

    root.EmergencyCard = {
        KEY: KEY,
        load: load,
        hasData: hasData,
        medLabel: medLabel,
        esc: esc,
        telHref: telHref,
        html: html,
        render: render
    };
}(typeof window !== 'undefined' ? window : this));
