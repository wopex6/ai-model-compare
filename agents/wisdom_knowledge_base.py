"""
Wisdom Knowledge Base
=====================
A structured corpus of human wisdom drawn from:
- Eastern & Western history (patterns that repeat across civilisations)
- Philosophy (Stoics, Confucians, Buddhists, Existentialists, Pragmatists, etc.)
- Psychology (Freud, Jung, Maslow, CBT, Positive Psychology, Attachment Theory, etc.)
- Sociology (Durkheim, Weber, Bourdieu, social capital, group dynamics)
- Economics (behavioural economics, Kahneman, Thaler, incentive theory)

Design principles:
1. Each lesson is a STRUCTURED object — not just a quote.
2. Conflicting interpretations are stored explicitly.
3. The agent picks between interpretations based on user evidence.
4. Lessons map to HUMAN MISTAKE PATTERNS — the recurring errors across history.
5. The corpus is queryable by domain, mistake_type, and culture.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set


# ─────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────

@dataclass
class Interpretation:
    """One school of thought's reading of a lesson — may conflict with others."""
    school: str            # e.g. 'Stoic', 'Buddhist', 'Freudian', 'Behaviourist'
    culture: str           # 'Eastern', 'Western', 'Universal'
    stance: str            # One sentence: what this school says about the pattern
    advice: str            # Concrete advice derived from this stance
    evidence: str          # Historical or research evidence backing this
    conditions: str        # When this interpretation applies best


@dataclass
class WisdomLesson:
    """
    A structured lesson from human history/philosophy/science.
    Represents a PATTERN OF HUMAN BEHAVIOUR with multiple interpretations.
    """
    id: str                          # Unique key, e.g. 'avoidance_of_discomfort'
    title: str                       # Human-readable title
    mistake_type: str                # Category: see MISTAKE_TYPES below
    domains: List[str]               # Where this appears: health, relationships, career, etc.
    universal_pattern: str           # The core human pattern in plain language
    historical_examples: List[str]   # Real historical instances (East + West)
    interpretations: List[Interpretation]  # Competing schools of thought
    resolution_hint: str             # How the agent should pick between interpretations
    keywords: List[str]              # For matching against user data
    urgency_when_detected: str       # 'high', 'medium', 'low'


# ─────────────────────────────────────────────────────
# Dynamic registries — derived from lesson data, never hardcoded
# ─────────────────────────────────────────────────────

def get_all_mistake_types() -> List[str]:
    """All mistake types present in the loaded corpus — discovered, not declared."""
    return sorted({l.mistake_type for l in WISDOM_LESSONS})


def get_all_domains() -> List[str]:
    """All life domains covered across all lessons."""
    return sorted({d for l in WISDOM_LESSONS for d in l.domains})


def get_all_schools() -> List[str]:
    """All schools of thought present across all interpretations."""
    return sorted({i.school for l in WISDOM_LESSONS for i in l.interpretations})


def get_all_cultures() -> List[str]:
    """All cultures represented across all interpretations."""
    return sorted({i.culture for l in WISDOM_LESSONS for i in l.interpretations})


def get_schools_by_culture(culture: str) -> List[str]:
    """Schools belonging to a given culture (Eastern / Western / Universal)."""
    return sorted({
        i.school
        for l in WISDOM_LESSONS
        for i in l.interpretations
        if i.culture == culture
    })


def get_next_school(current_school: str, tried_schools: List[str] = None) -> str:
    """
    Given a school that was rejected, return the next best school to try.
    Derived entirely from the knowledge base — no hardcoded rotation.

    Strategy:
    1. Prefer schools from the same lesson that haven't been tried yet.
    2. Then prefer schools from lessons sharing the same mistake_type.
    3. Then fall back to any untried school in the full corpus.
    4. If all have been tried, return the one with the lowest usage
       (i.e., restart from least-used).
    """
    tried = set(tried_schools or [])
    tried.add(current_school)

    # Find all lessons that contain the current school
    source_lessons = [
        l for l in WISDOM_LESSONS
        if any(i.school == current_school for i in l.interpretations)
    ]

    # 1. Other schools in the same lessons, not yet tried (deduplicated, order-preserved)
    same_lesson_schools = list(dict.fromkeys(
        i.school
        for l in source_lessons
        for i in l.interpretations
        if i.school not in tried
    ))
    if same_lesson_schools:
        return same_lesson_schools[0]

    # 2. Schools from same mistake_type lessons, not tried (deduplicated, order-preserved)
    same_type_types = {l.mistake_type for l in source_lessons}
    type_schools = list(dict.fromkeys(
        i.school
        for l in WISDOM_LESSONS
        if l.mistake_type in same_type_types
        for i in l.interpretations
        if i.school not in tried
    ))
    if type_schools:
        return type_schools[0]

    # 3. Any untried school in the entire corpus
    all_schools = get_all_schools()
    untried = [s for s in all_schools if s not in tried]
    if untried:
        return untried[0]

    # 4. All tried — restart from least-used school, preferring those in the same
    # mistake_type domain first before falling back to the full corpus.
    usage: Dict[str, int] = {s: 0 for s in all_schools}
    for l in WISDOM_LESSONS:
        for i in l.interpretations:
            usage[i.school] += 1
    # Prefer schools from same mistake_type lessons (domain-relevant restart)
    domain_schools = list(dict.fromkeys(
        i.school
        for l in WISDOM_LESSONS
        if l.mistake_type in same_type_types
        for i in l.interpretations
    ))
    if domain_schools:
        return min(domain_schools, key=lambda s: usage.get(s, 0))
    return min(all_schools, key=lambda s: usage.get(s, 0))


# ─────────────────────────────────────────────────────
# The Knowledge Base
# ─────────────────────────────────────────────────────

