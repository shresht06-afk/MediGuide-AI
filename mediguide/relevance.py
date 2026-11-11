"""
Medical relevance classifier for MediGuide AI  — v2 (bugfix release).

CONFIRMED BUGS FIXED
--------------------
1. Celebrity / person queries  ("who is Hrithik Roshan?") scored 0 because no
   negative pattern existed for person/biography queries.  Score 0 > threshold
   -2  =>  ambiguous_pass  =>  LLM answered.

2. Raw arithmetic expressions  ("what is 68900+98776") scored 0 because the
   math negative-pattern list only covered named concepts (calculus, algebra…),
   not digit-operator sequences.  Same ambiguous_pass path.

ARCHITECTURAL FIX
-----------------
The previous threshold was _REJECT_THRESHOLD = -2, which meant any message
scoring 0 (no signals in either direction) was passed as "ambiguous".  This
is wrong: a message with zero medical evidence should not reach the LLM.

New rule:  score > 0  =>  accepted (positive medical evidence present).
           score <= 0 =>  rejected, unless the message is:
                          - trivially short (<= _SHORT_PASS_LENGTH chars), or
                          - a pure greeting, or
                          - a confirmed short follow-up in a medical conversation.

New negative signal groups added:
  - Person / celebrity / biography queries.
  - Raw arithmetic digit+operator expressions.
  - Broadened math, geography, entertainment and trivia patterns.

The follow-up bypass now also requires that the message itself contains no
negative off-topic signal, preventing "who is Hrithik Roshan?" from slipping
through when preceded by a medical assistant turn.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# A message is accepted ONLY when score is STRICTLY GREATER THAN this value.
# score == 0 (no signals either way) is now REJECTED.
_REJECT_THRESHOLD = 0

# Messages at or under this character count bypass scoring entirely.
_SHORT_PASS_LENGTH = 12

# Follow-up messages must be at most this long to qualify for the bypass.
_FOLLOWUP_MAX_LENGTH = 150

# ---------------------------------------------------------------------------
# Signal tables
# ---------------------------------------------------------------------------

_POSITIVE_SIGNALS: list[tuple[str, int]] = [
    # Symptom vocabulary
    (
        r"\b(symptom|symptoms|fever|pain|ache|headache|migraine|sore|swollen|nausea|vomit|diarrhea|constipat"
        r"|bleed|bleeding|nosebleed|rash|itch|dizzy|dizziness|fatigue|tired|weak|cramp|spasm|tremor|seizure|faint"
        r"|fainting|passed out|pass out|unconscious|not waking|won.?t wake"
        r"|blurr|vision loss|hearing loss|tinnitus|discharge|sweat|chills"
        r"|shortness of breath|palpitat|wheez|cough|sneez|runny nose|congestion"
        r"|bloat|indigestion|heartburn|swelling|inflammation|numbness|tingling"
        r"|breathless|confusion|disoriented|loss of appetite|chest tightness"
        r"|severity|severe|mild|moderate|dull|sharp|throbbing|stabbing|burning|aching"
        r"|out of 10|/10\b"
        r"|kill myself|hurt myself|self.?harm|suicide|suicidal|hopeless|harm myself)\b",
        3,
    ),
    # Body parts / systems
    (
        r"\b(stomach|liver|kidney|lung|lungs|heart|brain|spine|spinal|joint|muscle"
        r"|bone|skin|eye|ear|nose|throat|chest|abdomen|pelvis|bladder|bowel|colon"
        r"|intestin|appendix|gland|thyroid|pancreas|artery|vein|blood|lymph"
        r"|uterus|ovary|prostate|testis|nerve"
        r"|belly|belly button|navel|tummy|gut|temple|temples|forehead|behind eyes|neck|groin|flank"
        r"|back of head|across the abdomen|upper abdomen|lower abdomen"
        r"|lower right|lower left|upper right|upper left|right side|left side)\b",
        2,
    ),
    # Conditions and diseases
    (
        r"\b(diabetes|diabetic|hypertension|hypertensive|asthma|cancer|infection[s]?"
        r"|allergy|allergies|allergic|arthritis|anemia|depression|depressed|anxiety|anxious"
        r"|bipolar|schizophrenia|epilepsy|epileptic|migraine[s]?|fibromyalgia|autism"
        r"|adhd|obesity|obese|malaria|tuberculosis|tb\b|hepatitis|hiv|aids|covid"
        r"|coronavirus|flu|influenza|pneumonia|eczema|psoriasis|parkinson"
        r"|alzheimer|dementia|stroke|sepsis|appendicitis|ulcer[s]?|hernia|gout|lupus"
        r"|celiac|crohn|ibs|copd|hypothyroid|hyperthyroid|osteoporosis"
        r"|chronic|acute|autoimmune|disease[s]?|illness(es)?|disorder[s]?)\b",
        3,
    ),
    # Medications, treatments and diagnostics
    (
        r"\b(medication[s]?|medicine[s]?|drug[s]?|tablet[s]?|capsule[s]?|pill[s]?|dose[s]?|dosage[s]?"
        r"|antibiotic[s]?|painkiller[s]?|ibuprofen|paracetamol|acetaminophen|aspirin|metformin"
        r"|lisinopril|atorvastatin|omeprazole|amoxicillin|cetirizine|loratadine"
        r"|vaccines?|vaccinat\w*|immunis\w*|immuniz\w*|injection[s]?|surgery|surgical|therapy"
        r"|treatment[s]?|supplement[s]?|vitamins?|minerals?|probiotics?|antidepressant[s]?|antiviral[s]?"
        r"|insulin|steroid[s]?|chemotherapy|radiation|dialysis|transplant|biopsy"
        r"|mri|ct scan|xray|x-ray|ultrasound|ecg|ekg|blood test|urine test"
        r"|checkup|check-up|screening|colonoscopy|mammogram|endoscopy)\b",
        3,
    ),
    # Wellness, preventive health and first aid
    (
        r"\b(nutrition|nutritional|diet|dietary|calorie[s]?|protein[s]?|carbohydrate[s]?|carbs?"
        r"|fat|fibre|fiber|hydration|hydrate|rehydrate|exercise|fitness|workout|yoga|meditation"
        r"|sleep|insomnia|stress|mental health|wellbeing|wellness|weight loss"
        r"|weight gain|bmi|immune|immunity|first.?aid|wound[s]?|burn[s]?|fracture[s]?|sprain[s]?"
        r"|cpr|resuscitat\w*|dehydrat\w*|energy|vitality|stamina)\b",
        2,
    ),
    # Health-adjacent verbs and phrases
    (
        r"\b(heal|recovery|recovering|prevent|prevention|diagnos|treat|treatment"
        r"|manage|management|monitor|consult|prescrib"
        r"|causes?|caused by|what causes|why do i|why does|why am i"
        r"|feel (better|worse|sick|unwell|ill)"
        r"|getting sick|feeling sick|not feeling well"
        r"|health(y|ier)?|medical|clinical|surgical|prognosis"
        r"|side effect|contraindication)",
        1,
    ),
    # Medical professionals and facilities
    (
        r"\b(doctor|physician|gp\b|specialist|nurse|pharmacist|therapist|dentist"
        r"|dermatologist|cardiologist|oncologist|pediatrician|paediatrician"
        r"|gynecologist|gynaecologist|neurologist|psychiatrist|psychologist"
        r"|endocrinologist|urologist|ophthalmologist|hospital|clinic|er\b|a&e"
        r"|emergency room|urgent care|pharmacy|dispensary)\b",
        2,
    ),
    # Reproductive / life-stage health
    (
        r"\b(pregnancy|pregnant|postpartum|prenatal|antenatal|postnatal|infant[s]?"
        r"|toddler[s]?|paediatric\w*|pediatric\w*|child|children|adult[s]?|elderly|geriatric|menopause|menstrual|period"
        r"|puberty|fertility|breastfeed|lactation|contraception|contraceptive[s]?)\b",
        2,
    ),
    # Clinical intake & symptom progression / duration terms
    (
        r"\b(since yesterday|days ago|hours ago|weeks ago|more than a week|a few days"
        r"|just started|started today|duration|recurring|chronic|acute|constant|intermittent"
        r"|comes and goes|worse at night|all day|1 to 10|out of 10|none of these"
        r"|location|sensation|onset|severity|associated|cramp\w*|stabb\w*|throb\w*|puls\w*)\b",
        2,
    ),
]

_NEGATIVE_SIGNALS: list[tuple[str, int]] = [
    # --- Person / celebrity / biography queries (confirmed bypass vector) ---
    (
        r"\b(who is|who was|who are|who were"
        r"|biography of|life story of|life of"
        r"|actor|actress|singer|musician|politician|athlete"
        r"|sportsman|footballer|cricketer|celebrity|famous person|famous people"
        r"|bollywood|hollywood|pop star|rockstar"
        r"|president\b|prime minister\b|chancellor\b|king\b|queen\b"
        r"|prince\b|princess\b)\b",
        -3,
    ),
    # --- Raw arithmetic / calculation (confirmed bypass vector) ---
    # Catches: "68900+98776", "what is 5*3", "how much is 100/4", "calculate 7^2"
    (
        r"(\d[\d\s]*[+*^%][\s\d]|\b\d+\s*/\s*(?!10\b)\d+\b|\bwhat is \d|\bhow much is \d"
        r"|\bcalculate\b|\bcompute\b|\bsolve \d"
        r"|\b\d+ (plus|minus|times|divided by|multiplied by) \d)",
        -3,
    ),
    # --- Pure mathematics (word-based) ---
    (
        r"\b(calculus|algebra|geometry|trigonometry|integral|derivative|matrix"
        r"|vector|equation|theorem|proof|logarithm|factorial|prime number"
        r"|polynomial|quadratic|arithmetic|statistics|probability"
        r"|permutation|combination|set theory|number theory)\b",
        -3,
    ),
    # --- Software / programming ---
    (
        r"\b(python|javascript|java\b|c\+\+|typescript|html\b|css\b|sql\b"
        r"|database|algorithm|function\b|variable|code|coding|programming"
        r"|software|api\b|server|github|git\b|docker|kubernetes|cloud computing"
        r"|aws\b|azure\b|linux|terminal|command line|debug|compile|runtime"
        r"|syntax|library|framework|react\b|angular\b|vue\b|django|flask\b"
        r"|fastapi|nodejs|devops)\b",
        -3,
    ),
    # --- Geography / history / general trivia ---
    (
        r"\b(capital (city|of)|capital of [A-Z]|which country|what country"
        r"|president of [A-Z]|prime minister of [A-Z]|war of|battle of"
        r"|world war|ww1|ww2|wwi|wwii|year [12]\d{3}|geography|continent\b"
        r"|ocean\b|mountain range|longest river|country flag|currency of"
        r"|population of|history of [A-Z]|ancient|medieval|renaissance"
        r"|civilization|empire|colony|independence day)\b",
        -2,
    ),
    # --- Entertainment / sports / pop culture ---
    (
        r"\b(movie|film\b|box office|music chart|song lyrics|album"
        r"|band member|football score|basketball score|cricket match"
        r"|chess|video game|netflix|youtube channel|tiktok|instagram|twitter"
        r"|oscar|grammy|emmy|bafta|superhero|anime|manga|tv show|sitcom|web series)\b",
        -2,
    ),
    # --- Finance / markets ---
    (
        r"\b(stock price|share price|stocks\b|crypto|bitcoin|ethereum"
        r"|invest\b|investment\b|portfolio\b|interest rate|gdp|inflation rate"
        r"|recession|bank loan|index fund|mutual fund|equity market|bonds\b"
        r"|forex|hedge fund|venture capital|ipo\b|dividend|market cap)\b",
        -2,
    ),
    # --- Non-health writing / translation / weather ---
    (
        r"\b(write (a|an|me|my) (essay|poem|story|letter|email|report|resume|cv)"
        r"|write me (an|a) (essay|poem)|an essay about|a poem about"
        r"|translate (this|the|into)|summarize (this|the) (article|book|document|text)"
        r"|weather (today|tomorrow|forecast|report)"
        r"|climate change|global warming|political science|economics of)\b",
        -2,
    ),
    # --- Cooking / recipes ---
    (
        r"\b(recipe for|how to bake|teaspoon of|tablespoon of|roast the|fry the"
        r"|saute|marinate|cuisine\b|head chef|cooking method|ingredients for)\b",
        -1,
    ),
]

# Pronoun-heavy / affirmation / intake response patterns that suggest a follow-up or answer.
_FOLLOWUP_PATTERN = re.compile(
    r"^(yes|no|okay|ok|sure|thanks|thank you|please|why|how|when|can you"
    r"|what about|what if|what when|and (if|when)|is that|does that|do i|should i|will it"
    r"|how long|how much|it|that|this|they|them|those symptoms"
    r"|the medication|the treatment|what else|anything else|tell me more"
    r"|more details|go on|and then|what happens|what should"
    r"|since|started|began|about|around|more than|less than|a few|couple of"
    r"|for \d|past \d|just|only|mostly|mainly|none|not sure"
    r"|location|sensation|onset|severity|associated)\b",
    re.IGNORECASE,
)

# Pure greetings / openers — always accepted.
_GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|good (morning|afternoon|evening|night)|howdy|greetings"
    r"|help|i need help|can you help( me)?|what can you do|who are you"
    r"|what are you)[?!.,\s]*$",
    re.IGNORECASE,
)

# Pre-compile all signal patterns at import time.
_COMPILED_POSITIVE = [(re.compile(p, re.IGNORECASE), w) for p, w in _POSITIVE_SIGNALS]
_COMPILED_NEGATIVE = [(re.compile(p, re.IGNORECASE), w) for p, w in _NEGATIVE_SIGNALS]


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RelevanceResult:
    """Outcome of a medical relevance check.

    Attributes
    ----------
    is_medical:
        True  -> forward message to the LLM.
        False -> return OFF_TOPIC_RESPONSE.
    score:
        Net weighted signal score.
    reason:
        Short analytic label; never contains user message content.
    """

    is_medical: bool
    score: int
    reason: str


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def check_relevance(
    message: str,
    conversation_history: list[dict] | None = None,
) -> RelevanceResult:
    """Decide whether *message* is sufficiently medical to warrant an LLM response.

    Decision logic (in priority order):
    1. Empty or trivially short -> pass (short_pass / empty_pass).
    2. Pure greeting            -> pass (greeting_pass).
    3. Confirmed medical follow-up in an active medical conversation -> pass (followup_pass).
    4. Score > 0                -> pass (medical_pass).
    5. Score <= 0               -> reject (off_topic_reject).
    """
    stripped = message.strip()

    if not stripped:
        return RelevanceResult(is_medical=True, score=0, reason="empty_pass")

    if len(stripped) <= _SHORT_PASS_LENGTH:
        return RelevanceResult(is_medical=True, score=0, reason="short_pass")

    if _GREETING_PATTERN.match(stripped):
        return RelevanceResult(is_medical=True, score=0, reason="greeting_pass")

    if _is_medical_followup(stripped, conversation_history):
        return RelevanceResult(is_medical=True, score=0, reason="followup_pass")

    score = _score(stripped)
    if score > _REJECT_THRESHOLD:
        return RelevanceResult(is_medical=True, score=score, reason="medical_pass")

    return RelevanceResult(is_medical=False, score=score, reason="off_topic_reject")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _score(text: str) -> int:
    """Sum all positive and negative signal weights found in *text*."""
    total = 0
    for pattern, weight in _COMPILED_POSITIVE:
        if pattern.search(text):
            total += weight
    for pattern, weight in _COMPILED_NEGATIVE:
        if pattern.search(text):
            total += weight
    return total


def _negative_score(text: str) -> int:
    """Return only the negative component of the score (always <= 0)."""
    total = 0
    for pattern, weight in _COMPILED_NEGATIVE:
        if pattern.search(text):
            total += weight
    return total


def _is_medical_followup(message: str, history: list[dict] | None) -> bool:
    """Return True iff *message* is a short follow-up in a medical conversation.

    All conditions must hold:
    (a) History exists.
    (b) Message length <= _FOLLOWUP_MAX_LENGTH.
    (c) Message matches the follow-up affirmation/pronoun pattern.
    (d) Message itself carries NO negative off-topic signal.
        (Prevents "who is X?" from riding the follow-up bypass after a medical turn.)
    (e) The most recent assistant turn has positive medical signal.
    """
    if not history:
        return False
    if len(message) > _FOLLOWUP_MAX_LENGTH:
        return False
    if not _FOLLOWUP_PATTERN.match(message):
        return False
    if _negative_score(message) < 0:
        return False
    for turn in reversed(history):
        if turn.get("role") == "assistant":
            return _score(turn.get("content", "")) > 0
    return False


# ---------------------------------------------------------------------------
# Decline message
# ---------------------------------------------------------------------------

OFF_TOPIC_RESPONSE = (
    "I'm MediGuide AI, an assistant focused on health and medical information. "
    "I can help with symptoms, general health concerns, medications and wellness. "
    "Feel free to ask a health-related question."
)
