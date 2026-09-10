from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    name: str
    confidence: float


KEYWORDS = {
    "Sleep": ("sleep", "insomnia", "snoring", "tired"),
    "Nutrition": ("diet", "nutrition", "food", "vitamin", "meal"),
    "Exercise": ("exercise", "workout", "fitness", "muscle"),
    "Mental Wellbeing": ("stress", "anxiety", "mood", "depressed", "worry"),
    "Headache": ("headache", "migraine", "head pain"),
    "Digestive Health": ("stomach", "nausea", "constipation", "diarrhea", "digestion"),
    "Heart Health": ("heart", "blood pressure", "palpitation"),
    "Respiratory": ("cough", "breathing", "asthma", "wheeze"),
    "Skin": ("rash", "skin", "itch", "acne"),
    "Preventive Health": ("screening", "vaccine", "checkup", "prevention"),
    "General Wellness": ("healthy", "wellness", "habit"),
}


def classify(text: str) -> Topic:
    lowered = text.casefold()
    scores = {topic: sum(lowered.count(word) for word in words) for topic, words in KEYWORDS.items()}
    name, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        return Topic("Other", 0.2)
    return Topic(name, min(0.95, 0.55 + score * 0.1))