WISDOM_LESSONS: List[WisdomLesson] = [

    WisdomLesson(
        id='avoidance_of_discomfort',
        title='Avoiding Discomfort Grows the Problem',
        mistake_type='avoidance',
        domains=['health', 'relationships', 'career', 'mental_health'],
        universal_pattern=(
            'Humans consistently delay confronting uncomfortable truths — illness symptoms, '
            'relationship conflicts, financial problems — hoping they resolve on their own. '
            'Across all recorded history, this pattern accelerates the original problem.'
        ),
        historical_examples=[
            'Roman senators who refused to acknowledge the empire\'s fiscal decline until '
            'it was irreversible (Western, ~3rd century AD) — applies to anyone avoiding '
            'financial or organisational warning signs',
            'Ming Dynasty officials who suppressed reports of peasant revolts, leading to '
            'the dynasty\'s collapse (Eastern, 17th century) — applies to leaders or '
            'professionals who avoid difficult team or organisational feedback',
            'Neville Chamberlain\'s appeasement policy — avoiding confrontation made Hitler '
            'more emboldened, not less (Western, 1938) — applies to relationship or '
            'workplace conflicts where silence allows harm to compound',
            'Emperor Commodus (Rome, ~180 AD): surrounded himself with flatterers, executed '
            'those who raised concerns — empire\'s governance collapsed within his reign. '
            'Applies to anyone who avoids honest feedback from doctors, family, or colleagues',
            'King George III of England refused to acknowledge early symptoms of mental illness '
            'for years; court physicians were discouraged from honest assessment — his '
            'incapacity prolonged the American Revolution and the Regency Crisis '
            '(Western, 1780s) — applies to health avoidance, especially in high-functioning people',
            'Individuals in the Framingham Heart Study who avoided early cardiac symptoms '
            'had 3x worse outcomes than those who sought early intervention — applies directly '
            'to any user delaying a health check, test, or medical appointment',
        ],
        interpretations=[
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='Avoidance is a failure of virtue — courage (andreia) requires facing '
                       'what is unpleasant. The Stoics held that discomfort confronted is '
                       'discomfort diminished.',
                advice='Name the thing you are avoiding. Write it down. Schedule one concrete '
                       'action toward it within 48 hours.',
                evidence='Marcus Aurelius: "You have power over your mind, not outside events. '
                         'Realise this, and you will find strength." (Meditations, ~170 AD)',
                conditions='Best when the person has intellectual self-awareness but emotional avoidance'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Avoidance arises from attachment to comfort (upadana). The Second Noble '
                       'Truth holds that suffering is caused by clinging — including clinging to '
                       'ease. Impermanence means the problem will change whether you face it or not.',
                advice='Sit with the discomfort without acting on it for 10 minutes daily '
                       '(mindfulness). Then act from a place of calm, not fear.',
                evidence='The Buddha left his palace to face suffering directly — his enlightenment '
                         'required confronting, not avoiding, dukkha.',
                conditions='Best when the person is emotionally reactive and needs to calm before acting'
            ),
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='Avoidance is a cognitive behaviour that provides short-term relief but '
                       'reinforces the anxiety response long-term (negative reinforcement loop). '
                       'Exposure therapy is the most evidence-backed intervention.',
                advice='Use graded exposure: list feared situations from least to most threatening, '
                       'then address the smallest one first. Each success reduces anxiety.',
                evidence='Meta-analysis of 72 RCTs shows exposure-based CBT is 60-80% effective '
                         'for anxiety and avoidance disorders (Hofmann et al., 2012)',
                conditions='Best when avoidance is linked to specific anxiety or phobia patterns'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Avoidance violates ren (benevolence) toward oneself. A junzi (superior '
                       'person) practises self-cultivation through honest self-examination (zixing). '
                       'Confucius: "When you know a thing, hold that you know it; when you do not '
                       'know a thing, allow that you do not know it."',
                advice='Daily self-examination (daily checkin practice). Ask: what did I avoid '
                       'today and why? Write one honest sentence about it.',
                evidence='The Analects, 1:4 — Zengzi examined himself daily on three points.',
                conditions='Best when person has strong social or filial values'
            ),
        ],
        resolution_hint=(
            'If the user shows emotional reactivity → prefer Buddhist/CBT. '
            'If they are analytical and self-aware → prefer Stoic/Confucian. '
            'If they mention specific fears → CBT graded exposure is most evidenced.'
        ),
        keywords=['avoid', 'delay', 'put off', 'not ready', 'later', 'ignore', 'suppress',
                  'pretend', 'hoping it goes away', 'not thinking about it'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='repeating_same_mistake',
        title='The Cycle of Repeated Error',
        mistake_type='repetition',
        domains=['relationships', 'career', 'health', 'finance'],
        universal_pattern=(
            'Humans repeat the same patterns of error across their lifespan and across '
            'civilisations — not from stupidity but because the root cause (belief, trauma, '
            'habit, incentive) was never addressed, only the surface symptom.'
        ),
        historical_examples=[
            'Athens lost three major wars (Peloponnesian, Lamian, Chremonidean) by '
            'overextending alliances — the same strategic mistake each time (Western, ~5th-3rd BC). '
            'Applies to anyone who repeatedly overcommits resources, energy, or trust',
            'Japan modernised rapidly under Meiji but repeated imperial overextension '
            'leading to WWII — same pattern as Edo shogunate isolation failures (Eastern). '
            'Applies to organisations and individuals who modernise the surface but '
            'not the underlying decision-making pattern',
            'Napoleon Bonaparte: brilliant military innovator who repeated the fatal error '
            'of fighting on two fronts simultaneously — Spain (1808) and Russia (1812) — '
            'despite having seen the same pattern destroy previous European powers. '
            'Applies to high-achievers who repeat ambitious overextension despite prior warning signs',
            'Henry VIII of England: repeated the pattern of discarding advisors who '
            'told him truths he disliked — Wolsey, More, Cromwell each executed or '
            'destroyed for honest counsel. Applies to leaders, managers, or family heads '
            'who cycle through relationships when people stop agreeing with them',
            'The Meiji samurai who repeatedly staged uprisings (culminating in the '
            'Satsuma Rebellion, 1877) despite each being crushed — unable to update '
            'their strategy despite repeated failure. Applies to career transitions where '
            'the same approach to job-seeking or advancement keeps failing',
            'Studies show 67% of second marriages fail for the same reasons as first '
            'marriages when no self-work is done between (Gottman Institute research). '
            'Applies directly to any user describing repeating relationship difficulties',
        ],
        interpretations=[
            Interpretation(
                school='Psychoanalytic',
                culture='Western',
                stance='Repetition is driven by the unconscious seeking to master an '
                       'unresolved past trauma. The pattern won\'t break until the original '
                       'wound is brought to consciousness.',
                advice='Look for the earliest memory of this feeling/situation. Journal: '
                       '"When did I first feel this way?" The pattern likely has childhood roots.',
                evidence='Freud, Beyond the Pleasure Principle (1920). Supported by '
                         'attachment theory research (Bowlby, Ainsworth, 1969-1978)',
                conditions='Best when person shows relationship patterns with emotional intensity'
            ),
            Interpretation(
                school='Behaviourist',
                culture='Western',
                stance='Repetition is reinforced behaviour. The mistake provides some reward '
                       '(comfort, familiarity, identity confirmation) that outweighs the cost. '
                       'Change requires identifying and removing that reward.',
                advice='Map the habit loop: Trigger → Behaviour → Reward. What reward does '
                       'the mistake actually give you? Design a substitute that gives the same '
                       'reward without the cost.',
                evidence='Skinner\'s operant conditioning; Duhigg\'s The Power of Habit (2012) '
                         'based on MIT basal ganglia research',
                conditions='Best when pattern is clearly habitual and reward-driven'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Repeated error signals a failure of self-cultivation (xiushen). '
                       'The junzi learns from mistakes immediately. Repetition means the '
                       'lesson has not been truly internalised, only intellectually acknowledged.',
                advice='For each mistake, write the lesson in your own words AND describe '
                       'one structural change to your environment or routine that makes '
                       'repetition harder.',
                evidence='Analects 1:8 — "When you make a mistake, do not be afraid to correct it."',
                conditions='Best when person is highly intellectual but low on follow-through'
            ),
            Interpretation(
                school='Positive Psychology',
                culture='Western',
                stance='Repetition often persists because the person focuses on what went '
                       'wrong rather than building the strength that makes the mistake '
                       'unnecessary. Character strengths (VIA) can replace the gap the '
                       'mistake fills.',
                advice='Identify which VIA character strength is weakest in the area where '
                       'you repeat mistakes. Build that strength through deliberate practice.',
                evidence='Seligman, Authentic Happiness (2002); VIA Institute meta-studies '
                         'showing strength-building reduces recidivism of negative patterns',
                conditions='Best when person is growth-oriented and not in acute crisis'
            ),
        ],
        resolution_hint=(
            'If the pattern is in relationships → psychoanalytic first, then CBT. '
            'If it is habit/routine based → behaviourist. '
            'If person is growth-oriented → Positive Psychology. '
            'If person is highly disciplined but lacks follow-through → Confucian.'
        ),
        keywords=['again', 'same mistake', 'keep doing', 'always end up', 'why do I',
                  'pattern', 'cycle', 'history repeating', 'not again'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='short_termism',
        title='Sacrificing the Future for Present Comfort',
        mistake_type='short_termism',
        domains=['health', 'finance', 'career', 'relationships'],
        universal_pattern=(
            'Across cultures and epochs, individuals and societies consistently undervalue '
            'future consequences relative to immediate gratification. This is not a moral '
            'failing — it is a cognitive architecture issue (hyperbolic discounting) that '
            'has destroyed empires, health, and wealth.'
        ),
        historical_examples=[
            'The Roman grain dole (annona) — short-term social stability at the cost of '
            'agricultural collapse and long-term dependency (Western, 1st century BC onward). '
            'Applies to anyone using short-term relief (spending, avoidance, comfort eating) '
            'that compounds a long-term problem',
            'Deforestation of Easter Island — islanders consumed present resources until '
            'civilisational collapse; no faction held long-term view (Pacific, ~1400-1600 AD). '
            'Applies to health and financial decisions where present enjoyment depletes '
            'future capacity',
            'Emperor Nero\'s economic policies (Rome, 54–68 AD): debased the currency '
            '(reduced silver content) repeatedly to fund immediate spectacles and military '
            'pay — each debasement provided short-term relief and long-term inflation. '
            'Applies to financial short-termism: borrowing, spending, or avoiding savings',
            'The British East India Company\'s exploitation of Bengal (1757–1770): '
            'extracted maximum short-term revenue, destroying the agricultural base — '
            'the Bengal Famine of 1770 killed 10 million. Applies to organisations and '
            'individuals who extract from a resource (body, relationship, finances) '
            'without reinvestment until it collapses',
            'Tokugawa Japan\'s sakoku policy (1603–1868): closed borders to protect '
            'short-term stability, creating 250 years of technological stagnation that '
            'left Japan defenceless against Western military power (Eastern). Applies to '
            'career and health decisions where short-term comfort blocks necessary change',
            'The 2008 financial crisis — short-term banking incentives overrode long-term '
            'systemic risk awareness. Applies directly to personal financial decisions '
            'and anyone deferring health, financial, or relationship maintenance',
        ],
        interpretations=[
            Interpretation(
                school='Behavioural Economics',
                culture='Western',
                stance='Hyperbolic discounting is a cognitive bias, not a character flaw. '
                       'The solution is to design the environment so that the long-term '
                       'choice is the path of least resistance (choice architecture).',
                advice='Remove friction from long-term choices and add friction to short-term '
                       'ones. Auto-schedule health check-ups. Set up automatic savings. '
                       'Pre-commit to future actions when you are calm.',
                evidence='Thaler & Sunstein, Nudge (2008). Pre-commitment devices shown to '
                         'increase savings rates by 40% (Thaler & Benartzi, 2004)',
                conditions='Best for practical, systems-oriented people'
            ),
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='Short-termism is a failure of reason over passion (logos over pathos). '
                       'The Stoics trained themselves to visualise long-term consequences '
                       '(negative visualisation, memento mori) to restore proportionate judgment.',
                advice='Practise negative visualisation: vividly imagine where this path leads '
                       'in 5 years. Write it in detail. Then compare to your preferred future.',
                evidence='Seneca: "Omnia aliena sunt, tempus tantum nostrum est." '
                         '(All things are external; time alone is ours.) Letters to Lucilius.',
                conditions='Best for intellectually reflective people who respond to reasoning'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The junzi takes a long view — Confucius planned in decades, not days. '
                       'Short-termism violates zhengming (rectification of names) — calling '
                       'something good when it is merely comfortable is a moral failure.',
                advice='Write a 10-year letter to yourself. Describe the person you want to be. '
                       'Test each current decision: does it move toward or away from that person?',
                evidence='Analects 15:12 — "The man who does not think far ahead will have '
                         'trouble near at hand."',
                conditions='Best when person has strong values but acts inconsistently with them'
            ),
            Interpretation(
                school='Buddhist Economics',
                culture='Eastern',
                stance='Short-termism arises from tanha (craving) — the desire for immediate '
                       'sensation. E.F. Schumacher\'s Buddhist Economics argues that right '
                       'livelihood requires satisfaction from process, not just outcome, '
                       'removing the craving for immediate reward.',
                advice='Find the intrinsic satisfaction in the long-term path itself. '
                       'If you can\'t enjoy the process, the goal will not satisfy you when reached.',
                evidence='Schumacher, Small is Beautiful (1973). Research on hedonic adaptation '
                         'shows achieved goals provide minimal lasting happiness increase.',
                conditions='Best when person achieves goals but feels empty; or when burnout is present'
            ),
        ],
        resolution_hint=(
            'Practical person → Behavioural Economics (system design). '
            'Philosophical/reflective → Stoic negative visualisation. '
            'Strong value system → Confucian long-view. '
            'Meaning/purpose issues → Buddhist Economics.'
        ),
        keywords=['just this once', 'I\'ll start tomorrow', 'later', 'treat myself',
                  'not now', 'enjoy now', 'one more', 'procrastin', 'will do it when'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='external_blame',
        title='Externalising Blame Blocks Growth',
        mistake_type='blame_externalising',
        domains=['relationships', 'career', 'mental_health', 'finance'],
        universal_pattern=(
            'The attribution of one\'s difficulties entirely to external forces — other people, '
            'fate, society, bad luck — is one of the most consistent psychological barriers to '
            'growth. It appears across every culture and era, and the research consensus is clear: '
            'it correlates strongly with learned helplessness and depression.'
        ),
        historical_examples=[
            'The decline of the Qing Dynasty was attributed by officials to Western aggression '
            'rather than internal structural failures — blocking self-reform for decades '
            '(Eastern, 19th century). Applies to anyone blaming external circumstances '
            '(employers, economy, family) for outcomes that also have internal causes',
            'Post-WWI Germany\'s "stab in the back" myth (Dolchstoßlegende) — blaming internal '
            'enemies rather than military failure created the psychological conditions for '
            'Nazism (Western, 1918–1933). Applies to situations where blame narratives '
            'are politically or emotionally useful but prevent learning and recovery',
            'Tsar Nicholas II of Russia attributed the 1905 Revolution and then the '
            '1917 Revolution to agitators and enemies of Russia — never examining his own '
            'governance failures. He was executed with his family in 1918. Applies to '
            'anyone in a leadership role (parent, manager, partner) who attributes '
            'all relational breakdown to others\' failings',
            'The Roman Emperor Julian (361–363 AD): attributed the decline of Roman '
            'traditional religion entirely to Christian subversion — not to his own '
            'failure to make paganism relevant or reform its institutions. '
            'Applies to anyone who attributes the loss of a relationship, career, or '
            'community to others without examining their own contribution',
            'Nelson Mandela\'s contrast: after 27 years in prison, he explicitly refused '
            'to blame his imprisonment for all subsequent difficulties — he identified '
            'what was in his power to change and acted on it. Applies to any user who '
            'has experienced genuine injustice but is now blocked by the blame narrative',
            'Seligman\'s learned helplessness experiments: subjects who attributed negative '
            'outcomes to external, permanent forces stopped trying even when the situation changed. '
            'Applies to health ("nothing will help"), career ("the system is rigged"), '
            'and relationships ("people never change")',
        ],
        interpretations=[
            Interpretation(
                school='Existentialist',
                culture='Western',
                stance='Sartre: "Man is condemned to be free" — radical responsibility. '
                       'We are always complicit in our situation because we choose our response. '
                       'Bad faith (mauvaise foi) is the self-deception of claiming no choice.',
                advice='For any situation you blame on others, ask: "What was my 10% role in '
                       'this?" Even finding 10% restores agency. You cannot change what you '
                       'do not own.',
                evidence='Sartre, Being and Nothingness (1943). Viktor Frankl: even in '
                         'Auschwitz, the last human freedom is choosing one\'s attitude.',
                conditions='Best for highly intelligent people capable of brutal self-honesty'
            ),
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='External attribution is a cognitive distortion (specifically, '
                       '"personalisation" in reverse — giving others all the agency). '
                       'Attribution retraining is the evidence-backed intervention.',
                advice='Use the ABC model: Activating event → Belief (why did this happen?) → '
                       'Consequence. Examine whether the B is accurate or distorted.',
                evidence='Beck, Cognitive Therapy of Depression (1979). Attribution retraining '
                         'shown to reduce depressive symptoms in 6 weeks (meta-analysis, 2008)',
                conditions='Best when person shows patterns of helplessness or repeated victimhood'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Self-cultivation (xiushen) is the foundation of all social order. '
                       'The Great Learning (Daxue) begins with the individual, not society. '
                       'One who blames others has not yet begun to cultivate themselves.',
                advice='Begin with yourself. Confucius asked not "why does the world fail me" '
                       'but "how can I become worthy?" Write one way you could have acted '
                       'differently in the situation you are blaming.',
                evidence='Daxue (Great Learning) — the eight steps begin with "investigation '
                         'of things" and "rectification of the mind," before engaging the world.',
                conditions='Best when person has strong social awareness but poor self-awareness'
            ),
            Interpretation(
                school='Sociology (Bourdieu)',
                culture='Western',
                stance='External forces are REAL — habitus (internalised social structures), '
                       'field (social context), and capital (economic/cultural/social) genuinely '
                       'constrain agency. Full internal attribution can be a tool of the powerful '
                       'to prevent legitimate critique of structural injustice.',
                advice='Distinguish: what is genuinely structural (requires collective action) '
                       'vs what is within your immediate power to change. Address both, '
                       'but change what you can immediately while advocating for the structural.',
                evidence='Bourdieu, Distinction (1984). Research on poverty traps shows '
                         'structural barriers are real and not solely attributable to individual choice.',
                conditions='Use when external factors are genuinely systemic (poverty, discrimination). '
                           'Prevents over-blaming the individual for structural problems.'
            ),
        ],
        resolution_hint=(
            'If person is stuck in victimhood with clear personal choices available → Existentialist/CBT. '
            'If person faces genuine structural barriers → Bourdieu — validate real constraints. '
            'If person is highly intellectual → Sartre radical responsibility. '
            'If person has cultural/family values → Confucian self-cultivation.'
        ),
        keywords=['their fault', 'blame', 'not fair', 'always happens to me', 'victim',
                  'nothing I can do', 'out of my control', 'they made me', 'if only they'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='sunk_cost_fallacy',
        title='Continuing Bad Paths Due to Past Investment',
        mistake_type='sunk_cost',
        domains=['career', 'relationships', 'finance', 'health'],
        universal_pattern=(
            'Humans universally persist in failing courses of action because of what has already '
            'been invested — time, money, emotion, identity. The past investment has no bearing '
            'on future outcomes, yet emotionally it dominates rational decision-making. '
            'This pattern has ended wars, relationships, companies, and lives.'
        ),
        historical_examples=[
            'The Vietnam War — US escalated for a decade partly because of what had already '
            'been spent, not because of strategic merit (Western, 1965–1975). Applies to '
            'anyone persisting in a failing career, relationship, or health behaviour '
            'because of years already invested',
            'The Concorde project — UK and France continued despite knowing it was economically '
            'unviable because of prior investment; "Concorde fallacy" is named after this. '
            'Applies to financial decisions: continuing an investment, business, or property '
            'because of what was spent, not what it is worth now',
            'Emperor Justinian I (Byzantine, 527–565 AD): spent the last 20 years of his reign '
            'attempting to reconquer the Western Roman Empire — depleting treasury, army, and '
            'political capital — because of what had already been sacrificed for early gains. '
            'Applies to any high-achiever who cannot exit a failing project due to identity investment',
            'The Japanese Imperial Army\'s campaign in China (1937–1945): continued long after '
            'strategic advisors indicated it was unwinnable, because withdrawal would have '
            'invalidated the sacrifice already made. Applies to relationships or careers '
            'where the honest answer is to leave, but the years invested make it feel impossible',
            'Qing Dynasty prolonged the imperial examination system (keju) for centuries '
            'despite its irrelevance to modern governance — cultural investment overrode '
            'strategic logic (Eastern). Applies to anyone clinging to qualifications, '
            'methods, or identities that no longer serve their situation',
            'Personal parallel: a surgeon who continues an operation that should be abandoned '
            'because "I\'ve already opened" — documented cause of preventable deaths in '
            'surgical audit literature. Applies to health decisions where past treatment '
            'investment prevents changing course',
        ],
        interpretations=[
            Interpretation(
                school='Behavioural Economics',
                culture='Western',
                stance='Sunk cost bias is a predictable cognitive error — loss aversion '
                       'makes past investment feel like a future loss if abandoned. '
                       'The rational decision ignores sunk costs entirely.',
                advice='Ask only: "Given where I am NOW, with no past investment, would I '
                       'choose this path?" If no, the sunk cost is distorting your judgment.',
                evidence='Kahneman, Thinking Fast and Slow (2011). Arkes & Blumer (1985) '
                         'original sunk cost experiments showing universal susceptibility.',
                conditions='Best for analytical people who respect evidence-based reasoning'
            ),
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='What is past is not in our control (ouk eph\' hemin). Continuing a '
                       'bad path to justify past suffering is a double error — suffering twice '
                       'for the same mistake. Amor fati: accept what is past and act wisely now.',
                advice='Distinguish: what can I control from this moment forward? The past '
                       'is fixed. Only the present decision is yours.',
                evidence='Epictetus, Enchiridion, 1: "Some things are in our control and '
                         'others not." Stoics practised daily death meditation to clarify '
                         'what truly matters.',
                conditions='Best when person has intellectual control but emotional attachment to past'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Attachment to past investment is a form of clinging (upadana) to '
                       'a self-narrative ("I have invested X, therefore I am X"). '
                       'Impermanence (anicca) means the past self who made that investment '
                       'no longer exists in the same form.',
                advice='Separate your identity from the investment. You are not your past '
                       'decisions. Practise the question: "Who am I without this investment?"',
                evidence='Pali Canon, Milindapanha — the ship of Theseus argument applied '
                         'to personal identity. Supports radical flexibility in self-concept.',
                conditions='Best when sunk cost is tied to identity ("I\'ve given 10 years to this")'
            ),
        ],
        resolution_hint=(
            'Analytical + practical → Behavioural Economics framing. '
            'Identity-based attachment → Buddhist. '
            'Philosophical about loss → Stoic amor fati.'
        ),
        keywords=['already invested', 'can\'t give up now', 'wasted', 'too much to quit',
                  'come this far', 'give up', 'walked away', 'years of', 'after all this',
                  'given', 'cannot quit', 'too far', 'put in', 'years into', 'so much time'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='meaning_vacuum',
        title='Loss of Purpose and Existential Drift',
        mistake_type='meaning_vacuum',
        domains=['mental_health', 'retirement', 'career', 'relationships'],
        universal_pattern=(
            'When humans lose a primary source of meaning — work, relationship, faith, role — '
            'they often drift into depression, addiction, or nihilism unless a new source is '
            'actively constructed. This is especially acute after retirement, bereavement, or '
            'major identity transitions. It is one of the most underdiagnosed drivers of '
            'declining health in older adults.'
        ),
        historical_examples=[
            'Roman generals returning from conquest often collapsed into dissolution — '
            'Sulla retired into debauchery, Pompey lost direction without a campaign, '
            'Antony abandoned Rome for Cleopatra\'s court — when the campaign (their '
            'meaning structure) ended, the man dissolved (Western). Directly applies '
            'to retirement, redundancy, or the end of any dominant life role',
            'Post-Meiji samurai class in Japan: stripped of their warrior role by '
            'the 1876 sword prohibition, suicide rates and social dysfunction spiked '
            'dramatically — men defined entirely by a role that society abolished (Eastern). '
            'Applies to anyone whose professional or social identity has been made obsolete',
            'Alexander the Great\'s final years (323 BC): after conquering the known world '
            'at 32, he reportedly wept "because there were no more worlds to conquer" — '
            'then descended into alcoholism and erratic behaviour. Applies to high-achievers '
            'post-peak: retirement, empty nest, or reaching a long-sought goal that does not satisfy',
            'Nelson Mandela\'s 27 years in prison: maintained purpose through studying law, '
            'teaching fellow prisoners, writing — purpose was not in the role but in the '
            'contribution. Survived psychological intact where others broke. Applies to '
            'anyone facing loss of role or freedom who needs to locate meaning within constraints',
            'Frankl\'s logotherapy developed in Auschwitz: those with a "why" to live '
            'survived conditions that killed those without one — purpose is a survival variable, '
            'not a luxury. Applies to any user expressing emptiness, especially post-retirement',
            'WHO studies on retirement: health decline correlates more strongly with '
            'loss of purpose than with physical aging in the first 5 post-retirement years. '
            'Applies directly to retired users; also to anyone who has lost a central role',
        ],
        interpretations=[
            Interpretation(
                school='Existentialist / Logotherapy',
                culture='Western',
                stance='Meaning is not found — it is created through commitment and action. '
                       'Frankl: the will to meaning (not pleasure or power) is the primary '
                       'human drive. A meaning vacuum must be actively filled, not waited out.',
                advice='List three things that gave you the strongest sense of meaning in '
                       'your life. Design a way to contribute to each of those things now, '
                       'even in a small capacity.',
                evidence='Frankl, Man\'s Search for Meaning (1946). Meta-analysis of purpose '
                         'in life studies: high purpose correlates with 23% lower mortality risk.',
                conditions='Best when person is intellectually reflective and open to self-design'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The junzi finds meaning in role and relationship — the five relationships '
                       '(wulun) provide structure. When roles disappear (retirement, empty nest), '
                       'new roles must be cultivated. Service to community (ren) fills the vacuum.',
                advice='Identify a community role you can step into — mentoring, teaching, '
                       'community service. Confucian meaning comes from being needed by others.',
                evidence='Analects 12:1 — To master oneself and return to ritual propriety '
                         'is benevolence. Japanese ikigai (reason for being) is a related construct.',
                conditions='Best when person has strong social and family values'
            ),
            Interpretation(
                school='Positive Psychology',
                culture='Western',
                stance='PERMA model (Seligman): wellbeing requires Positive emotion, '
                       'Engagement, Relationships, Meaning, and Achievement. A meaning vacuum '
                       'is usually multi-dimensional — several PERMA elements have been lost simultaneously.',
                advice='Score yourself on each PERMA element (1-10). Identify which are lowest. '
                       'Design one small action per week for each element below 5.',
                evidence='Seligman, Flourish (2011). PERMA interventions show significant '
                         'improvement in wellbeing within 6 weeks in clinical trials.',
                conditions='Best for structured, goal-oriented people who respond to frameworks'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Meaning-seeking itself can be a form of suffering (dukkha) if it '
                       'requires a particular outcome. The middle path finds meaning in '
                       'present engagement (sati), not in future arrival. Meaning is in the '
                       'doing, not the destination.',
                advice='Return to basic practice: choose one activity today that requires '
                       'full present attention. Gardening, cooking, walking. Meaning often '
                       'returns through engagement, not through searching.',
                evidence='Csikszentmihalyi\'s flow research (1990) aligns with Buddhist '
                         'present-moment engagement as a source of deep satisfaction.',
                conditions='Best when person is future-oriented and unable to enjoy the present'
            ),
        ],
        resolution_hint=(
            'Intellectually reflective → Frankl/Existentialist — self-designed meaning. '
            'Social/relational person → Confucian service/role. '
            'Structured/goal-oriented → Positive Psychology PERMA. '
            'Anxious/future-oriented → Buddhist present engagement. '
            'NOTE: Retirement + health decline together = high urgency. Address this directly.'
        ),
        keywords=['no point', 'what\'s the purpose', 'retired', 'empty', 'lost',
                  'directionless', 'nothing to look forward to', 'why bother', 'meaningless',
                  'just going through', 'hollow', 'drift'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='social_comparison_trap',
        title='Measuring Worth by Comparison to Others',
        mistake_type='comparison_trap',
        domains=['mental_health', 'career', 'finance', 'relationships'],
        universal_pattern=(
            'Social comparison is a universal human tendency (Festinger, 1954) that served '
            'evolutionary purposes but in modern information-saturated environments becomes '
            'pathological. The comparison is always asymmetric — we compare our inside to '
            'others\' outside, our worst moments to their best. '
            'This pattern has been consistent across every recorded society.'
        ),
        historical_examples=[
            'Tang Dynasty aristocrats ruined themselves financially maintaining appearances '
            'relative to peers — the "face" (mianzi) economy drove families into debt across '
            'generations (Eastern, 7th–10th century). Applies to financial decisions '
            'driven by social appearance rather than genuine need',
            'Thorstein Veblen\'s "conspicuous consumption" (1899) — the Western industrial '
            'middle class destroyed savings to match upper-class appearances. Applies to '
            'anyone spending to maintain a social image that their finances cannot support',
            'Louis XIV of France (1638–1715): required his nobles to live at Versailles '
            'in competitive display — deliberately ruining their independent wealth through '
            'comparison-driven spending, making them dependent on royal favour. Applies to '
            'workplace cultures of competitive status display',
            'The Warring States period in China: feudal lords ruined states competing in '
            'military display against neighbouring kingdoms — each escalation triggered by '
            'comparison, not strategic need (Eastern, ~475–221 BC). Applies to competitive '
            'escalation in career, finance, or relationships',
            'Julius Caesar and Pompey: their rivalry was partly fuelled by comparison — '
            'each needed to be seen as the greater man. The comparison destroyed both and '
            'ended the Republic (Western, 49–44 BC). Applies to professional or family '
            'rivalries where ego comparison overrides practical judgment',
            'Social media studies (Twenge et al., 2018): upward social comparison on platforms '
            'correlates with 66% higher depression rates. Applies directly to any user '
            'describing dissatisfaction after checking others\' achievements or lifestyles',
        ],
        interpretations=[
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='External goods (wealth, status, appearance) are "indifferents" (adiaphora) '
                       '— neither good nor bad. Only virtue is good. Comparing yourself to others '
                       'on indifferents is a category error.',
                advice='When you catch yourself comparing, ask: am I comparing something within '
                       'my control (virtue, effort, character) or outside it (wealth, appearance)? '
                       'Compete only on what is within your control.',
                evidence='Marcus Aurelius, Meditations 6:2. Epictetus: "Seek not that the things '
                         'which happen should happen as you wish."',
                conditions='Best for intellectually minded people open to philosophical reframing'
            ),
            Interpretation(
                school='Psychology (SDT)',
                culture='Western',
                stance='Self-Determination Theory (Deci & Ryan) distinguishes intrinsic from '
                       'extrinsic motivation. Social comparison feeds extrinsic motivation, '
                       'which research shows consistently reduces wellbeing and sustained performance.',
                advice='Identify your intrinsic motivators (what you\'d do with no audience, '
                       'no reward). Redirect one hour per day toward intrinsically motivated activity.',
                evidence='Deci & Ryan, 40 years of SDT research: intrinsic motivation predicts '
                         'wellbeing, persistence, and creativity. Extrinsic motivation undermines them.',
                conditions='Best when person is achievement-driven but feels empty after success'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Comparison arises from the illusion of a fixed, comparable self (anatta). '
                       'The self is a process, not a thing. There is no fixed "you" to rank. '
                       'Mudita (sympathetic joy) — finding genuine happiness in others\' success — '
                       'is the Buddhist antidote to comparison and envy.',
                advice='Practise mudita: when you notice envy or comparison, deliberately generate '
                       'one genuine positive thought about the person you\'re comparing yourself to.',
                evidence='Pali Canon, Metta Bhavana practice. Neuroimaging shows compassion '
                         'meditation reduces amygdala reactivity to social threat.',
                conditions='Best for spiritually or philosophically open individuals'
            ),
        ],
        resolution_hint=(
            'Intellectually driven → Stoic adiaphora framing. '
            'Achievement-driven but unfulfilled → SDT intrinsic motivation. '
            'Open to spiritual practice → Buddhist mudita. '
        ),
        keywords=['better than me', 'compared to', 'they have', 'why can\'t I',
                  'everyone else', 'jealous', 'envy', 'not as good as', 'behind',
                  'successful', 'what others think'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='body_neglect',
        title='Ignoring Physical Health Signals',
        mistake_type='body_neglect',
        domains=['health'],
        universal_pattern=(
            'Across cultures, humans routinely ignore, minimise, or delay responding to '
            'physical health signals — fatigue, pain, unusual symptoms — especially men, '
            'especially those with high cognitive engagement in other domains. '
            'The body is treated as a vehicle to be driven until it breaks, not a system '
            'to be maintained. This pattern has a measurable mortality cost.'
        ),
        historical_examples=[
            'Descartes\' mind-body dualism (1641) deeply embedded in Western culture the '
            'idea that the body is separate from the "real" self — a philosophical error '
            'with enormous medical consequences: Western medicine spent 300 years treating '
            'symptoms in isolation. Applies to anyone who intellectualises or ignores '
            'what their body is signalling',
            'Emperor Qin Shi Huang (China, ~246–210 BC): obsessively sought immortality '
            'through mercury-based elixirs prescribed by court physicians he refused to '
            'question — died at 49, likely of mercury poisoning. His neglect of genuine '
            'health signals while pursuing a fantasy of physical invincibility is a '
            'direct historical parallel. Applies to any user avoiding real medical care '
            'while pursuing alternative approaches, or ignoring symptoms',
            'King Charles II of England (1685): died after his physicians applied 58 '
            'different treatments in four days — the interventions, not the illness, '
            'likely killed him. But he had ignored prodromal symptoms for months. '
            'Applies to health avoidance followed by crisis-mode intervention',
            'Traditional Chinese Medicine and Ayurvedic traditions explicitly rejected '
            'mind-body separation — both treated the body as a unified system requiring '
            'maintenance before crisis, not crisis intervention alone. Applies to '
            'preventive health behaviours: sleep, movement, diet, regular checks',
            'Winston Churchill\'s health: ignored chest pain and fatigue through WWII, '
            'suffered multiple strokes and a heart attack — his physicians documented his '
            'resistance to medical advice even while running the war. Applies to '
            'high-functioning people who treat health as subordinate to duty or achievement',
            'The Framingham Heart Study (1948–present): the single strongest predictor of '
            'cardiac events is not cholesterol but failure to act on early warning signs. '
            'Applies directly to any user with outstanding medical appointments or ignored symptoms',
        ],
        interpretations=[
            Interpretation(
                school='Traditional Chinese Medicine / Eastern Holism',
                culture='Eastern',
                stance='The body is not separate from the mind or spirit. Qi (vital energy) '
                       'flows through both. Ignoring physical signals is ignoring messages '
                       'from the whole self. The body speaks what the mind suppresses.',
                advice='Treat physical symptoms as information, not inconveniences. '
                       'For each symptom you\'ve been ignoring: name it, date it, and '
                       'book one appointment or consultation this week.',
                evidence='Yellow Emperor\'s Classic of Internal Medicine (Huangdi Neijing, ~200 BC) '
                         '— preventive medicine as the highest form of medicine.',
                conditions='Best for Eastern or holistic-minded individuals'
            ),
            Interpretation(
                school='Modern Psychology / Embodied Cognition',
                culture='Western',
                stance='Somatic markers (Damasio) show that the body carries emotional '
                       'and decision-making information. Ignoring the body is ignoring '
                       'a critical data stream for living well.',
                advice='Body scan practice: 5 minutes daily, systematically noticing '
                       'physical sensations without judgment. This re-establishes the '
                       'mind-body information channel.',
                evidence='Damasio, Somatic Marker Hypothesis (1994). '
                         'Bessel van der Kolk, The Body Keeps the Score (2014).',
                conditions='Best for analytically minded individuals who intellectualise rather than feel'
            ),
        ],
        resolution_hint=(
            'Eastern or holistic → TCM/Ayurvedic framing. '
            'Western analytical → Somatic markers / embodied cognition. '
            'Health conditions already present → elevate urgency to HIGH immediately.'
        ),
        keywords=['tired', 'pain', 'ignoring', 'not been to doctor', 'feeling off',
                  'probably nothing', 'just stress', 'busy', 'no time', 'push through',
                  'medication', 'symptom', 'test result', 'diagnosis'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='identity_rigidity',
        title='Refusing to Update the Self-Concept',
        mistake_type='identity_rigidity',
        domains=['career', 'relationships', 'mental_health', 'retirement'],
        universal_pattern=(
            'When circumstances change — retirement, illness, relationship loss, cultural shift — '
            'humans often cling to an identity that no longer fits. The self-concept becomes '
            'a prison rather than a home. This is especially common in high-achievers who '
            'derived identity from role or status, and in people undergoing major life transitions.'
        ),
        historical_examples=[
            'Japanese samurai after the Meiji Restoration (1868) clung to the bushido identity '
            'in a world that no longer needed it — suicide rates among former samurai spiked '
            'dramatically. Applies to retirement, redundancy, or any transition where a '
            'central professional or social identity is removed',
            'Many Vietnam veterans could not update their identity from "warrior" to "civilian" — '
            'contributing to the highest veteran suicide rates in US history at that time. '
            'Applies to anyone whose core identity was built around a role that has ended',
            'Charles de Gaulle (France, 1890–1970): successfully updated his identity three '
            'times — from soldier to exile resistance leader to statesman to elder statesman — '
            'each time releasing the previous self-concept before the new one was certain. '
            'Applies as a positive model: identity flexibility is a skill, not a character weakness',
            'Empress Dowager Cixi of China (1861–1908): clung to a Confucian imperial identity '
            'decades after it had become functionally obsolete — blocked every institutional reform '
            'to preserve the self-concept of imperial authority. Applies to anyone whose '
            'resistance to change is really resistance to updating who they believe they are',
            'Post-colonial identity crises across Africa and Asia — entire civilisations '
            'struggling to integrate new self-concepts with ancient traditions (global). '
            'Applies to users from immigrant or multicultural backgrounds navigating '
            'identity between heritage and current environment',
            'Erik Erikson\'s psychosocial stages: failure to resolve identity vs role confusion '
            'at any stage creates developmental arrest — the psychology remains anchored to a '
            'past self even as circumstances demand growth. Applies across the lifespan: '
            'career transitions, retirement, divorce, empty nest',
        ],
        interpretations=[
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='The self is anatta — not-self, a process rather than a fixed entity. '
                       'Clinging to a self-concept is the same error as clinging to anything '
                       'impermanent. Liberation comes from releasing the need for a fixed identity.',
                advice='Practice the "I am not..." exercise: list five things you have told '
                       'yourself you ARE. Then write: "I am not only this. I am also capable of..."',
                evidence='Pali Canon, Anattalakkhana Sutta. Supported by ACT (Acceptance and '
                         'Commitment Therapy) defusion techniques — Frankl also validated this.',
                conditions='Best for individuals undergoing major role loss (retirement, divorce)'
            ),
            Interpretation(
                school='Narrative Psychology',
                culture='Western',
                stance='Identity is a story we tell about ourselves (McAdams). Stories can be '
                       'rewritten. The problem is not the old identity — it is treating it as '
                       'the only possible story. New chapters require conscious authorship.',
                advice='Write a one-page "next chapter" narrative for your life. Give it a title. '
                       'Who is the protagonist? What is their new mission? What wisdom do they '
                       'carry from previous chapters?',
                evidence='McAdams, The Stories We Live By (1993). Narrative therapy '
                         '(White & Epston, 1990) shows story-rewriting reduces depression scores.',
                conditions='Best for articulate, self-reflective individuals'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The junzi continuously cultivates (xiushen) — self-cultivation is never '
                       'finished. Each life stage (the five relationships change as children grow, '
                       'as parents die) requires updating who one is in relation to others.',
                advice='Map your current roles and relationships. Which ones have changed? '
                       'Who do you need to be now in each? Confucian identity is relational, '
                       'not individual — update your relationships to update yourself.',
                evidence='Analects 2:4 — Confucius describes his own development decade by decade: '
                         '"At 15, I bent my mind on learning. At 30, I stood firm..."',
                conditions='Best when person has strong family/social orientation'
            ),
        ],
        resolution_hint=(
            'Role loss (retirement, redundancy) → Narrative Psychology + Confucian roles. '
            'Spiritual/philosophical → Buddhist anatta. '
            'High-achiever identity crisis → all three in sequence.'
        ),
        keywords=['used to be', 'I was', 'I\'m not who I was', 'lost myself',
                  'don\'t know who I am', 'changed', 'retired', 'not the same',
                  'identity', 'purpose', 'role', 'what I do'],
        urgency_when_detected='medium'
    ),
]


# ─────────────────────────────────────────────────────
# Query interface
# ─────────────────────────────────────────────────────

def get_lesson_by_id(lesson_id: str) -> Optional[WisdomLesson]:
    """Return the lesson or None if not found. Use get_lesson_by_id_safe for must-exist calls."""
    return next((l for l in WISDOM_LESSONS if l.id == lesson_id), None)


def get_lesson_by_id_safe(lesson_id: str) -> WisdomLesson:
    """Return the lesson or raise ValueError with a clear message if not found."""
    lesson = get_lesson_by_id(lesson_id)
    if lesson is None:
        raise ValueError(
            f"Lesson '{lesson_id}' not found in WISDOM_LESSONS. "
            f"Valid IDs: {[l.id for l in WISDOM_LESSONS]}"
        )
    return lesson


def get_lessons_by_mistake_type(mistake_type: str) -> List[WisdomLesson]:
    return [l for l in WISDOM_LESSONS if l.mistake_type == mistake_type]


def get_lessons_by_domain(domain: str) -> List[WisdomLesson]:
    return [l for l in WISDOM_LESSONS if domain in l.domains]


def match_lessons_to_text(text: str, threshold: int = 2) -> List[WisdomLesson]:
    """
    Match lessons to free text (user messages, pattern descriptions) by keyword overlap.
    Uses word-boundary matching to avoid fragment false positives (e.g. 'anger' in 'stranger').
    Returns lessons sorted by match count descending.
    """
    text_lower = text.lower()
    scored = []
    for lesson in WISDOM_LESSONS:
        hits = 0
        for kw in lesson.keywords:
            if ' ' in kw:
                hits += 1 if kw in text_lower else 0
            else:
                hits += 1 if re.search(r'\b' + re.escape(kw) + r'\b', text_lower) else 0
        if hits >= threshold:
            scored.append((hits, lesson))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in scored]


def match_lessons_to_patterns(pattern_descriptions: List[str]) -> List[WisdomLesson]:
    """
    Match a list of detected user patterns to wisdom lessons.
    Scores each lesson against each pattern individually (not concatenated) to avoid
    false positives from keyword collisions across unrelated patterns.
    Uses word-boundary matching to avoid fragment false positives (e.g. 'anger' in 'stranger').
    Returns lessons sorted by best single-pattern score descending.
    """
    if not pattern_descriptions:
        return []

    def _wm(text: str, phrase: str) -> bool:
        if ' ' in phrase:
            return phrase in text
        return bool(re.search(r'\b' + re.escape(phrase) + r'\b', text))

    lesson_scores: Dict[str, int] = {}
    for pattern in pattern_descriptions:
        text_lower = pattern.lower()
        for lesson in WISDOM_LESSONS:
            hits = sum(1 for kw in lesson.keywords if _wm(text_lower, kw))
            if hits > 0:
                # Accumulate (sum) hits across all patterns: rewards breadth-of-relevance
                # so a lesson matching 2 patterns beats one matching only 1 pattern deeply.
                lesson_scores[lesson.id] = lesson_scores.get(lesson.id, 0) + hits

    # Keep lessons with at least 1 hit across all patterns (Python 3.7-compatible)
    matched = [(lesson_scores[l.id], l) for l in WISDOM_LESSONS
               if lesson_scores.get(l.id, 0) >= 1]
    matched.sort(key=lambda x: x[0], reverse=True)
    return [l for _, l in matched]


_EASTERN_MARKERS = ('eastern', 'chinese', 'japanese', 'korean', 'indian', 'confucian',
                    'dynasty', 'emperor', 'meiji', 'tang', 'ming', 'qing', 'okinaw',
                    'tao', 'buddhist', 'vedant')
_WESTERN_MARKERS = ('western', 'roman', 'greek', 'british', 'french', 'american',
                    'napoleon', 'churchill', 'lincoln', 'stoic', 'socrat', 'freud',
                    'jung', 'erikson', 'vietnam', 'usa', 'europe')


def _pick_historical_examples(
    lesson: 'WisdomLesson',
    user_domains: List[str],
    n: int = 3
) -> List[str]:
    """
    Pick the most contextually relevant historical examples for this user.
    Prefers examples whose 'Applies to' tag mentions the user's active domains.
    Always tries to include at least one Eastern and one Western example for breadth.
    Falls back to the first n examples if no domain match is found.
    """
    domain_keywords = {
        'health':         ['health', 'doctor', 'symptom', 'body', 'cardiac', 'medical', 'illness'],
        'finance':        ['financ', 'debt', 'saving', 'money', 'investment', 'bank', 'economic'],
        'relationships':  ['relationship', 'marriage', 'partner', 'family', 'relational', 'trust'],
        'career':         ['career', 'work', 'job', 'professional', 'manager', 'leader', 'redundan'],
        'retirement':     ['retirement', 'retired', 'role ended', 'post-peak', 'empty nest'],
        'mental_health':  ['mental', 'depression', 'anxiety', 'trauma', 'grief', 'isolation', 'burnout'],
    }
    active_kws: List[str] = []
    for d in user_domains:
        active_kws.extend(domain_keywords.get(d, []))

    if not active_kws:
        return lesson.historical_examples[:n]

    def _wm_domain(text: str, phrase: str) -> bool:
        """Word-boundary match for domain keywords inside historical example text."""
        if ' ' in phrase:
            return phrase in text
        return bool(re.search(r'\b' + re.escape(phrase) + r'\b', text))

    scored: List[tuple] = []
    for ex in lesson.historical_examples:
        ex_lower = ex.lower()
        score = sum(1 for kw in active_kws if _wm_domain(ex_lower, kw))
        scored.append((score, ex))
    scored.sort(key=lambda x: x[0], reverse=True)

    # Build initial pick from top-scored examples
    picked: List[str] = [ex for _, ex in scored[:n]]

    # Enforce Eastern+Western balance: if all picked are the same hemisphere, swap one
    picked_lower = [p.lower() for p in picked]
    has_eastern = any(any(m in p for m in _EASTERN_MARKERS) for p in picked_lower)
    has_western = any(any(m in p for m in _WESTERN_MARKERS) for p in picked_lower)

    if len(picked) >= 2 and not (has_eastern and has_western):
        missing_markers = _EASTERN_MARKERS if not has_eastern else _WESTERN_MARKERS
        # Search all remaining examples (not just scored[n:]) for the missing hemisphere
        candidates = [ex for _, ex in scored if ex not in picked
                      and any(m in ex.lower() for m in missing_markers)]
        if candidates:
            picked[-1] = candidates[0]

    # Fill up to n if still short
    if len(picked) < n:
        for _, ex in scored:
            if ex not in picked:
                picked.append(ex)
            if len(picked) >= n:
                break

    return picked


def build_wisdom_context_for_prompt(
    pattern_descriptions: List[str],
    user_domains: List[str],
    max_lessons: int = 4
) -> str:
    """
    Build a compact wisdom context string for the AI prompt.
    Returns the most relevant lessons with contextually selected historical examples.
    Historical examples are filtered to match the user's active domains so the
    AI can draw parallels that are meaningful to that specific person's situation.

    Ordering guarantee: pattern-matched lessons (scored) always come before
    domain-fill lessons so high-relevance lessons are never crowded out.
    """
    # Match by patterns first (scored by keyword overlap)
    matched = match_lessons_to_patterns(pattern_descriptions)

    # Domain-fill: append lessons NOT already matched, at the end (unscored padding)
    # This ensures pattern-matched lessons always occupy the top slots.
    # Early-exit once we have enough candidates to fill max_lessons.
    matched_ids = {l.id for l in matched}
    for domain in user_domains:
        if len(matched) >= max_lessons:
            break
        for lesson in get_lessons_by_domain(domain):
            if lesson.id not in matched_ids:
                matched.append(lesson)
                matched_ids.add(lesson.id)
            if len(matched) >= max_lessons:
                break

    lessons = matched[:max_lessons]
    if not lessons:
        return "No specific historical patterns matched. Apply general wisdom principles."

    lines = ["RELEVANT HUMAN WISDOM FROM HISTORY & PHILOSOPHY:\n"]
    for lesson in lessons:
        lines.append(f"## {lesson.title} [{lesson.mistake_type.upper()}]")
        lines.append(f"Universal pattern: {lesson.universal_pattern[:300]}")
        # Pick domain-relevant historical examples for this user's situation
        examples = _pick_historical_examples(lesson, user_domains, n=3)
        lines.append("Historical parallels (choose the most relevant for this user):")
        for ex in examples:
            lines.append(f"  - {ex}")
        lines.append("Competing interpretations (choose the best fit for this user):")
        for interp in lesson.interpretations:
            lines.append(f"  [{interp.school} / {interp.culture}]")
            lines.append(f"    Stance: {interp.stance[:200]}")
            lines.append(f"    Advice: {interp.advice[:200]}")
            lines.append(f"    Applies when: {interp.conditions}")
        lines.append(f"Resolution guide: {lesson.resolution_hint}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────
# PHASE 1 LESSONS — filling critical mistake-type gaps
# Guard against double-append on module reload (e.g. in REPL or test harness)
# ─────────────────────────────────────────────────────

_PHASE1_IDS = {'perfectionism', 'fear_of_failure', 'burnout_and_overextension',
               'grief_and_loss', 'chronic_people_pleasing'}
_existing_ids = {l.id for l in WISDOM_LESSONS}
if not _PHASE1_IDS.issubset(_existing_ids):
    WISDOM_LESSONS += [

    WisdomLesson(
        id='perfectionism',
        title='Perfectionism as the Enemy of Progress',
        mistake_type='perfectionism',
        domains=['career', 'health', 'relationships', 'mental_health'],
        universal_pattern=(
            'The demand for flawless execution before beginning — or the abandonment of '
            'effort the moment a standard is not met — is one of the most consistent blockers '
            'of human growth across history. It masquerades as high standards but functions '
            'as paralysis or procrastination. The perfect becomes the enemy of the good.'
        ),
        historical_examples=[
            'Voltaire coined "Le mieux est l\'ennemi du bien" (1772) — the best is the enemy '
            'of the good — observing that French Enlightenment projects stalled chasing '
            'perfection while English pragmatism produced results. Applies to anyone '
            'delaying action until conditions are ideal',
            'The Japanese concept of wabi-sabi: imperfection is not a flaw but the natural '
            'condition of all things; the tea ceremony uses imperfect vessels intentionally. '
            'Applies to anyone whose standards prevent them from starting, sharing, or completing',
            'Leonardo da Vinci (1452–1519): left dozens of major commissions unfinished — '
            'including The Adoration of the Magi — because his perfectionism prevented '
            'completion. Despite genius, many patrons abandoned him for less talented but '
            'more reliable artists. Applies to high-ability people whose perfectionism '
            'produces less output than less gifted but action-oriented peers',
            'Emperor Yongle of China (1402–1424): his perfectionist vision for the '
            'Forbidden City was so exacting that construction took 14 years and cost '
            'the lives of an estimated million workers. Positive result but extreme cost. '
            'Applies to the hidden price of perfectionism: what relationships, health, '
            'and opportunities are sacrificed for the standard?',
            'NASA\'s shuttle programme: perfectionist culture of never admitting problems '
            'contributed to both Challenger (1986) and Columbia (2003) disasters — '
            'engineers who raised concerns were overridden to preserve the image of perfection. '
            'Applies to workplace or family cultures where admitting imperfection is unsafe',
            'Meta-analysis of 284 studies (Limburg et al., 2017): perfectionism underlies '
            'anxiety, depression, eating disorders, and OCD simultaneously. Applies to '
            'any user where high standards coexist with chronic dissatisfaction or procrastination',
        ],
        interpretations=[
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='Perfectionism is a cognitive distortion driven by all-or-nothing '
                       'thinking ("if it\'s not perfect it\'s worthless") and '
                       'selective abstraction (focusing on the one flaw in many successes). '
                       'Behavioural experiments that prove imperfect action still produces '
                       'good outcomes are the primary intervention.',
                advice='Design a deliberate "good enough" experiment: choose one task where '
                       'you normally over-invest and submit it at 80% effort. Record the '
                       'actual consequence. Repeat until the cognitive distortion weakens.',
                evidence='Shafran et al., Cognitive Behaviour Therapy for Perfectionism (2010). '
                         'Flett & Hewitt meta-analysis (2002): perfectionism correlates 0.34 '
                         'with depression across 125 studies.',
                conditions='Best when perfectionism manifests as procrastination or over-checking; '
                           'person is analytical and responds to behavioural evidence'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Perfectionism is attachment (upadana) to an ideal self-image. '
                       'The demand for perfection is rooted in aversion (dosa) to the '
                       'impermanence of reality. Wabi-sabi — the beauty of imperfection — '
                       'is the antidote: finding value in the incomplete and transient.',
                advice='Practise deliberate imperfection: make one thing intentionally '
                       'imperfect per day (a rough sketch, an unedited message). Notice '
                       'the discomfort without acting on it. It diminishes with repetition.',
                evidence='Pali Canon, Samyutta Nikaya 22.59: clinging to a fixed self-standard '
                         'is a form of the second fetter. Wabi-sabi tradition traced to '
                         'Sen no Rikyu (16th century), Zen tea ceremony.',
                conditions='Best when perfectionism is tied to identity ("I am someone who '
                           'does things properly"); person is spiritually or aesthetically oriented'
            ),
            Interpretation(
                school='Positive Psychology',
                culture='Western',
                stance='Seligman distinguishes adaptive "optimalism" (high standards + '
                       'acceptance of reality) from maladaptive perfectionism (high standards '
                       '+ inability to accept any shortfall). The intervention is building '
                       'psychological capital: resilience, optimism, efficacy, hope — '
                       'which allow high performance without rigidity.',
                advice='Reframe from "did I achieve the standard?" to "did I grow?" '
                       'Keep a progress journal — track improvement over time, not '
                       'distance from an ideal. Growth orientation replaces fixed standards.',
                evidence='Tal Ben-Shahar, The Pursuit of Perfect (2009). '
                         'Dweck\'s growth vs fixed mindset research (2006): fixed mindset '
                         'correlates strongly with perfectionist avoidance behaviour.',
                conditions='Best when person is achievement-driven and responds to reframing '
                           'rather than direct exposure; already has self-awareness'
            ),
        ],
        resolution_hint=(
            'Analytical + procrastination pattern → CBT behavioural experiment. '
            'Identity-level perfectionism ("I am a perfectionist") → Buddhist wabi-sabi. '
            'High achiever wanting to maintain standards → Positive Psychology optimalism. '
            'If perfectionism is causing health avoidance specifically → CBT first, then Buddhist.'
        ),
        keywords=['perfect', 'not good enough', 'all or nothing', 'if i can\'t do it right',
                  'failed', 'not ready', 'have to be perfect', 'high standards', 'flawed',
                  'never satisfied', 'imperfect', 'should be better', 'not worth doing'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='catastrophising',
        title='Catastrophising — Treating Possibility as Certainty',
        mistake_type='catastrophising',
        domains=['mental_health', 'health', 'career', 'relationships'],
        universal_pattern=(
            'The cognitive pattern of treating a possible negative outcome as if it were '
            'certain, inevitable, and unbearable. The imagination leaps to the worst case '
            'and treats it as the only case. This pattern amplifies every other difficulty '
            'and is one of the most treatable — and most common — cognitive errors across '
            'all cultures and documented throughout written history.'
        ),
        historical_examples=[
            'Epictetus (55–135 AD): "Men are disturbed not by the things which happen, but '
            'by the opinions about the things." The Stoics considered catastrophising the '
            'primary source of unnecessary suffering. Applies universally — Epictetus was '
            'born a slave and endured far worse than most users face',
            'Song Dynasty poet Su Shi (1037–1101), repeatedly exiled, wrote his most '
            'celebrated poetry during exile — catastrophising about the exile would have '
            'destroyed the work. His equanimity under genuine adversity is instructive '
            'for anyone catastrophising about lesser setbacks (Eastern)',
            'The English Civil War (1642–1651): Parliamentary leaders catastrophised that '
            'any negotiated settlement would lead to absolute tyranny — this prevented '
            'compromises that might have avoided the execution of Charles I and the '
            'subsequent instability. Applies to relationship or workplace conflicts '
            'where catastrophising about negotiation prevents resolution',
            'Emperor Hirohito\'s advisors in 1945 catastrophised that surrender would mean '
            'the complete destruction of Japanese culture — in fact, Japan\'s post-war '
            'reconstruction became the fastest economic growth in recorded history. '
            'Applies to career or life transitions where fear of the worst case '
            'prevents a necessary and ultimately beneficial change',
            'Winston Churchill\'s wartime leadership: explicitly refused to catastrophise '
            'publicly despite privately knowing the military situation was dire — '
            '"We shall fight on the beaches" was a deliberate counter to mass catastrophising. '
            'Applies to anyone whose catastrophising is spreading to family or colleagues',
            'Beck\'s cognitive model (1976): catastrophising amplifies anxiety by 2–4x. '
            'Applies directly to health anxiety, financial worry, or relationship fears '
            'where the imagined outcome is significantly worse than the probable one',
        ],
        interpretations=[
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='Catastrophising confuses what is "up to us" (our judgments) with '
                       'what is "not up to us" (external events). The Stoic practice of '
                       'negative visualisation (premeditatio malorum) — deliberately '
                       'imagining the worst in a controlled way — paradoxically reduces '
                       'catastrophic fear by making the worst familiar and survivable.',
                advice='Practise premeditatio malorum: write down the worst realistic '
                       'outcome. Then write: "If this happened, I would survive it by..." '
                       'The act of planning for it removes its power to paralyse.',
                evidence='Epictetus, Enchiridion, 5. Seneca, Letters 24: "Rehearse death — '
                         'or rather, any other condition that seems terrible."',
                conditions='Best when the person is intellectually oriented and can engage '
                           'with a thought exercise; pattern is about future uncertainty'
            ),
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='Catastrophising is a cognitive distortion: "magnification" of '
                       'negative probability and "minimisation" of coping ability. '
                       'The Socratic technique of decatastrophising — systematically '
                       'examining the evidence for the feared outcome — is the '
                       'most evidence-backed intervention.',
                advice='Use the decatastrophising chain: What is the worst that could happen? '
                       'How likely is it really (0–100%)? If it happened, could you cope? '
                       'What is the most realistic outcome? Write all four answers.',
                evidence='Beck, Cognitive Therapy of Depression (1979). '
                         'Meta-analysis of 269 RCTs (Hofmann et al., 2012): CBT for '
                         'catastrophising reduces anxiety symptoms by 50–60%.',
                conditions='Best when catastrophising is linked to specific triggers or health anxiety'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Catastrophising is the mind\'s projection of suffering into a future '
                       'that does not yet exist. The teaching of anicca (impermanence) and '
                       'the practice of returning attention to the present moment interrupt '
                       'the fear cascade before it completes.',
                advice='When you notice catastrophic thoughts: name them ("catastrophising '
                       'is happening") without engaging. Return to three sensory details '
                       'in the present room. The future fear cannot survive present-moment '
                       'attention sustained for 90 seconds.',
                evidence='MBSR (Mindfulness-Based Stress Reduction, Kabat-Zinn 1979): '
                         'reduces catastrophising scores by 44% in chronic pain populations '
                         '(Garland et al., 2012). Directly derived from vipassana practice.',
                conditions='Best when catastrophising is diffuse (not tied to one specific fear) '
                           'and person is emotionally reactive rather than analytical'
            ),
        ],
        resolution_hint=(
            'Intellectual, future-focused anxiety → Stoic premeditatio malorum. '
            'Specific trigger-based catastrophising → CBT decatastrophising chain. '
            'Diffuse, emotional, present-moment overwhelm → Buddhist mindfulness. '
            'Health-related catastrophising → CBT first (most evidence for health anxiety specifically).'
        ),
        keywords=['worst case', 'going to be terrible', 'everything will fall apart',
                  'disaster', 'can\'t cope', 'unbearable', 'what if', 'spiral',
                  'doom', 'terrible', 'catastrophe', 'panic', 'overwhelmed', 'fear'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='isolation_withdrawal',
        title='Withdrawing from Others When Support Is Most Needed',
        mistake_type='isolation',
        domains=['mental_health', 'health', 'relationships', 'retirement'],
        universal_pattern=(
            'When humans face difficulty, shame, illness, or failure, the instinct to '
            'withdraw from social connection is nearly universal — and nearly always '
            'counterproductive. Social isolation is now classified as a mortality risk '
            'equivalent to smoking 15 cigarettes per day. The pattern is especially '
            'acute after retirement, bereavement, and illness, when the structural '
            'sources of connection disappear simultaneously with the need for them.'
        ),
        historical_examples=[
            'Durkheim\'s Suicide (1897): social integration is the single strongest '
            'protective factor against suicide — isolation kills. Applies to anyone '
            'post-retirement, post-bereavement, or post-redundancy who is withdrawing '
            'from social contact',
            'Japanese hikikomori phenomenon (1990s–present): over 1 million adults '
            'withdrawn completely — a modern Eastern manifestation accelerated by '
            'cultural shame around failure. Applies to anyone withdrawing after '
            'a perceived failure, job loss, health decline, or social humiliation',
            'Emperor Diocletian (Rome, 285–305 AD): one of the few Roman emperors who '
            'voluntarily retired — and deliberately maintained a garden community, '
            'friendships, and civic engagement. When pressed to return to power he said: '
            '"Come see the cabbages I have grown with my own hands." '
            'Applies to retirement transitions: active social engagement is the difference '
            'between flourishing and decline',
            'The Hermit Scholars of Tang Dynasty China: intellectuals who withdrew from '
            'court life to solitary study were admired culturally but documented as dying '
            'younger and producing less than those who maintained scholarly communities. '
            'Even the Chinese cultural ideal of solitary wisdom required community (Eastern). '
            'Applies to introverted or intellectual users who justify isolation as virtue',
            'Nikola Tesla\'s final years (1933–1943): withdrew almost entirely from social '
            'contact, lived alone in a hotel, and his most innovative period was long over. '
            'His isolation was not a cause of his genius but a contributor to its end. '
            'Applies to high-ability people who withdraw as their productive years end',
            'Cacioppo & Patrick, Loneliness (2008): loneliness is physiological — it '
            'increases cortisol, disrupts sleep, reduces immune function, equivalent to '
            'smoking 15 cigarettes per day. Applies to any user describing social withdrawal, '
            'especially after health events or role transitions',
        ],
        interpretations=[
            Interpretation(
                school='Existentialist',
                culture='Western',
                stance='Isolation is a choice — Sartre: we are condemned to be free, '
                       'including free to remain isolated. But Camus argued that the '
                       'absurd can only be transcended through solidarity and revolt '
                       'with others, not alone. Authentic existence requires engagement, '
                       'not withdrawal.',
                advice='Name the reason for withdrawing honestly. Is it shame? Fear of '
                       'burdening others? Habit? Identify one person you trust and make '
                       'contact this week — not to solve anything, just to be present '
                       'with another human being.',
                evidence='Camus, The Myth of Sisyphus (1942). Frankl: in Auschwitz, '
                         'those who maintained human connection survived at higher rates.',
                conditions='Best when the person is intellectually reflective and the '
                           'isolation is a conscious choice they can examine'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The self is constituted through relationships (wulun). '
                       'To withdraw is to diminish the self — there is no "me" '
                       'outside of the roles and relationships that give me shape. '
                       'Withdrawal is not rest; it is self-erasure. '
                       'Ren (benevolence) requires others to practise on.',
                advice='Map the five relationships in your life right now: ruler/subject '
                       '(now: employer/community), parent/child, husband/wife, '
                       'elder/younger, friend/friend. Which are inactive? Choose one '
                       'and take one step to reactivate it this week.',
                evidence='Analects 1:6 — "A young man should be dutiful at home, '
                         'respectful outside, careful and trustworthy." The relational '
                         'self is not a metaphor — it is Confucius\'s ontology.',
                conditions='Best when person has strong family or cultural ties and '
                           'isolation is from those specific networks'
            ),
            Interpretation(
                school='Behaviourist',
                culture='Western',
                stance='Social withdrawal is a behaviour maintained by negative '
                       'reinforcement: it reduces anxiety in the short term, which '
                       'reinforces avoidance. Behavioural activation — scheduling '
                       'small, concrete social contacts — breaks the reinforcement '
                       'cycle without requiring insight or motivation first.',
                advice='Do not wait to feel like socialising. Schedule one small '
                       'social contact this week (a phone call counts). The mood '
                       'improvement follows the behaviour — it does not precede it. '
                       'Start with the lowest-effort contact in your network.',
                evidence='Lewinsohn\'s behavioural model of depression (1974): '
                         'social withdrawal reduces positive reinforcement, deepening '
                         'depression. Behavioural activation is now NICE-recommended '
                         'for depression (meta-analysis: Cuijpers et al., 2007).',
                conditions='Best when person says "I don\'t feel like it" or "I have '
                           'no energy for people" — motivation-first thinking is the block'
            ),
        ],
        resolution_hint=(
            'Deliberate, reflective isolation → Existentialist — examine the choice. '
            'Family/cultural disconnection → Confucian relational self. '
            '"No energy/motivation" barrier → Behaviourist activation (behaviour first). '
            'Post-retirement or bereavement isolation → ALL three in sequence: '
            'acknowledge the loss (Existentialist), map remaining relationships (Confucian), '
            'schedule one contact regardless of mood (Behaviourist).'
        ),
        keywords=['alone', 'isolated', 'withdrawn', 'no one', 'don\'t want to see anyone',
                  'by myself', 'lonely', 'no friends', 'pushing people away', 'hiding',
                  'closed off', 'don\'t feel like socialising', 'keep to myself'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='overconfidence',
        title='Overconfidence — Not Knowing What You Don\'t Know',
        mistake_type='overconfidence',
        domains=['career', 'health', 'finance', 'relationships'],
        universal_pattern=(
            'The consistent human tendency to overestimate one\'s knowledge, skill, '
            'and judgment — particularly in domains where one has partial knowledge. '
            'Dunning and Kruger (1999) demonstrated it experimentally, but it is '
            'documented across 2,500 years of recorded wisdom. It is most dangerous '
            'in health self-diagnosis, financial decisions, and interpersonal judgments — '
            'precisely the domains where the consequences are largest.'
        ),
        historical_examples=[
            'The Athenian disaster at Syracuse (415 BC): launched on overconfident '
            'strategic assessment by generals who had never fought there — the greatest '
            'Athenian military defeat. Applies to major decisions made without adequate '
            'expertise or consultation: health self-diagnosis, financial investments, '
            'career pivots',
            'The Qing Dynasty\'s "self-strengthening movement" (1861–1895): officials '
            'overestimated their understanding of Western technology — defeat in the '
            'First Sino-Japanese War followed (Eastern). Applies to anyone importing '
            'new tools or approaches without understanding the underlying principles',
            'Napoleon\'s invasion of Russia (1812): his overconfidence in his own '
            'military genius — and his dismissal of advisors who warned against it — '
            'destroyed the Grande Armée of 600,000. Of the men who entered Russia, '
            'fewer than 100,000 returned. Applies to high-achievers who mistake '
            'past success for guaranteed future success',
            'Emperor Xuanzong of Tang (685–762 AD): his overconfident trust in '
            'An Lushan as a military commander — despite multiple warning signs from '
            'advisors — led to the An Lushan Rebellion, which killed 13–36 million '
            'people and permanently weakened the dynasty (Eastern). Applies to '
            'misplaced trust in relationships, business partners, or health practitioners',
            'Charles I of England: overconfidently dismissed Parliament\'s concerns '
            'about his rule, believing divine right made opposition illegitimate — '
            'executed in 1649. Applies to any relationship or workplace conflict where '
            'one party refuses to consider they might be wrong',
            'Dunning & Kruger (1999): least competent performers overestimated by 50 '
            'percentile points. Crucially, gaining competence enables recognising '
            'previous incompetence. Applies to health self-diagnosis, financial '
            'decision-making, and relationship judgments',
        ],
        interpretations=[
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='Overconfidence violates the Stoic commitment to accurate '
                       'judgment (synkatathesis). The Stoics held that assenting to '
                       'impressions without sufficient examination is the root of '
                       'error. Marcus Aurelius practised constant epistemic humility: '
                       '"How much is lost by not knowing what is in other men\'s minds! '
                       'But how little is lost by not knowing what is in yours." '
                       'The discipline of assent requires pausing before certainty.',
                advice='Before any major decision, write: "What do I know for certain? '
                       'What am I assuming? Who knows more than me about this?" '
                       'Identify the one person whose opinion would most challenge yours '
                       'and actively seek it out.',
                evidence='Marcus Aurelius, Meditations 9:18. Epictetus: "It is impossible '
                         'to begin to learn that which one thinks one already knows."',
                conditions='Best when the person is confident and intellectually capable '
                           'but making decisions without consulting others'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Confucius explicitly linked overconfidence to incomplete learning. '
                       '"Real knowledge is to know the extent of one\'s ignorance." '
                       'The junzi seeks teachers, not confirmation. Zhengming '
                       '(rectification of names) requires calling things by their '
                       'correct names — including calling one\'s ignorance ignorance.',
                advice='For any area where you feel confident: identify one acknowledged '
                       'expert and one book or primary source you have not read. '
                       'The willingness to be a student in a domain you think you know '
                       'is the Confucian mark of genuine knowledge.',
                evidence='Analects 2:17 — "When you know a thing, to recognise that '
                         'you know it; when you do not know a thing, to recognise '
                         'that you do not know it. This is knowledge."',
                conditions='Best when overconfidence is domain-specific and person '
                           'has strong intellectual values'
            ),
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='Overconfidence is an availability bias — we judge our knowledge '
                       'by how easily examples come to mind, not by the actual depth '
                       'of what we know. The Dunning-Kruger effect shows this is not '
                       'arrogance but a genuine metacognitive failure: we cannot '
                       'accurately assess what we don\'t know until we know more.',
                advice='Use calibration training: make 10 specific predictions about '
                       'a domain you feel confident in, assign a probability to each, '
                       'then check results. People who do this regularly become '
                       'reliably better calibrated within weeks.',
                evidence='Dunning & Kruger, Unskilled and Unaware of It (1999). '
                         'Superforecasting research (Tetlock & Gardner, 2015): '
                         'calibration practice increases predictive accuracy by 60%.',
                conditions='Best for analytically minded people; works when there '
                           'are concrete, verifiable predictions to test against'
            ),
        ],
        resolution_hint=(
            'Major decision without consultation → Stoic epistemic humility. '
            'Domain-specific expertise overconfidence → Confucian student stance. '
            'Analytical person who responds to data → CBT calibration training. '
            'Health self-diagnosis overconfidence → flag as HIGH urgency + CBT + Stoic.'
        ),
        keywords=['I know', 'obvious', 'don\'t need to check', 'sure about', 'certain',
                  'no need for advice', 'already know', 'don\'t need a doctor', 'trust myself',
                  'confident', 'definitely', 'without a doubt', 'not that complicated'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='grief_transition_resistance',
        title='Resisting Grief and Life Transitions',
        mistake_type='avoidance',
        domains=['mental_health', 'relationships', 'retirement', 'health'],
        universal_pattern=(
            'The refusal to grieve — to fully process loss, endings, and major transitions — '
            'is one of the most documented causes of prolonged psychological suffering. '
            'The loss may be of a person, a role, a physical ability, a relationship, '
            'or an identity. Societies and individuals consistently attempt to bypass '
            'grief through distraction, intellectualisation, or premature "moving on," '
            'which invariably prolongs the suffering rather than abbreviating it.'
        ),
        historical_examples=[
            'The Roman tradition of elaborate public mourning (luctus): grief required '
            'social permission and ritual structure — its suppression was considered '
            'socially dangerous. Roman generals who lost battles were expected to mourn '
            'publicly before returning to command. Applies to anyone told to "move on" '
            'before genuine processing has occurred',
            'Confucian mourning rites (sang li) prescribed three years of mourning for '
            'a parent — not punishment but recognition that grief restructures the '
            'relational world and takes time (Eastern). Applies to bereavement, '
            'retirement, divorce, or any loss of a central relationship or role',
            'Abraham Lincoln\'s grief: the death of his son Willie (1862) during the '
            'Civil War plunged him into prolonged grief that his advisors feared would '
            'incapacitate him — instead, processed rather than suppressed, it deepened '
            'his empathy and is credited with shaping the compassion of his Reconstruction '
            'plans. Applies to high-functioning people who fear grief will incapacitate them',
            'Emperor Meiji of Japan (1867–1912): his modernisation of Japan required '
            'grieving the entire Confucian-feudal world order — he conducted elaborate '
            'ritual mourning for abolished institutions while simultaneously building new '
            'ones. Transition and grief were not opposites but companions (Eastern). '
            'Applies to major life transitions where the new cannot begin until the '
            'old is properly honoured',
            'Post-WWII Japan\'s enforced suppression of collective grief about Hiroshima '
            'and the emperor-worship collapse led to what psychiatrists called "the silence" '
            '— a national trauma that took generations to surface. Applies to families or '
            'individuals where grief has been suppressed by cultural or social pressure',
            'Kübler-Ross (1969): grief suppression in terminal patients increased distress; '
            'supported grief reduced it. Applies to any loss: bereavement, retirement, '
            'divorce, health decline, or end of a significant life chapter',
        ],
        interpretations=[
            Interpretation(
                school='Psychoanalytic',
                culture='Western',
                stance='Freud\'s Mourning and Melancholia (1917) distinguished healthy '
                       'grief (mourning) from pathological grief (melancholia). '
                       'In mourning, the ego gradually detaches from the lost object. '
                       'In melancholia, the loss is internalised and turned against '
                       'the self. The cure is not "getting over it" but completing '
                       'the mourning process — which requires time and consciousness.',
                advice='Give the loss a name. Write about it as though explaining '
                       'it to someone who doesn\'t know you. What exactly was lost? '
                       'What did it mean to you? What will you never have again? '
                       'The grief that is spoken is grief that can move.',
                evidence='Freud, Mourning and Melancholia (1917). '
                         'Stroebe & Schut, Dual Process Model of Coping with '
                         'Bereavement (1999): oscillating between grief and '
                         'restoration is healthier than either extreme.',
                conditions='Best when grief has been intellectualised or suppressed; '
                           'person uses insight and language well'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Grief is an expression of ren (benevolence/love) — to grieve '
                       'is to honour. The three-year mourning period was not arbitrary: '
                       'it recognised that major losses restructure one\'s entire '
                       'relational world and that this restructuring takes time. '
                       'Rushing grief dishonours the relationship that was lost.',
                advice='Create a small ritual for the loss. It does not need to be '
                       'elaborate — it needs to be intentional. A weekly act, a '
                       'dedicated moment. Confucian wisdom says: the ritual is what '
                       'turns raw grief into structured mourning that has an end.',
                evidence='Analects 17:21 — Confucius refuses to shorten mourning '
                         'rites, arguing the comfort of the rites is what makes '
                         'the grief bearable and finite.',
                conditions='Best when person has cultural or family values around '
                           'respect and honouring; grief from bereavement or role loss'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Grief arises from attachment (upadana). The Buddhist response '
                       'is not to suppress grief — the Buddha wept at the death of '
                       'his disciples — but to grieve without clinging to the grief '
                       'itself. Anicca (impermanence) is not a comfort that denies '
                       'loss; it is an invitation to let the loss be real without '
                       'making it permanent.',
                advice='Allow the grief fully for a set period — 20 minutes today. '
                       'Then return to the present moment. The practice is not '
                       'suppression but cycling: grieve fully, then return. '
                       'Grief clinging to itself becomes suffering; grief that '
                       'moves becomes wisdom.',
                evidence='Therigatha (verses of the elder nuns): multiple poems '
                         'of grief and release. Buddhist chaplaincy research shows '
                         'impermanence teaching reduces prolonged grief disorder '
                         'in palliative care (Kellehear, 2000).',
                conditions='Best when person is stuck in repetitive grief or '
                           'oscillates between avoiding and being overwhelmed'
            ),
        ],
        resolution_hint=(
            'Grief intellectualised or suppressed → Psychoanalytic (name the loss). '
            'Grief from bereavement or loss of role → Confucian ritual and honour. '
            'Grief that cycles or overwhelms → Buddhist: grieve fully, return. '
            'Retirement + role loss + health decline together → HIGH urgency; '
            'all three interpretations in sequence; consider referral to counselling.'
        ),
        keywords=['lost', 'grief', 'gone', 'can\'t get over', 'miss', 'bereavement',
                  'passed away', 'ended', 'transition', 'change', 'letting go',
                  'moving on', 'not the same', 'never be the same', 'mourning'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='financial_denial',
        title='Avoiding Financial Reality',
        mistake_type='financial_denial',
        domains=['finance', 'career', 'mental_health'],
        universal_pattern=(
            'The systematic avoidance of accurate financial information — not opening '
            'statements, not calculating debt, not reviewing spending — is one of the '
            'most consistent and most harmful forms of avoidance. It is not caused '
            'by lack of intelligence but by anxiety, shame, and the same avoidance '
            'mechanisms that operate in health and relationships. The gap between '
            'financial reality and financial belief grows larger the longer it '
            'is left unexamined.'
        ),
        historical_examples=[
            'The Roman aristocracy refused to examine their estates\' actual finances — '
            'Pliny the Younger wrote extensively about wealthy families who discovered '
            'ruin only at death, protected from the numbers by household staff. '
            'Applies to anyone whose financial avoidance is enabled by comfort or status',
            'The Ming Dynasty\'s fiscal collapse: emperors refused to examine treasury '
            'reports showing insolvency for decades — the dynasty could no longer pay '
            'its armies (Eastern, 17th century). Applies to long-term financial denial '
            'where the avoidance has compounded the underlying problem',
            'Louis XVI of France (1754–1793): his finance ministers repeatedly presented '
            'accurate accounts of royal bankruptcy — he dismissed three ministers in '
            'succession for delivering unwelcome numbers. The French Revolution followed. '
            'Applies to anyone dismissing financial advisors, accountants, or family '
            'members who try to surface financial reality',
            'The Greek government\'s concealment of deficit figures before the 2010 '
            'debt crisis: financial denial at national scale — politicians avoided '
            'confronting numbers until the crisis required IMF intervention and '
            'decade-long austerity. Applies to personal finance: the longer the '
            'denial, the more painful the eventual reckoning',
            'Henry Ford\'s later years: refused to examine sales data showing the '
            'Model T was losing market share to General Motors — denied reality until '
            'the company nearly collapsed. He had built his empire on data-driven '
            'decisions but refused the same discipline when the data was unwelcome. '
            'Applies to anyone who was once financially astute but is now avoiding '
            'uncomfortable financial truths',
            'Kahneman, Thinking Fast and Slow (2011): financial loss aversion causes '
            'ostrich-effect avoidance — the anticipated pain of seeing a bad number '
            'exceeds the benefit of knowing it. Predictable mechanism, not a character flaw. '
            'Applies to anyone avoiding bank statements, investment values, or debt figures',
        ],
        interpretations=[
            Interpretation(
                school='Behavioural Economics',
                culture='Western',
                stance='Financial avoidance is driven by loss aversion and the '
                       'ostrich effect — people literally look away from negative '
                       'financial information more than positive. The solution is '
                       'not willpower but system design: automatic visibility '
                       '(statements that arrive and must be acknowledged) and '
                       'removing the friction of checking.',
                advice='Set up one automatic financial visibility trigger this week: '
                       'a monthly calendar alert to open one statement, or a '
                       'budgeting app that sends a weekly summary. '
                       'The goal is not to fix everything — it is to make '
                       'avoidance structurally harder than knowing.',
                evidence='Galai & Sade, The Ostrich Effect (2006): investors '
                         'check portfolios less in downturns. Thaler & Sunstein, '
                         'Nudge (2008): automatic enrolment increases savings '
                         'participation from 40% to 90%.',
                conditions='Best for practical, systems-oriented people; '
                           'works when the avoidance is structural, not shame-based'
            ),
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='Financial reality, however uncomfortable, belongs to '
                       'the category of "things that are" — and Stoic wisdom '
                       'requires seeing what is, not what is comfortable. '
                       'Seneca, who managed enormous wealth, wrote extensively '
                       'about the distinction between the fear of poverty and '
                       'actual poverty: confronting the numbers makes the '
                       'fear concrete and therefore manageable.',
                advice='Spend 30 minutes this week calculating your actual '
                       'financial position: total assets, total liabilities, '
                       'monthly inflow, monthly outflow. No judgments — just '
                       'numbers. The Stoic holds that knowing the real situation '
                       'is always better than not knowing, however uncomfortable.',
                evidence='Seneca, Letters 17–18: on financial clarity and the '
                         'fear of poverty. "Omnia aliena sunt, tempus tantum '
                         'nostrum est" — what you own does not define you.',
                conditions='Best when shame is the primary barrier; '
                           'person has intellectual capacity to separate '
                           'self-worth from net worth'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='Financial clarity is an expression of self-cultivation (xiushen). '
                       'The Daxue (Great Learning) describes bringing order to one\'s '
                       'household (qijia) as the precondition for contributing to '
                       'society. A disordered household — including financially — '
                       'prevents the person from fully developing or serving others.',
                advice='Treat one financial review session as an act of self-respect '
                       'and family responsibility. Prepare one simple written summary '
                       'of your household\'s financial position. '
                       'You cannot order what you cannot see.',
                evidence='Daxue (Great Learning), Chapter 1: '
                         '"Their households being regulated, their states were rightly governed." '
                         'The sequence begins with the individual and household.',
                conditions='Best when person has strong family or social responsibility values; '
                           'avoidance is driven by shame toward family rather than self'
            ),
        ],
        resolution_hint=(
            'Structural avoidance (never looks at numbers) → Behavioural Economics system design. '
            'Shame-based avoidance → Stoic separation of self-worth from net worth. '
            'Family responsibility values → Confucian household ordering. '
            'If debt is significant → HIGH urgency; recommend professional financial advice '
            'alongside any of the above interpretations.'
        ),
        keywords=['debt', 'money', 'finances', 'bills', 'savings', 'spending',
                  'can\'t afford', 'financial', 'broke', 'overdraft', 'credit',
                  'not enough money', 'avoid looking', 'don\'t want to know',
                  'financial stress', 'money worries'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='social_conformity',
        title='Following the Crowd Against One\'s Own Judgment',
        mistake_type='social_conformity',
        domains=['career', 'relationships', 'finance', 'mental_health'],
        universal_pattern=(
            'The suppression of one\'s own accurate judgment in favour of social '
            'consensus — even when that consensus is demonstrably wrong. '
            'Asch\'s conformity experiments showed that 75% of people will give '
            'a factually wrong answer at least once when surrounded by others '
            'giving that answer. This is not weakness — it is a deeply wired '
            'social survival mechanism that becomes pathological in modern '
            'complex environments requiring independent judgment.'
        ),
        historical_examples=[
            'The Bay of Pigs invasion (1961): Kennedy\'s advisors suppressed doubts '
            'to maintain group cohesion — producing a decision they privately knew '
            'was flawed. Janis coined "groupthink" from this case. Applies to '
            'family, workplace, or social group decisions where expressing doubt '
            'feels socially dangerous',
            'Galileo Galilei (1564–1642): recanted his heliocentric model under '
            'pressure from the Inquisition — the ultimate historical example of '
            'social conformity overriding individual knowledge. But his private '
            'notebooks show he never stopped believing the truth. Applies to anyone '
            'publicly conforming while privately knowing better',
            'The Ming Dynasty\'s collective Confucian orthodoxy suppressed scientific '
            'inquiry — scholars who raised new ideas were marginalised (Eastern, '
            '15th–17th century). Japan avoided the same trap via the Rangaku '
            '(Dutch learning) movement where individual scholars defied conformity '
            'to import Western science. Applies to career and intellectual contexts '
            'where conformity blocks learning or advancement',
            'Tulip Mania (Netherlands, 1637) and South Sea Bubble (1720): both '
            'sustained entirely by social conformity — people invested because '
            'others were investing. Individual investors who followed independent '
            'analysis exited before collapse; conformists lost everything. '
            'Applies to financial decisions driven by what peers or media are doing',
            'Emperor Qianlong of China (1736–1795): when British envoy Lord Macartney '
            'proposed trade agreements, conformity to Sinocentric assumptions '
            '("China needs nothing from barbarians") prevented engagement with '
            'a changing world — contributing to China\'s later vulnerability. '
            'Applies to anyone whose conformity to past assumptions blocks '
            'engagement with present reality',
            'Asch conformity experiments (1951): 75% gave wrong answers at least once; '
            '5% conformed on every trial — even when the correct answer was obvious. '
            'Applies to medical decisions (going along with family pressure), financial '
            'choices (following the crowd), and relationship decisions (staying because '
            'it is expected)',
        ],
        interpretations=[
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='The Stoics identified the "herd" (ochlos) as a constant '
                       'threat to rational judgment. Marcus Aurelius wrote: '
                       '"Receive without pride, relinquish without struggle." '
                       'The Stoic test is whether an action follows from logos '
                       '(reason) or from social pressure. The crowd is not '
                       'a reliable guide to virtue or truth.',
                advice='For any decision where you\'re following others: write '
                       'down what you would do if no one would ever know your '
                       'choice. If the answer differs from what you\'re doing, '
                       'the difference is conformity. Examine it.',
                evidence='Marcus Aurelius, Meditations 3:4. Epictetus: '
                         '"First say to yourself what you would be; then do what '
                         'you have to do."',
                conditions='Best when the person is intellectually independent '
                           'but socially anxious about standing out'
            ),
            Interpretation(
                school='Positive Psychology',
                culture='Western',
                stance='Conformity suppresses authentic self-expression — '
                       'a core component of wellbeing in Seligman\'s PERMA model. '
                       'Csikszentmihalyi\'s flow research shows that peak experience '
                       'requires intrinsically motivated engagement, which '
                       'conformity systematically undermines.',
                advice='Identify one area where you\'re doing what you think '
                       'you\'re supposed to do, rather than what genuinely '
                       'engages you. Design one experiment in that area where '
                       'you follow your own judgment for 30 days and measure '
                       'your actual wellbeing.',
                evidence='Csikszentmihalyi, Flow (1990). Seligman, Authentic '
                         'Happiness (2002): authentic expression is the strongest '
                         'predictor of sustained wellbeing.',
                conditions='Best when conformity is suppressing genuine interests '
                           'or talents; person is growth-oriented'
            ),
            Interpretation(
                school='Psychoanalytic',
                culture='Western',
                stance='Conformity is often driven by fear of abandonment or '
                       'punishment — object relations theory (Winnicott, Fairbairn) '
                       'shows that the "false self" develops precisely to conform '
                       'to others\' expectations and protect the "true self." '
                       'The conformist may not even know what they actually think '
                       'until they explore what they have been suppressing.',
                advice='Ask: "Whose voice am I hearing when I tell myself I must '
                       'conform?" Journal about the earliest memory of suppressing '
                       'your own view to fit in. The origin of the pattern often '
                       'reveals its remedy.',
                evidence='Winnicott, The Maturational Processes and the '
                         'Facilitating Environment (1965): true self / false self. '
                         'Bowlby: anxious attachment predicts conformist behaviour '
                         'in social settings.',
                conditions='Best when conformity has a strong emotional charge '
                           'or the person shows significant anxiety about disapproval'
            ),
        ],
        resolution_hint=(
            'Intellectual independence but social anxiety → Stoic logos vs crowd. '
            'Authentic expression suppressed by expectations → Positive Psychology PERMA. '
            'Strong emotional charge around disapproval → Psychoanalytic true/false self. '
            'Financial conformity (investing because others are) → Behavioural Economics first, '
            'then Stoic independent judgment.'
        ),
        keywords=['everyone else is', 'supposed to', 'what people expect', 'fit in',
                  'follow the crowd', 'don\'t want to stand out', 'what others think',
                  'pressure to', 'should according to', 'peer pressure', 'conform',
                  'expected of me', 'going along with'],
        urgency_when_detected='medium'
    ),

]


# ─────────────────────────────────────────────────────
# PHASE 2 LESSONS — Eastern/Universal school balance
# New schools: Taoist, Vedantic, Ikigai/Bushido, Ubuntu, Socratic
# ─────────────────────────────────────────────────────

WISDOM_LESSONS += [

    WisdomLesson(
        id='overcontrol_forcing',
        title='Forcing Outcomes Instead of Allowing Natural Flow',
        mistake_type='perfectionism',
        domains=['career', 'relationships', 'health', 'mental_health'],
        universal_pattern=(
            'The belief that sufficient effort, control, and intervention can force '
            'any desired outcome — and that anything short of full control is failure. '
            'This creates exhaustion, brittle plans that collapse at first resistance, '
            'and a chronic inability to distinguish between what can be changed and '
            'what must be accepted. It is the mirror image of passivity: '
            'overcontrol is as damaging as underaction, and far less visible.'
        ),
        historical_examples=[
            'The Yellow Emperor\'s Classic of Medicine (Huangdi Neijing, ~200 BC): '
            'health is balance, not conquest — forcing the body against its natural rhythms '
            'is the primary cause of disease in the oldest continuous medical tradition. '
            'Applies to health overcontrol: over-exercising, extreme diets, ignoring '
            'recovery signals',
            'The Great Leap Forward (China, 1958–62): Mao\'s attempt to force '
            'industrial and agricultural transformation at unnatural speed caused '
            '15–55 million deaths — the most catastrophic example of overcontrol in '
            'recorded history. Applies to anyone who believes any outcome can be '
            'forced through sufficient effort and willpower',
            'Philip II of Spain (1527–1598): micromanaged the Armada campaign '
            'down to the tactical level from Madrid — commanders on the water were '
            'forbidden to adapt to conditions. The Armada failed not from lack of ships '
            'but from the commander\'s inability to respond to weather (Western). '
            'Applies to managers, parents, or partners who cannot delegate or allow others\' judgment',
            'Gandhi\'s Salt March (1930): achieved what direct confrontation could not '
            'through wu wei-like non-forcing resistance — the most successful anti-colonial '
            'campaign in history succeeded by moving with moral force, not against '
            'physical force. Applies to any situation where force has failed '
            'and a different approach is needed',
            'Alexander the Great: campaigns succeeded through flexibility but his death '
            'at 32 followed years of ignoring his body\'s signals to rest. Applies to '
            'high-achievers whose overcontrol of outcomes coexists with neglect of self',
            'Burnout research (Maslach & Leiter, 1997): chronic overcontrol is the '
            'most consistent predictor of occupational burnout. Applies to any user '
            'showing exhaustion, cynicism, or reduced effectiveness despite maximum effort',
        ],
        interpretations=[
            Interpretation(
                school='Taoist',
                culture='Eastern',
                stance='Wu wei (non-forcing action) is not passivity — it is action '
                       'that moves with the natural current of events rather than '
                       'against it. The Tao Te Ching (Laozi, ~6th century BC) teaches '
                       'that water shapes stone not by force but by persistence and '
                       'alignment with what is. Forcing produces resistance; '
                       'aligned action produces effortless results.',
                advice='Identify one situation where you are pushing hard with '
                       'diminishing returns. Ask: "What is the natural direction '
                       'here if I stop forcing?" Take one small step with the '
                       'current instead of against it and observe what happens.',
                evidence='Tao Te Ching, Chapter 8: "The highest good is like water — '
                         'it benefits all things without striving." Chapter 78: '
                         '"Nothing in the world is as soft as water, yet nothing '
                         'is better at overcoming the hard."',
                conditions='Best when the person is exhausted by effort that produces '
                           'little result; overcontrol driven by anxiety rather than strategy'
            ),
            Interpretation(
                school='Stoic',
                culture='Western',
                stance='The dichotomy of control (Epictetus) provides the same insight '
                       'from a Western angle: some things are "up to us" (our judgments, '
                       'intentions, actions) and some are not. Energy spent trying to '
                       'control what is not up to us is wasted — and creates '
                       'the suffering of frustrated attachment.',
                advice='List every outcome you are currently trying to control. '
                       'Mark each: is this actually in my control? For those that '
                       'are not — write the specific action that is in your control '
                       'and redirect your energy there exclusively.',
                evidence='Epictetus, Enchiridion, 1: "Some things are in our control '
                         'and others not." This opening principle structures all '
                         'Stoic practice.',
                conditions='Best when overcontrol is intellectual and the person '
                           'responds to logical frameworks'
            ),
            Interpretation(
                school='CBT / Psychology',
                culture='Western',
                stance='Overcontrol is a safety behaviour — it provides short-term '
                       'anxiety relief by creating the illusion of certainty. '
                       'Intolerance of uncertainty (IU) is now recognised as a '
                       'transdiagnostic factor underlying most anxiety disorders. '
                       'Graduated exposure to uncertainty — allowing small outcomes '
                       'to be uncontrolled — reduces IU over time.',
                advice='Choose one low-stakes situation this week where you would '
                       'normally over-plan or over-check. Deliberately do not check. '
                       'Record the actual outcome. The goal is proving to your '
                       'nervous system that uncertainty is survivable.',
                evidence='Dugas et al., Intolerance of Uncertainty Scale (1997). '
                         'Carleton et al. (2016): IU is a stronger predictor of '
                         'anxiety than negative affect alone.',
                conditions='Best when overcontrol manifests as checking, planning, '
                           'over-preparing, or inability to delegate'
            ),
        ],
        resolution_hint=(
            'Exhaustion from effort with diminishing returns → Taoist wu wei. '
            'Logical, framework-oriented person → Stoic dichotomy of control. '
            'Anxiety-driven overcontrol (checking, planning) → CBT intolerance of uncertainty. '
            'Physical burnout signs present → HIGH urgency; Taoist body-rhythm approach first.'
        ),
        keywords=['control', 'force', 'make it work', 'push through', 'can\'t let go',
                  'need to manage', 'have to oversee', 'micromanage', 'exhausted',
                  'burned out', 'not delegating', 'need things done my way',
                  'won\'t stop until', 'drive myself'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='identity_purpose_loss',
        title='Loss of Purpose When a Central Role Ends',
        mistake_type='meaning_vacuum',
        domains=['retirement', 'career', 'mental_health', 'relationships'],
        universal_pattern=(
            'When a person\'s central source of identity — a career, a role as parent, '
            'a physical capability, a relationship — is removed, a purpose vacuum '
            'appears that is frequently left unfilled. The pattern across cultures is '
            'identical: the person who was entirely defined by the role has no '
            'identity independent of it. The transition to retirement, empty nest, '
            'disability, or redundancy triggers an existential crisis that '
            'is rarely prepared for in advance.'
        ),
        historical_examples=[
            'The Bhagavad Gita (~200 BC–200 AD): Arjuna\'s crisis on the battlefield '
            'is the archetypal identity-purpose collapse — warrior identity against '
            'family duty. Krishna\'s answer — dharma beyond any single role — is '
            'the Vedantic resolution. Applies universally to anyone whose identity '
            'has been built around a single role that has ended or is ending',
            'Hiroo Onoda (Japan, 1922–2014): continued fighting in the Philippine '
            'jungle until 1974 because his identity was entirely fused with his '
            'military role — he could not update it when the world changed. '
            'Applies to extreme identity fusion: anyone who has lost the role '
            'they built their entire selfhood around',
            'Roman senators after Augustus (27 BC): many who had defined themselves '
            'through political service were psychologically destroyed when Augustus '
            'removed meaningful senatorial power. Some found new purpose in philosophy '
            '(Seneca) or scholarship; others did not recover. Applies to professionals '
            'post-redundancy and retirees who have not cultivated identity outside work',
            'Nelson Mandela (1918–2013): in 27 years of imprisonment, deliberately '
            'cultivated multiple identity sources — lawyer, teacher, father, leader — '
            'so that no single role could destroy him if removed. Released at 72, '
            'he had a richer sense of purpose than most people half his age. '
            'Applies as a positive model: diversifying identity sources before a '
            'crisis is the strongest protection against purpose collapse',
            'The Okinawan Blue Zone: residents maintain ikigai into their 90s by '
            'continuously evolving their role from worker to elder to teacher to '
            'community elder — the role changes, the contribution continues. '
            'Applies to retirement: purpose does not end, it transforms',
            'Retirement transition research (Wang, 2007): 40% of retirees experience '
            'psychological disenchantment; those with multiple identity sources recover '
            'significantly faster. Applies directly to any user approaching or in retirement',
        ],
        interpretations=[
            Interpretation(
                school='Vedantic',
                culture='Eastern',
                stance='The Bhagavad Gita teaches that the self (Atman) is not '
                       'identical with any role, body, or social function — '
                       'these are the field (kshetra), not the knower of the field. '
                       'The crisis of role-loss is an invitation to discover '
                       'the self that exists independently of all roles. '
                       'Dharma — one\'s deepest nature — does not retire.',
                advice='Ask: "Who am I without this role?" Sit with the discomfort '
                       'of the question. Then ask: "What would I do if there were '
                       'no audience, no title, no expectation?" The answer is '
                       'closer to your dharma than any role ever was.',
                evidence='Bhagavad Gita, Chapter 2: Arjuna\'s crisis and Krishna\'s '
                         'instruction on the eternal self. Chapter 3: nishkama karma — '
                         'action as duty, not for result.',
                conditions='Best when person has spiritual inclination or is '
                           'asking existential questions; identity crisis is philosophical'
            ),
            Interpretation(
                school='Ikigai / Bushido',
                culture='Eastern',
                stance='Japanese ikigai (reason for being) holds that purpose '
                       'lives at the intersection of what you love, what you are '
                       'good at, what the world needs, and what you can be paid for. '
                       'Bushido extends this: the warrior who loses his lord does '
                       'not lose his craft — skill and discipline are portable '
                       'across all roles. The purpose is in the doing, not the title.',
                advice='Map your ikigai: What do you love doing regardless of reward? '
                       'What are you genuinely skilled at? Where do these overlap '
                       'with what others need? The intersection is available '
                       'in any life stage — retirement does not close it.',
                evidence='Mieko Kamiya, Ikigai-ni-tsuite (1966): ikigai as a '
                         'psychological concept of life worth. Héctor García & '
                         'Francesc Miralles, Ikigai (2016): Okinawan centenarians '
                         'attribute longevity to maintaining ikigai through old age.',
                conditions='Best for practical, activity-oriented people; '
                           'person needs a concrete framework for purpose, not philosophy'
            ),
            Interpretation(
                school='Existentialist / Logotherapy',
                culture='Western',
                stance='Frankl\'s logotherapy: meaning cannot be given — it must '
                       'be found. The loss of a role removes a previous source of '
                       'meaning but cannot destroy the will to meaning (Wille zum Sinn). '
                       'Every life stage contains unique possibilities for meaning '
                       'that earlier stages did not. The question is not '
                       '"how do I get my old meaning back?" but '
                       '"what meaning is available here that was not available before?"',
                advice='Write a "meaning audit" for your current life stage: '
                       'What experiences are available now that were not before? '
                       'Who can you serve now? What can you create, give, or '
                       'witness? Frankl: meaning can be found in three ways — '
                       'creation, experience, or chosen attitude toward suffering.',
                evidence='Frankl, Man\'s Search for Meaning (1946). '
                         'Meta-analysis (Steger et al., 2009): presence of meaning '
                         'is the strongest predictor of wellbeing across all age groups.',
                conditions='Best when person is philosophically oriented and '
                           'asking "what is the point?" questions'
            ),
        ],
        resolution_hint=(
            'Existential/philosophical identity crisis → Vedantic Atman beyond roles. '
            'Practical person needing concrete purpose framework → Ikigai mapping. '
            '"What is the point?" questions → Existentialist/Logotherapy meaning audit. '
            'Retirement + loss of professional identity → Ikigai first (concrete), '
            'then Vedantic (deeper) if person is receptive.'
        ),
        keywords=['retired', 'no purpose', 'what\'s the point', 'who am i now',
                  'identity', 'role ended', 'empty nest', 'nothing to do', 'redundant',
                  'lost my job', 'career over', 'no longer needed', 'what now',
                  'reason to get up', 'don\'t know who i am anymore'],
        urgency_when_detected='high'
    ),

    WisdomLesson(
        id='individual_vs_community',
        title='The Myth of Self-Sufficiency — Refusing Help and Community',
        mistake_type='isolation',
        domains=['relationships', 'mental_health', 'health', 'career'],
        universal_pattern=(
            'The belief that one should be able to handle all difficulties alone — '
            'that asking for help is weakness, that self-sufficiency is virtue. '
            'This pattern is culturally reinforced in many modern Western contexts '
            'but contradicts the evidence from every long-lived culture: humans '
            'are a deeply social species, and the refusal of community is one of '
            'the strongest predictors of poor health and reduced lifespan.'
        ),
        historical_examples=[
            'Ubuntu philosophy (Southern Africa): "Umuntu ngumuntu ngabantu" — '
            '"A person is a person through other persons." Individual identity '
            'was never separable from communal belonging across Bantu civilisations. '
            'Applies to anyone raised in an individualist culture who is struggling '
            'alone with what communal support could address',
            'Okinawa Blue Zone: the moai (lifelong social support group of 5) is '
            'the single most consistent feature of Okinawan centenarians\' lives. '
            'They never faced difficulty alone (Eastern). Applies to health, '
            'retirement, and bereavement — the moai provides support precisely '
            'when self-sufficiency is most likely to be invoked',
            'Nelson Mandela\'s Truth and Reconciliation Commission (South Africa, 1996): '
            'built entirely on Ubuntu philosophy — healing national trauma required '
            'communal acknowledgment, not individual resolution. The commission '
            'explicitly rejected the Western legal model of individual culpability '
            'in favour of communal restoration. Applies to interpersonal conflicts '
            'where individual resolution has failed',
            'Abraham Lincoln deliberately built a "team of rivals" — inviting '
            'his political opponents (Seward, Chase, Bates) into his cabinet. '
            'His greatest decisions were made through structured community '
            'challenge, not solitary deliberation. Applies to anyone facing a '
            'major decision who is refusing consultation because of self-sufficiency',
            'The frontier mythology of the American West created the self-sufficient '
            'individual archetype — yet frontier communities survived through '
            'cooperative barn-raising, shared harvests, and collective defence, not isolation. '
            'The myth and the history are opposite. Applies to any user whose '
            'self-sufficiency belief is culturally inherited, not evidence-based',
            'Holt-Lunstad et al. (2015): social integration is a stronger predictor '
            'of survival than exercise, diet, or abstaining from alcohol. '
            'Applies to any user who prioritises physical health interventions '
            'while simultaneously refusing social connection',
        ],
        interpretations=[
            Interpretation(
                school='Ubuntu',
                culture='Universal',
                stance='"I am because we are." Ubuntu holds that the individual '
                       'self is constituted through relationship — there is no '
                       'meaningful "I" that exists independently of "we." '
                       'Accepting help is not weakness; it is an act that '
                       'strengthens the community by allowing others to '
                       'exercise their humanity through giving.',
                advice='Identify one need you are currently carrying alone. '
                       'Tell one person about it — not to solve it, but to '
                       'share it. Ubuntu holds that the act of sharing a burden '
                       'changes its weight before anything else changes.',
                evidence='Desmond Tutu, No Future Without Forgiveness (1999): '
                         'Ubuntu as the philosophical foundation of the Truth '
                         'and Reconciliation Commission. Archbishop Tutu: '
                         '"My humanity is bound up in yours."',
                conditions='Best when self-sufficiency is cultural or masculine-identity-driven; '
                           'person has others around them but refuses to ask'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The five relationships (wulun) are not optional — they '
                       'are the structure within which virtue is possible. '
                       'Ren (benevolence) requires giving and receiving. '
                       'A person who refuses all help deprives others of the '
                       'opportunity to exercise ren — the refusal is therefore '
                       'not just a personal failing but a communal one.',
                advice='Map which of your five relationships are currently one-directional '
                       '(you give, never receive). Choose one and allow yourself '
                       'to receive help in a specific, small way this week. '
                       'Receiving is as much a relational duty as giving.',
                evidence='Analects 12:1: "To master oneself and return to ritual '
                         'propriety is ren." Propriety includes the proper '
                         'reciprocity of giving and receiving.',
                conditions='Best when person has a strong duty/responsibility orientation '
                           'and giving is easy but receiving feels wrong'
            ),
            Interpretation(
                school='Positive Psychology',
                culture='Western',
                stance='Seligman\'s PERMA model identifies relationships (R) as '
                       'one of five pillars of wellbeing — not a nice-to-have '
                       'but constitutive of flourishing. Dunn et al. (2008) '
                       'demonstrated that prosocial spending (spending on others) '
                       'produces more wellbeing than personal spending — '
                       'reciprocal connection benefits both giver and receiver.',
                advice='Identify one person who has offered help you have declined. '
                       'Accept it. Track your wellbeing before and after. '
                       'The evidence consistently shows that connection, not '
                       'self-sufficiency, is the fastest route to flourishing.',
                evidence='Seligman, Flourish (2011). Holt-Lunstad et al. (2015): '
                         'social integration as mortality predictor. '
                         'Cacioppo, Loneliness (2008).',
                conditions='Best when person is data-responsive and the block '
                           'is a belief about self-sufficiency rather than shame'
            ),
        ],
        resolution_hint=(
            'Cultural/masculine self-sufficiency → Ubuntu communal identity. '
            'Strong duty orientation, giver who won\'t receive → Confucian reciprocity. '
            'Data-responsive, believes in self-improvement → Positive Psychology PERMA. '
            'Combination of all three: frame receiving as strength, duty, and evidence-based wellbeing.'
        ),
        keywords=['on my own', 'don\'t need help', 'can handle it myself', 'not a burden',
                  'don\'t want to bother', 'self-sufficient', 'independent', 'private',
                  'won\'t ask for help', 'figure it out alone', 'strong enough',
                  'don\'t want to rely on'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='unexamined_assumptions',
        title='Living by Unexamined Assumptions',
        mistake_type='overconfidence',
        domains=['career', 'relationships', 'mental_health', 'health'],
        universal_pattern=(
            'The beliefs that govern most human decisions were formed in childhood '
            'and adolescence — under conditions of incomplete information, '
            'limited experience, and high social pressure. These assumptions '
            'are rarely examined in adult life. They operate invisibly, '
            'shaping choices while being mistaken for objective reality. '
            'The examined life — Socrates\' central concern — remains the '
            'exception across all cultures and all periods of recorded history.'
        ),
        historical_examples=[
            'Socrates\' trial and death (399 BC): executed for questioning unexamined '
            'Athenian assumptions about piety and justice. His defence: "The unexamined '
            'life is not worth living." Applies to anyone who has not examined '
            'a belief that is causing repeated problems — the discomfort of questioning '
            'is smaller than the cost of not questioning',
            'Empress Dowager Cixi (China, 1835–1908): governed for 47 years on the '
            'unexamined assumption that the Confucian imperial system was permanent '
            'and superior. Every reform that might have saved the dynasty was blocked '
            'by this assumption. China\'s century of humiliation followed. Applies '
            'to anyone whose resistance to change is really an unexamined assumption '
            'that the old way is inherently right',
            'Woodrow Wilson\'s failure to ratify the League of Nations (1919–1920): '
            'Wilson operated on the unexamined assumption that the moral rightness '
            'of his cause would overcome political opposition — he never examined '
            'whether this assumption was true. The League failed; WWII followed. '
            'Applies to anyone in a conflict or negotiation who has not examined '
            'their assumptions about how the other party will respond',
            'The Indian concept of maya: the phenomenal world mistaken for ultimate '
            'reality; viveka (discernment) is the practice of distinguishing real '
            'from projected (Eastern). Applies to anyone whose suffering arises from '
            'treating assumptions about themselves or others as objective fact',
            'Cognitive science (Nisbett & Wilson, 1977): humans confabulate — we invent '
            'post-hoc explanations for decisions driven by processes we cannot access. '
            'Applies to any user who is certain they know why they do what they do, '
            'especially in repeated patterns',
            'Bourdieu\'s habitus: social assumptions absorbed in childhood operate as '
            '"the way things are" — not experienced as assumptions but as reality. '
            'Applies to cultural, family, and class-based assumptions about '
            'what is possible, appropriate, or deserved',
        ],
        interpretations=[
            Interpretation(
                school='Socratic',
                culture='Western',
                stance='The Socratic method: every significant belief must be able '
                       'to withstand questioning. Not to destroy all beliefs, '
                       'but to ensure that what remains is genuinely held rather '
                       'than inherited. Socrates considered himself a midwife — '
                       'helping others give birth to what they actually believed, '
                       'rather than what they had been told to believe.',
                advice='Choose one strong belief that governs an important area '
                       'of your life. Ask: "How do I know this is true? '
                       'What would have to be false for this belief to be wrong? '
                       'Have I tested this, or inherited it?" Write the answers.',
                evidence='Plato, Apology: "The unexamined life is not worth living." '
                         'Meno: the method of hypothesis and examination. '
                         'Socratic questioning is the foundation of all modern '
                         'critical thinking and therapeutic inquiry.',
                conditions='Best when person is intellectually engaged and '
                           'assumptions are producing visible recurring problems'
            ),
            Interpretation(
                school='Vedantic',
                culture='Eastern',
                stance='Viveka (discernment between real and unreal) is the '
                       'first of the four qualifications for Vedantic practice. '
                       'The assumptions we mistake for reality are maya — '
                       'not hallucinations, but projections. The practice is '
                       'neti neti (not this, not this) — systematically '
                       'questioning what we have taken for granted until '
                       'what remains cannot be questioned.',
                advice='Take one assumption you hold about yourself or your situation. '
                       'Apply neti neti: "Is this truly me, or is it a role, '
                       'a habit, a story?" Remove each layer until what remains '
                       'cannot be removed. What is left is closer to the real.',
                evidence='Adi Shankaracharya, Vivekachudamani (~8th century AD): '
                         'the primary text on discernment and the examination '
                         'of assumed reality. Upanishads: Mandukya Upanishad '
                         'on the layers of self (koshas).',
                conditions='Best when person is spiritually oriented or '
                           'questions about identity and reality are already arising'
            ),
            Interpretation(
                school='Psychoanalytic',
                culture='Western',
                stance='Freud\'s core insight: most of what drives us is '
                       'unconscious. The assumptions formed in early life '
                       'operate as unconscious schemata — they are not '
                       'experienced as beliefs but as reality. Making them '
                       'conscious (the work of analysis) does not automatically '
                       'change behaviour, but it makes change possible.',
                advice='Track one recurring frustration or conflict pattern. '
                       'Ask: "When did I first feel this? Who else was '
                       'present?" The assumption driving current behaviour '
                       'often has a precise origin that, once named, '
                       'loses some of its automatic power.',
                evidence='Freud, The Interpretation of Dreams (1900); '
                         'Beyond the Pleasure Principle (1920). '
                         'Schema therapy (Young, 2003): early maladaptive '
                         'schemas persist into adulthood as unexamined assumptions.',
                conditions='Best when person has recurring patterns they '
                           'cannot explain rationally; emotional charge is high'
            ),
        ],
        resolution_hint=(
            'Intellectually curious, assumptions producing visible problems → Socratic questioning. '
            'Spiritual orientation, identity questions → Vedantic viveka/neti neti. '
            'Recurring emotional patterns with no rational explanation → Psychoanalytic origin tracking. '
            'Use Socratic as entry point for most people; go deeper with Vedantic or Psychoanalytic '
            'based on the person\'s orientation.'
        ),
        keywords=['always thought', 'the way it is', 'never questioned', 'always been like this',
                  'just assumed', 'supposed to', 'natural', 'obvious', 'everyone knows',
                  'always knew', 'that\'s just how i am', 'been told', 'grew up believing'],
        urgency_when_detected='low'
    ),

    WisdomLesson(
        id='body_mind_disconnection',
        title='Treating the Body as Separate from Mind and Purpose',
        mistake_type='body_neglect',
        domains=['health', 'mental_health', 'career', 'retirement'],
        universal_pattern=(
            'The Cartesian split between mind and body — "I think, therefore I am" — '
            'has produced a cultural assumption in the West that the body is a '
            'vehicle for the mind, to be maintained when convenient and ignored when '
            'inconvenient. Every Eastern tradition, and now modern neuroscience, '
            'rejects this model. Physical neglect directly impairs cognitive function, '
            'emotional regulation, and decision quality — which in turn worsen '
            'physical health in a downward spiral.'
        ),
        historical_examples=[
            'Japanese concept of Hara (the vital centre): traditional Japanese '
            'medicine and martial arts locate health in the hara (lower abdomen), '
            'rejecting the Western head-centred model. Okinawan elders maintain '
            'physical movement as inseparable from mental purpose (Eastern). '
            'Applies to sedentary workers and retirees who have disconnected '
            'physical activity from meaning',
            'Descartes\' Cogito (1637) institutionalised mind-body dualism — '
            'with consequences still visible today: medicine treating body and mind '
            'separately, workplaces treating physical signals as interruptions, '
            'individuals valuing only cognitive output. Applies to anyone '
            'who treats their body as a vehicle for their mind',
            'Emperor Qin Shi Huang\'s obsession with immortality elixirs (210 BC) '
            'and Emperor Jiajing of Ming (1521–1567) who took mercury-based '
            'immortality pills for decades — both rulers who pursued a fantasy '
            'of bodily control while ignoring the body\'s actual signals. '
            'Applies to any user pursuing health solutions that bypass '
            'genuine body-listening in favour of an external formula',
            'The Stoic soldier-philosopher Marcus Aurelius: maintained physical '
            'training, sleep, and dietary discipline throughout his reign, '
            'documenting in the Meditations how physical neglect impaired '
            'philosophical clarity. He explicitly connected body state to '
            'mental state. Applies to intellectually high-functioning people '
            'who dismiss physical maintenance as secondary',
            'van der Kolk, The Body Keeps the Score (2014): trauma is stored '
            'somatically; talk therapy alone cannot resolve it. This finding '
            'reversed decades of purely cognitive therapeutic approaches. '
            'Applies to anyone whose chronic physical symptoms resist '
            'explanation but correlate with stress, loss, or past trauma',
            'Damasio, Descartes\' Error (1994): patients with damaged emotion centres '
            'could not make rational decisions — body and emotion are constitutive '
            'of reason, not obstacles to it. Applies to analytical users who '
            'believe ignoring their body improves their thinking',
        ],
        interpretations=[
            Interpretation(
                school='Ikigai / Bushido',
                culture='Eastern',
                stance='The body is not a vehicle — it is an expression of purpose. '
                       'Bushido held that the warrior\'s physical discipline was '
                       'inseparable from moral and mental development. '
                       'Ikigai research shows that physical movement — '
                       'specifically purposeful movement — is one of the '
                       'strongest predictors of healthy longevity.',
                advice='Identify one physical practice that is both purposeful '
                       'and pleasurable — not punishing exercise but movement '
                       'that connects body to something meaningful '
                       '(walking to a destination, gardening, tai chi, craft). '
                       'Do it daily for two weeks and track mental clarity.',
                evidence='Héctor García & Francesc Miralles, Ikigai (2016): '
                         'Okinawan centenarians have a daily physical practice '
                         'tied to purpose. Bushido: Yamamoto Tsunetomo, '
                         'Hagakure (~1709): "The way of the samurai is found '
                         'in death" — meaning: total presence in each action.',
                conditions='Best for retirement or sedentary work context; '
                           'person values purpose over health rules'
            ),
            Interpretation(
                school='Traditional Chinese Medicine / Eastern Holism',
                culture='Eastern',
                stance='Qi (vital energy) flows through the body according to '
                       'natural rhythms — sleep, season, emotion, food, movement. '
                       'Disease is the disruption of natural flow. '
                       'Treatment is restoring flow, not suppressing symptoms. '
                       'The mind that ignores the body\'s signals is blocking '
                       'its own qi.',
                advice='For one week: track the three body signals you most '
                       'consistently ignore (fatigue, hunger, tension). '
                       'Each time you notice one, respond within 30 minutes '
                       'rather than suppressing it. TCM holds that responding '
                       'to signals early prevents disease; ignoring them '
                       'causes it.',
                evidence='Huangdi Neijing (Yellow Emperor\'s Classic, ~200 BC): '
                         'the foundational TCM text. Modern validation: '
                         'Steptoe & Kivimäki (2013) Nature Reviews: '
                         'stress-body-disease pathways confirmed in large cohort studies.',
                conditions='Best when person has chronic physical symptoms '
                           'they are attributing entirely to psychological or work causes'
            ),
            Interpretation(
                school='Modern Psychology / Embodied Cognition',
                culture='Western',
                stance='Cognition is embodied — thinking does not happen in '
                       'a brain disconnected from a body. Damasio\'s somatic '
                       'marker hypothesis shows that body states (emotions, '
                       'physical sensations) are prerequisite to rational '
                       'decision-making. Neglecting the body literally '
                       'impairs judgment, not just health.',
                advice='Before any important decision or difficult conversation: '
                       'take 5 minutes to notice your body state. '
                       'Are you hungry, tired, in pain, tense? '
                       'Address the physical state first. '
                       'Research shows this improves decision quality '
                       'more than any cognitive strategy alone.',
                evidence='Damasio, Descartes\' Error (1994). '
                         'van der Kolk, The Body Keeps the Score (2014). '
                         'Embodied cognition research: Niedenthal et al. (2005).',
                conditions='Best for analytical, mind-oriented people who '
                           'intellectually dismiss physical signals'
            ),
        ],
        resolution_hint=(
            'Purpose/retirement context → Ikigai purposeful movement. '
            'Chronic symptoms attributed to stress → TCM signal-response practice. '
            'Analytical, mind-first person → Embodied Cognition (decision quality framing). '
            'Trauma history present → flag HIGH urgency; refer to somatic therapy alongside any KB approach.'
        ),
        keywords=['ignore my body', 'push through pain', 'mind over matter', 'tired but',
                  'no time to rest', 'symptoms', 'aches', 'body signals', 'exercise',
                  'sedentary', 'sit all day', 'not sleeping', 'stress symptoms',
                  'body is just a tool'],
        urgency_when_detected='medium'
    ),

]


# ─────────────────────────────────────────────────────
# PHASE 3 LESSONS — deepening psychology coverage
# New schools: Jungian, Attachment Theory, ACT, Somatic/Trauma-informed
# ─────────────────────────────────────────────────────

WISDOM_LESSONS += [

    WisdomLesson(
        id='shadow_projection',
        title='Blaming Others for What We Deny in Ourselves',
        mistake_type='blame_externalising',
        domains=['relationships', 'mental_health', 'career'],
        universal_pattern=(
            'The qualities we most strongly disown in ourselves are those we most '
            'loudly condemn in others. This is not hypocrisy in the ordinary sense — '
            'it is a structural feature of how the psyche manages the tension between '
            'the self we consciously identify with and the full range of human '
            'potential we carry. Across cultures and millennia, the failure to '
            'examine the shadow — what we project outward — is identified as '
            'a root cause of conflict, moral rigidity, and relational breakdown.'
        ),
        historical_examples=[
            'The Spanish Inquisition: officials who condemned heresy most passionately '
            'often secretly held the doubts they were punishing — Jung\'s shadow at '
            'institutional scale (Western). Applies to anyone whose condemnation of '
            'others is disproportionately intense',
            'The Chinese Cultural Revolution (1966–76): those who denounced others '
            'for "capitalist" tendencies most ferociously were frequently motivated '
            'by envy of precisely those qualities. Shadow projection drove a '
            'civilisational catastrophe (Eastern). Applies to workplace or '
            'family dynamics where condemnation is really disguised desire',
            'Henry VIII: condemned each wife\'s failings with moral certainty while '
            'enacting the same pattern himself repeatedly — the shadow of his own '
            'inconstancy projected outward. Applies to anyone who repeatedly judges '
            'others for the same trait they embody',
            'Senator Joseph McCarthy (USA, 1950–1954): the anti-Communist crusade '
            'that destroyed hundreds of careers was later revealed to involve McCarthy\'s '
            'own deep insecurities about loyalty, status, and identity — '
            'shadow projection turned into institutional persecution. Applies to '
            'anyone whose blaming has become systematic or crusading',
            'Gandhi: explicitly practised what he called "experiments with truth" — '
            'examining his own capacity for the vices he saw in the British Empire. '
            'His autobiography documents his shadow work as inseparable from '
            'his moral leadership. Applies as a positive model: great leaders '
            'examine their shadows; they do not project them',
            'Bushman & Baumeister (1998): threatened egotism — high self-esteem '
            'combined with ego threat — predicts aggression toward others more '
            'strongly than low self-esteem. Applies to high-achievers whose '
            'blaming intensifies when their self-image is challenged',
        ],
        interpretations=[
            Interpretation(
                school='Jungian',
                culture='Western',
                stance='The shadow is not the enemy — it is the unintegrated '
                       'potential of the full self. Jung: "Until you make the '
                       'unconscious conscious, it will direct your life and '
                       'you will call it fate." The work is not eliminating '
                       'the shadow but integrating it — owning the full range '
                       'of what one is capable of, including the uncomfortable parts.',
                advice='Identify the trait you most judge in someone close to you. '
                       'Ask honestly: "In what circumstances could I do this? '
                       'When have I already done something similar?" '
                       'The discomfort of the question is the shadow moving '
                       'from projection back toward integration.',
                evidence='Jung, Aion (1951): the shadow as the dark side of '
                         'the personality. Two Essays on Analytical Psychology (1928). '
                         'Modern research: Bushman & Baumeister (1998): '
                         'threatened egotism predicts aggression toward others.',
                conditions='Best when person has a strong moral framework and '
                           'blame patterns are intense or self-righteous'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='The Buddhist concept of mudita (sympathetic joy) and '
                       'karuna (compassion) are specifically designed to dissolve '
                       'the separation between self and other that makes projection '
                       'possible. When we fully recognise our own capacity for '
                       'the same faults, blame loses its foothold.',
                advice='When blaming another, practise tonglen: breathe in their '
                       'suffering and the suffering of all who share this fault — '
                       'including yourself. Breathe out relief and compassion '
                       'for all. The practice dissolves the boundary that '
                       'makes their fault feel separate from yours.',
                evidence='Pema Chödrön, When Things Fall Apart (1997): tonglen '
                         'as shadow integration practice. Shantideva, '
                         'Bodhicaryavatara (~8th century): equanimity toward '
                         'self and other as the foundation of compassion.',
                conditions='Best when person is spiritually oriented or '
                           'open to contemplative practice'
            ),
            Interpretation(
                school='Existentialist',
                culture='Western',
                stance='Sartre: bad faith (mauvaise foi) is the refusal to '
                       'acknowledge one\'s own freedom and responsibility. '
                       'Blaming others is a primary form of bad faith — '
                       'it denies that I am always choosing, always capable '
                       'of the same acts I condemn. Authentic existence '
                       'requires owning the full weight of one\'s freedom.',
                advice='For each person or situation you blame: write '
                       '"I am responsible for..." and complete the sentence '
                       'with something real. Not to deny genuine wrongs done '
                       'by others, but to locate the part you own. '
                       'Authenticity begins where blame ends.',
                evidence='Sartre, Being and Nothingness (1943): bad faith. '
                         'Frankl: even in the worst circumstances, the last '
                         'freedom is the choice of one\'s attitude.',
                conditions='Best when blame is accompanied by a sense of '
                           'complete victimhood and no personal agency'
            ),
        ],
        resolution_hint=(
            'Strong moral condemnation of others, self-righteous pattern → Jungian shadow integration. '
            'Spiritually oriented, open to contemplative practice → Buddhist tonglen. '
            'Complete victimhood narrative, no sense of agency → Existentialist bad faith. '
            'Pattern of blaming specific person (partner, parent, employer) repeatedly → '
            'Jungian first (most specific to repetitive projection).'
        ),
        keywords=['their fault', 'blame them', 'they always', 'can\'t stand people who',
                  'everyone else is the problem', 'hypocrites', 'judge', 'condemn',
                  'what they did to me', 'if it weren\'t for', 'caused by',
                  'responsible for my', 'makes me'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='attachment_pattern_repetition',
        title='Repeating Relational Patterns from Early Attachment',
        mistake_type='repetition',
        domains=['relationships', 'mental_health', 'health'],
        universal_pattern=(
            'The attachment patterns formed in the first two years of life — '
            'secure, anxious, avoidant, or disorganised — become the template '
            'for all subsequent significant relationships. They are not '
            'consciously chosen; they operate below awareness as automatic '
            'expectations about whether others can be trusted, whether the self '
            'is worthy of love, and how to behave when a relationship feels threatened. '
            'Without examination, these patterns replay regardless of '
            'how unsuitable the current relationship is for them.'
        ),
        historical_examples=[
            'Bowlby developed attachment theory from work with delinquent children '
            'in London (1944) and children separated from parents in WWII hospitals — '
            'the first systematic proof that early relational patterns determine '
            'lifelong outcomes (Western). Applies to any user whose relationship '
            'difficulties show a clear generational or childhood pattern',
            'The Japanese concept of amae (dependence, Doi 1971): a culturally '
            'sanctioned relational dynamic functioning as a secure attachment substitute; '
            'its disruption produces identical anxiety to Western insecure attachment. '
            'Applies cross-culturally: the need for safe dependence is universal, '
            'though the form differs by culture',
            'Eleanor Roosevelt\'s early life: mother died when she was 8, father '
            'died at 10, raised by a cold grandmother — her avoidant attachment '
            'pattern led to deep loneliness in her marriage to FDR and a lifelong '
            'pattern of emotional withdrawal when threatened. Yet she became one of '
            'the most impactful public servants of the 20th century by converting '
            'her attachment wounds into empathy for the marginalised. Applies as a '
            'positive model: attachment patterns can be redirected, not just survived',
            'Sigmund Freud\'s own attachment: complicated early attachment to his '
            'mother and father produced the very patterns he spent his career '
            'describing in others — his transference theory was partly autobiography. '
            'Applies to anyone: even the theorist of unconscious patterns was not '
            'immune to them',
            'The multigenerational transmission of trauma in post-Holocaust families: '
            'children of survivors showed measurably higher anxiety and avoidant '
            'attachment even without direct trauma exposure (Danieli, 1998). '
            'Applies when relationship patterns seem inexplicable given the '
            'user\'s own direct experience',
            'Hazan & Shaver (1987): romantic love follows attachment theory exactly — '
            'secure, anxious, and avoidant styles map onto Ainsworth\'s infant '
            'classifications. Applies directly: the way a person describes their '
            'current relationship difficulties usually maps to an early pattern',
        ],
        interpretations=[
            Interpretation(
                school='Attachment Theory',
                culture='Western',
                stance='Adult attachment patterns are working models — internal '
                       'representations of self and other that were adaptive '
                       'in the original relationship but may be maladaptive now. '
                       'They can be updated through "earned security" — '
                       'a new relationship experience (therapeutic or otherwise) '
                       'that consistently disconfirms the old model.',
                advice='Identify your predominant attachment pattern in close '
                       'relationships: Do you pursue when threatened (anxious)? '
                       'Withdraw (avoidant)? Oscillate (disorganised)? '
                       'Name one specific moment this week when you acted '
                       'from the old pattern. What would earned security '
                       'look like instead?',
                evidence='Bowlby, Attachment and Loss (1969–1980). '
                         'Ainsworth et al., Patterns of Attachment (1978). '
                         'Wallin, Attachment in Psychotherapy (2007): '
                         'earned security is achievable at any age.',
                conditions='Best when relational patterns are clearly repetitive '
                           'across multiple relationships'
            ),
            Interpretation(
                school='Psychoanalytic',
                culture='Western',
                stance='Transference — the unconscious redirection of feelings '
                       'from a past relationship onto a present one — is the '
                       'psychoanalytic mechanism underlying relational repetition. '
                       'The patient does not know they are relating to the past; '
                       'they experience the present relationship as simply '
                       '"how things are." Making the transference conscious '
                       'is the primary work of relational change.',
                advice='When you feel a strong, disproportionate emotional reaction '
                       'in a relationship (more than the situation warrants), ask: '
                       '"Who does this remind me of?" '
                       'Write about the earlier relationship. '
                       'The present intensity is often past pain in disguise.',
                evidence='Freud, The Dynamics of Transference (1912). '
                         'Object relations theory: Winnicott, Klein, Fairbairn. '
                         'Meta-analysis (Diener et al., 2007): insight into '
                         'relational patterns reduces repetitive relationship problems.',
                conditions='Best when emotional reactions are intense and '
                           'person has capacity for self-reflection'
            ),
            Interpretation(
                school='Confucian',
                culture='Eastern',
                stance='The five relationships provide the normative structure '
                       'within which relational patterns are formed and reformed. '
                       'Confucian self-cultivation (xiushen) includes '
                       'examining one\'s conduct in each relationship daily — '
                       'Zengzi: "I daily examine myself on three points: '
                       'whether I am faithful to others, sincere with friends, '
                       'and have mastered and practised my teacher\'s instructions."',
                advice='For each significant relationship currently causing difficulty: '
                       'write one specific way you are not meeting the '
                       'Confucian standard for that relationship type. '
                       'Then write one specific action this week to move toward it. '
                       'The external conduct reshapes the internal pattern over time.',
                evidence='Analects 1:4 — Zengzi\'s daily self-examination. '
                         'The Confucian view: behaviour changes feeling; '
                         'ritual creates the emotion it expresses.',
                conditions='Best when person has strong family/duty values '
                           'and relational patterns are in family relationships'
            ),
        ],
        resolution_hint=(
            'Clear pattern across multiple relationships → Attachment Theory working models. '
            'Intense, disproportionate emotional reactions → Psychoanalytic transference. '
            'Family relationship patterns, duty-oriented person → Confucian daily examination. '
            'Combination of childhood trauma + adult relationship problems → HIGH urgency; '
            'Attachment Theory + recommend therapy.'
        ),
        keywords=['same pattern again', 'always end up with', 'relationships never work',
                  'push people away', 'clingy', 'abandoned', 'trust issues',
                  'same type of person', 'drawn to', 'repeat the same mistake',
                  'feel rejected', 'fear of abandonment', 'too needy', 'shut down'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='rigid_rules_inflexibility',
        title='Rigid Rules That Block Effective Living',
        mistake_type='identity_rigidity',
        domains=['mental_health', 'career', 'relationships', 'health'],
        universal_pattern=(
            'The beliefs and rules that once protected us — "never show weakness," '
            '"always be in control," "only my way is right" — become cages. '
            'Psychological inflexibility: the inability to adapt behaviour based '
            'on what a situation actually requires, in service of what genuinely '
            'matters. Across all cultures, wisdom traditions identify rigidity '
            'as a primary cause of suffering — not because standards are wrong '
            'but because the inability to hold them lightly prevents '
            'both effective action and genuine peace.'
        ),
        historical_examples=[
            'The Roman Senate\'s rigid adherence to Republican procedure while '
            'Caesar marched on Rome (49 BC): procedural rigidity prevented '
            'adaptive response to a new reality. Applies to anyone whose '
            'rules prevent them from responding to what is actually happening',
            'The Chinese concept of bian (change/adaptation): the I Ching '
            '(Book of Changes, ~1000 BC) is the oldest continuously used wisdom '
            'text because it is entirely about adaptive response — not rigid '
            'rules but situational wisdom (Eastern). Applies to anyone who '
            'believes their rigid approach is a strength, not a vulnerability',
            'Emperor Nicholas II of Russia: rigidly governed by the rule that '
            'an autocrat must never concede — when concessions might have saved '
            'the dynasty in 1905 and 1917, his rigidity made revolution inevitable. '
            'Applies to anyone in a relationship or leadership role where '
            'inflexibility is accelerating the very outcome they fear',
            'Miyamoto Musashi (1584–1645), Japan\'s greatest swordsman: his Book '
            'of Five Rings explicitly teaches that the warrior who follows a fixed '
            'style will be defeated by an opponent who adapts. Musashi himself '
            'changed his approach completely three times in his life. Applies to '
            'anyone whose rigid rules worked in one context but are failing in a new one',
            'Charles Darwin: explicitly described his scientific method as '
            'holding every hypothesis lightly — he kept a dedicated notebook for '
            'evidence against his own theories because he knew his mind would '
            'naturally filter it out. Applies to intellectual rigidity: '
            'the scientist who cannot be proven wrong cannot discover anything new',
            'Hayes et al., ACT (2004): psychological inflexibility — rigid rule-following '
            'at the cost of valued action — is the transdiagnostic core of most '
            'psychological suffering. Applies across all domains: health rules, '
            'relationship rules, career rules that have become cages',
        ],
        interpretations=[
            Interpretation(
                school='ACT',
                culture='Western',
                stance='Acceptance and Commitment Therapy identifies psychological '
                       'flexibility as the core of mental health: the ability to '
                       'contact the present moment fully and change or persist in '
                       'behaviour when doing so serves one\'s values. '
                       'Rigid rules block flexible action. The antidote is not '
                       'abandoning values but holding rules lightly — '
                       '"What matters here?" rather than "What is the rule here?"',
                advice='Identify one rigid rule currently causing you problems '
                       '("I must always...", "I can never..."). '
                       'Ask: "Does following this rule serve what I genuinely value? '
                       'What would I do if I held the rule lightly instead of tightly?" '
                       'Try the lighter version once and notice the result.',
                evidence='Hayes, Strosahl & Wilson, Acceptance and Commitment '
                         'Therapy (2004). Meta-analysis (A-Tjak et al., 2015): '
                         'ACT effective across 60+ conditions; psychological '
                         'flexibility mediates all outcomes.',
                conditions='Best when person describes rigid "must" or "never" rules; '
                           'rule-following is causing visible harm to valued relationships or goals'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='Rigidity is attachment (upadana) to a fixed view (ditthi). '
                       'The Buddha specifically listed "clinging to rules and rituals" '
                       '(silabbata-paramasa) as the third fetter — one of the first '
                       'to be released on the path. Fixed views are not wrong because '
                       'they are views; they are wrong because they are held '
                       'as permanently, unconditionally true.',
                advice='For any rule you are holding rigidly: ask '
                       '"Is this always true in every circumstance?" '
                       'Find one genuine exception. The rule is not destroyed — '
                       'it becomes a guideline rather than a law. '
                       'Guidelines serve you; laws rule you.',
                evidence='Majjhima Nikaya 22: the parable of the raft — '
                         'even the Dhamma (teaching) is a raft to cross the river, '
                         'not something to carry on your back after crossing. '
                         'No teaching, no rule, is to be clung to.',
                conditions='Best when rigidity is expressed as moral certainty '
                           'or spiritual rules; person is open to contemplative inquiry'
            ),
            Interpretation(
                school='Narrative Psychology',
                culture='Western',
                stance='Rigid rules are plot devices in a dominant story — '
                       '"I am someone who never asks for help," '
                       '"I am someone who always finishes what they start." '
                       'White & Epston\'s narrative therapy externalises the rule: '
                       'the rule is not you; it is a story that has been governing you. '
                       'Authorship can be reclaimed.',
                advice='Write the rule as a story: "There is a character who believes '
                       'they must always... This character developed this rule when... '
                       'The rule served them then because... '
                       'The rule costs them now because..." '
                       'Seeing it as a story makes it possible to revise.',
                evidence='White & Epston, Narrative Means to Therapeutic Ends (1990). '
                         'McAdams, The Stories We Live By (1993): identity is '
                         'narrative; revising the story revises the self.',
                conditions='Best when person is language/story-oriented '
                           'and rules are strongly tied to identity'
            ),
        ],
        resolution_hint=(
            '"Must" / "never" rules causing visible harm → ACT psychological flexibility. '
            'Moral or spiritual rigidity → Buddhist clinging to views (third fetter). '
            'Rules strongly tied to identity ("I am someone who...") → Narrative externalisation. '
            'Perfectionism + rigidity combination → ACT + Buddhist together.'
        ),
        keywords=['always have to', 'never', 'rules', 'must', 'can\'t change', 'that\'s just me',
                  'the right way', 'my way', 'principles', 'standards', 'won\'t compromise',
                  'how it has to be', 'stubborn', 'inflexible', 'set in my ways'],
        urgency_when_detected='medium'
    ),

    WisdomLesson(
        id='unprocessed_trauma_patterns',
        title='Unprocessed Trauma Driving Present Behaviour',
        mistake_type='repetition',
        domains=['mental_health', 'health', 'relationships'],
        universal_pattern=(
            'Trauma — overwhelmingly distressing experience that exceeds the nervous '
            'system\'s capacity to process — does not resolve through time alone. '
            'It is stored in the body and the implicit memory system as automatic '
            'survival responses (fight, flight, freeze, fawn) that activate '
            'in present circumstances that resemble the original threat — '
            'even when the current situation is safe. The person who was once '
            'helpless continues to respond as if helpless, not from weakness '
            'but from an unupdated survival system.'
        ),
        historical_examples=[
            'Shell shock (WWI) → combat fatigue (WWII) → PTSD (1980): '
            'recognition that extreme experience leaves lasting physiological traces '
            'took 60 years and multiple wars. Military physicians documented it in '
            'every conflict; institutional denial prolonged veterans\' suffering. '
            'Applies to anyone whose past experiences are still driving present '
            'reactions in ways they cannot fully explain',
            'Japanese hibakusha (atomic bomb survivors, 1945–present): showed '
            'chronic somatic symptoms, social withdrawal, and shame decades after '
            'the event — the same pattern Western trauma literature later named PTSD. '
            'The body\'s response to overwhelm is universal, not culturally specific (Eastern). '
            'Applies to any user carrying shame about their physiological responses to past events',
            'Wilfred Owen, Siegfried Sassoon, and other WWI poets: documented in verse '
            'the exact phenomenology of what we now call PTSD — intrusive memories, '
            'hypervigilance, dissociation — but the institution refused to recognise it, '
            'court-martialling soldiers for cowardice instead. Applies to anyone whose '
            'trauma responses have been labelled as weakness, laziness, or overreaction',
            'Nelson Mandela on Robben Island: described specific somatic practices '
            '(physical exercise, gardening) as essential to maintaining psychological '
            'integrity under imprisonment — he intuitively used body-based approaches '
            'before the research existed. Applies as a positive model: somatic '
            'regulation is not weakness but resilience infrastructure',
            'The multigenerational trauma of indigenous communities (Australia, '
            'Americas, Africa): documented transmission of trauma physiology '
            'across generations without direct exposure — epigenetic research '
            'confirms the biological mechanism. Applies to users who cannot '
            'account for their trauma responses from their own direct history',
            'ACE study (Felitti et al., 1998): ACE score of 4+ predicts 2x higher '
            'heart disease risk, 7x higher alcoholism, 12x higher suicide risk. '
            'Trauma is a public health issue, not a personal weakness. Applies '
            'directly when health conditions coexist with a history of adverse experiences',
        ],
        interpretations=[
            Interpretation(
                school='Somatic / Trauma-informed',
                culture='Western',
                stance='Trauma is stored in the body, not just the mind. '
                       'Talk therapy alone cannot reach it — the body must be '
                       'included in the healing. Levine\'s somatic experiencing '
                       'and van der Kolk\'s body-based approaches work with '
                       'the nervous system\'s incomplete survival responses, '
                       'completing them rather than suppressing them.',
                advice='When triggered: pause and locate the physical sensation '
                       '(tightness, heaviness, holding of breath). '
                       'Name it without story: "There is tightness in my chest." '
                       'Breathe into it slowly. Notice any small movement impulse '
                       '(shaking, shifting). Allow it. This is the nervous system '
                       'completing what was interrupted.',
                evidence='van der Kolk, The Body Keeps the Score (2014). '
                         'Levine, Waking the Tiger (1997): somatic experiencing. '
                         'Felitti et al., ACE study (1998). '
                         'EMDR meta-analysis (Chen et al., 2014): body-inclusive '
                         'approaches outperform pure talk for trauma.',
                conditions='Best when person shows physiological symptoms, '
                           'hypervigilance, or freeze responses; '
                           'ALWAYS recommend professional support alongside this'
            ),
            Interpretation(
                school='Attachment Theory',
                culture='Western',
                stance='Relational trauma (trauma from the actions of caregivers) '
                       'creates disorganised attachment — the simultaneous need '
                       'for and fear of closeness. The nervous system learned '
                       'that the source of comfort is also the source of danger. '
                       'Healing requires a new relational experience: '
                       'consistent safety with another person — therapist, '
                       'partner, or friend — that updates the working model.',
                advice='Identify one relationship that currently feels safe — '
                       'even partially. In that relationship, practice one small '
                       'act of vulnerability: sharing one true thing you '
                       'would normally protect. Notice the response. '
                       'The nervous system updates through experience, '
                       'not through understanding alone.',
                evidence='Bowlby, Attachment and Loss vol. 3 (1980). '
                         'Fonagy et al., Affect Regulation, Mentalization '
                         'and the Development of the Self (2002). '
                         'Siegel, The Developing Mind (1999).',
                conditions='Best when trauma is relational (from people, not events); '
                           'person oscillates between seeking and fearing closeness'
            ),
            Interpretation(
                school='Buddhist',
                culture='Eastern',
                stance='The Buddha\'s teaching on dukkha (suffering) acknowledges '
                       'that some suffering arises from wounds that precede '
                       'conscious understanding. Metta (loving-kindness) practice — '
                       'directing compassion first to self — is the '
                       'counterweight to the shame and self-blame that '
                       'trauma survivors disproportionately carry.',
                advice='Begin metta practice with yourself: '
                       '"May I be safe. May I be healthy. May I be at peace. '
                       'May I live with ease." Say this toward yourself — '
                       'the part of you that was hurt and is still trying '
                       'to protect you. Compassion toward the traumatised self '
                       'is not indulgence; it is the beginning of healing.',
                evidence='Neff, Self-Compassion (2011): self-compassion '
                         'reduces shame and increases trauma recovery. '
                         'Germer, The Mindful Path to Self-Compassion (2009). '
                         'RCT evidence for metta reducing PTSD symptoms '
                         '(Kearney et al., 2013).',
                conditions='Best when shame and self-blame are prominent; '
                           'person is spiritually oriented or open to meditation'
            ),
        ],
        resolution_hint=(
            'Physiological symptoms, freeze/fight/flight triggers → Somatic/Trauma-informed. '
            'Relational trauma, push-pull in close relationships → Attachment Theory. '
            'Shame, self-blame, self-criticism prominent → Buddhist metta/self-compassion. '
            'ANY trauma disclosure → flag HIGH urgency; recommend professional support; '
            'KB approaches are supplementary, not primary treatment.'
        ),
        keywords=['trauma', 'can\'t get over it', 'triggered', 'flashback', 'numb',
                  'freeze', 'panic attacks', 'hypervigilant', 'always on edge',
                  'don\'t feel safe', 'something happened', 'was abused',
                  'childhood', 'can\'t trust', 'shame', 'self-blame'],
        urgency_when_detected='high'
    ),

]


if __name__ == '__main__':
    print(f"Wisdom Knowledge Base: {len(WISDOM_LESSONS)} lessons loaded")
    print(f"Mistake types (discovered): {get_all_mistake_types()}")
    print(f"Domains (discovered):       {get_all_domains()}")
    print(f"Schools (discovered):       {get_all_schools()}")
    print(f"Cultures (discovered):      {get_all_cultures()}")
    total_interps = sum(len(l.interpretations) for l in WISDOM_LESSONS)
    total_examples = sum(len(l.historical_examples) for l in WISDOM_LESSONS)
    print(f"Total interpretations: {total_interps}")
    print(f"Total historical examples: {total_examples}")
    print("\nSchool rotation test (CBT rejected, tried=[CBT]):")
    print(f"  Next: {get_next_school('CBT / Psychology', ['CBT / Psychology'])}")
    print("School rotation test (all Western tried):")
    western = get_schools_by_culture('Western')
    print(f"  All Western: {western}")
    print(f"  Next after all Western tried: {get_next_school(western[-1], western)}")
    print("\nTest match for 'I keep avoiding the doctor':")
    results = match_lessons_to_text("I keep avoiding the doctor and putting off my health checks")
    for r in results:
        print(f"  → {r.title} ({len(r.interpretations)} interpretations)")
