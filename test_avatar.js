global.window = global;
global.clearInterval = clearInterval;
global.setInterval = setInterval;
global.setTimeout = setTimeout;
global.clearTimeout = clearTimeout;

require('./static/avatar_engine.js');

const eng = global.AvatarEngine;
let pass = 0, fail = 0;

function check(label, got, expected) {
    if (got === expected) { console.log('  ✓', label, '->', got); pass++; }
    else { console.log('  ✗', label, '-> got:', got, 'expected:', expected); fail++; }
}

console.log('\n=== AvatarEngine unit tests ===\n');

// buildPanelHTML structure
const html = eng.buildPanelHTML('test-panel');
check('buildPanelHTML has avatar-panel',     html.includes('class="avatar-panel"'), true);
check('buildPanelHTML has avatar-svg-wrap',  html.includes('avatar-svg-wrap'), true);
check('buildPanelHTML has avatar-bubble',    html.includes('avatar-bubble'), true);
check('buildPanelHTML has expr-btn',         html.includes('expr-btn'), true);
check('buildPanelHTML has avatar-name',      html.includes('avatar-name'), true);

// CHARACTER_MAP
check('stoic_philosopher -> man_ancient',    eng.CHARACTER_MAP['stoic_philosopher'], 'man_ancient');
check('psychologist -> woman',               eng.CHARACTER_MAP['psychologist'], 'woman');
check('scientist -> woman',                  eng.CHARACTER_MAP['scientist'], 'woman');
check('super_motivational_coach -> man',     eng.CHARACTER_MAP['super_motivational_coach'], 'man');
check('life_coach -> woman',                 eng.CHARACTER_MAP['life_coach'], 'woman');
check('coordinator -> girl',                 eng.CHARACTER_MAP['coordinator'], 'girl');

// PALETTES
const types = Object.keys(eng.PALETTES);
check('all 5 palette types defined',         types.length, 5);
check('girl palette has skin',               !!eng.PALETTES.girl.skin, true);
check('man_ancient has grey hair',           !!eng.PALETTES.man_ancient.hair, true);

// detectExpression
check('detect happy (amazing)',              eng.detectExpression('That is amazing, well done!'), 'happy');
check('detect sad (lonely)',                 eng.detectExpression('I feel sad and lonely today'), 'sad');
check('detect surprised (wow)',              eng.detectExpression('Wow that is really incredible!'), 'surprised');
check('detect encouraging (you can)',        eng.detectExpression('You can do this, believe in yourself!'), 'encouraging');
check('detect thinking (hmm)',               eng.detectExpression('Hmm let me think about that carefully'), 'thinking');
check('detect neutral (weather)',            eng.detectExpression('What is 2 plus 2?'), 'neutral');
check('detect neutral (null)',               eng.detectExpression(null), 'neutral');
check('detect neutral (empty)',              eng.detectExpression(''), 'neutral');

console.log(`\n=== Results: ${pass} passed, ${fail} failed ===\n`);
process.exit(fail > 0 ? 1 : 0);
