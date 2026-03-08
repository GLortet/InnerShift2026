from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
REPORTS_DIR = DATA_DIR / "reports"
PROFILES_DIR = DATA_DIR / "profiles"
SESSIONS_DIR = DATA_DIR / "sessions"
ASSETS_DIR = BASE_DIR / "assets"
STYLES_DIR = ASSETS_DIR / "styles"

DIRECTORIES = [
    DATA_DIR,
    AUDIO_DIR,
    TRANSCRIPTS_DIR,
    REPORTS_DIR,
    PROFILES_DIR,
    SESSIONS_DIR,
    ASSETS_DIR,
    STYLES_DIR,
]

APP_NAME = "InnerShift"
APP_BASELINE = "Clarifier la parole. Faire emerger les lignes de force. Structurer l'action."
APP_SUBTITLE = (
    "Un copilote local de clarification interieure et strategique, "
    "concu pour transformer une parole libre en decisions plus nettes."
)

DEFAULT_USER_ID = "default_user"
DEFAULT_PROFILE_PATH = PROFILES_DIR / f"{DEFAULT_USER_ID}.json"
DEFAULT_SESSION_TITLE = "Session de reflection"

UI_NAVIGATION = [
    "Accueil",
    "Nouvelle session",
    "Rapport",
    "Historique",
    "Profil utilisateur",
]

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg"}
SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "video/mp4": ".m4a",
}

WHISPER_MODEL_SIZE = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_BEAM_SIZE = 5
WHISPER_VAD_FILTER = True

MIN_TRANSCRIPTION_WORDS = 20
MAX_SUMMARY_SENTENCES = 3
KEYWORD_LIMIT = 12
TOP_THEME_LIMIT = 6
SALIENT_SENTENCE_LIMIT = 5
IDEAS_LIMIT = 5
TENSION_LIMIT = 3
RECOMMENDATION_LIMIT = 3

PDF_FILENAME_TEMPLATE = "innershift_report_{session_id}.pdf"

COLOR_BACKGROUND = "#F6F1E8"
COLOR_PANEL = "#F1E8DA"
COLOR_PANEL_ALT = "#FCFAF7"
COLOR_TEXT = "#17202A"
COLOR_MUTED = "#5D6D7E"
COLOR_PRIMARY = "#1E3A4C"
COLOR_SECONDARY = "#8A6E52"
COLOR_ACCENT = "#B78C52"
COLOR_SUCCESS = "#5E8C61"
COLOR_WARNING = "#A66A4A"
COLOR_GRID = "#D7C9B8"

PDF_COLORS = {
    "background": COLOR_BACKGROUND,
    "panel": COLOR_PANEL,
    "panel_alt": COLOR_PANEL_ALT,
    "text": COLOR_TEXT,
    "muted": COLOR_MUTED,
    "primary": COLOR_PRIMARY,
    "secondary": COLOR_SECONDARY,
    "accent": COLOR_ACCENT,
    "success": COLOR_SUCCESS,
    "warning": COLOR_WARNING,
    "grid": COLOR_GRID,
}

STOPWORDS_FR = {
    "a", "ai", "aie", "aient", "ainsi", "alors", "apres", "au", "aucun", "aussi", "autre",
    "avant", "avec", "avoir", "bon", "car", "ce", "cela", "ces", "cet", "cette", "comme",
    "comment", "dans", "de", "des", "du", "dedans", "depuis", "devrait", "dois", "donc",
    "elle", "elles", "en", "encore", "entre", "est", "et", "etre", "eu", "fait", "faire",
    "fois", "il", "ils", "je", "j", "la", "le", "les", "leur", "leurs", "lui", "ma", "mais",
    "me", "meme", "mes", "mon", "ne", "nos", "notre", "nous", "on", "ou", "par", "pas",
    "parce", "peu", "peut", "plus", "pour", "pourquoi", "qu", "que", "quel", "quelle",
    "quelles", "quels", "qui", "sa", "se", "ses", "si", "son", "sont", "sur", "ta", "te",
    "tes", "toi", "ton", "tous", "tout", "trop", "tu", "un", "une", "vos", "votre", "vous", "y",
}

STOPWORDS_EN = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "can", "could",
    "did", "do", "does", "for", "from", "had", "has", "have", "how", "i", "if", "in", "into",
    "is", "it", "its", "just", "me", "more", "my", "not", "of", "on", "or", "our", "out",
    "really", "so", "that", "the", "their", "them", "there", "they", "this", "to", "too",
    "was", "we", "were", "what", "when", "which", "who", "with", "would", "you", "your",
}

STOPWORDS = STOPWORDS_FR | STOPWORDS_EN

FILLER_WORDS = {
    "euh",
    "heu",
    "hum",
    "bah",
    "ben",
    "voila",
    "genre",
    "enfin",
    "tu vois",
    "je veux dire",
    "sort of",
    "kind of",
    "you know",
    "like",
}

CATEGORY_LABELS = {
    "vision": "Vision / aspiration",
    "blockages": "Blocages / tensions",
    "action": "Action / decision",
    "emotion": "Charge emotionnelle",
    "needs": "Besoins exprimes",
    "resources": "Ressources / appuis",
    "coherence": "Coherence / dispersion",
}

CATEGORY_KEYWORDS = {
    "vision": {
        "j'aimerais", "je veux", "je voudrais", "j'aspire", "vision", "avenir", "objectif",
        "ambition", "souhaite", "desire", "i want", "i would like", "goal", "future", "dream",
    },
    "blockages": {
        "bloque", "peur", "difficile", "probleme", "frein", "tension", "honte", "culpabilite",
        "j'hesite", "je n'arrive pas", "stuck", "blocked", "afraid", "fear", "hard", "issue",
    },
    "action": {
        "je vais", "prochaine etape", "decider", "agir", "faire", "mettre en place", "commencer",
        "tester", "plan", "next step", "decide", "act", "implement", "start", "ship",
    },
    "emotion": {
        "stress", "angoisse", "fatigue", "joie", "enthousiasme", "frustre", "motivation",
        "confus", "perdu", "excited", "frustrated", "tired", "energized", "confused",
    },
    "needs": {
        "besoin", "besoin de", "j'ai besoin", "support", "clarte", "temps", "cadre", "stabilite",
        "need", "i need", "space", "support", "clarity",
    },
    "resources": {
        "ressource", "force", "energie", "appui", "experience", "competence", "confiance",
        "allie", "support", "strength", "energy", "skill", "confidence",
    },
    "coherence": {
        "coherent", "clarifie", "alignement", "essentiel", "priorite", "focus", "aligned",
        "clear", "priority", "important",
    },
}

THEME_KEYWORDS = {
    "Vision / aspiration": {
        "avenir", "objectif", "ambition", "desir", "vision", "projet", "future", "goal", "growth",
    },
    "Blocages / tensions": {
        "blocage", "peur", "doute", "fatigue", "risque", "pression", "stuck", "fear", "tension",
    },
    "Action / decision": {
        "action", "decision", "faire", "commencer", "plan", "prochaine", "step", "execute", "deliver",
    },
    "Besoins exprimes": {
        "besoin", "clarte", "temps", "cadre", "support", "space", "clarity",
    },
    "Ressources / appuis": {
        "energie", "force", "ressource", "confiance", "experience", "skill", "support",
    },
    "Coherence / dispersion": {
        "priorite", "focus", "essentiel", "coherent", "confus", "disperse", "clarte", "confused",
    },
}

EMOTIONAL_SIGNAL_LEXICON = {
    "stress": {"stress", "pression", "angoisse", "stressant", "overwhelmed", "pressure"},
    "frustration": {"frustre", "frustration", "agace", "bloque", "frustrated", "annoyed"},
    "doute": {"doute", "hesite", "incertain", "uncertain", "not sure"},
    "motivation": {"motive", "envie", "elan", "energy", "motivated", "drive"},
    "enthousiasme": {"enthousiaste", "excite", "joie", "inspire", "excited", "inspired"},
    "fatigue": {"fatigue", "epuise", "lourd", "drained", "tired", "exhausted"},
    "clarte": {"clair", "clarte", "lucide", "clear", "clarity"},
    "confusion": {"confus", "perdu", "flou", "brouillon", "confused", "messy"},
}

COGNITIVE_SIGNAL_LEXICON = {
    "insight": {"je realise", "prise de conscience", "je comprends", "i realize", "i understand"},
    "projection": {"si", "quand", "dans quelques mois", "later", "next quarter", "future"},
    "hesitation": {"j'hesite", "je ne sais pas", "peut-etre", "maybe", "not sure"},
    "clarification": {"en fait", "ce qui compte", "l'essentiel", "what matters", "priority"},
    "rumination": {"toujours", "encore", "je tourne en rond", "again", "loop"},
}

ACTION_SIGNAL_LEXICON = {
    "decision": {"je decide", "je vais", "choisir", "decider", "i decide", "i will"},
    "planning": {"plan", "prochaine etape", "agenda", "timeline", "roadmap"},
    "experimentation": {"tester", "essayer", "prototype", "experiment", "pilot"},
    "engagement": {"m'engager", "commit", "tenir", "follow through"},
}

CONTRAST_CONNECTORS = {
    "mais",
    "pourtant",
    "sauf que",
    "en meme temps",
    "however",
    "but",
    "although",
    "yet",
}

SCORE_LABELS = {
    "clarity": "Clarte percue",
    "emotional_load": "Charge emotionnelle",
    "action_orientation": "Orientation action",
    "mental_dispersion": "Dispersion mentale",
    "internal_coherence": "Coherence interne",
}

SCORE_EXPLANATIONS = {
    "clarity": "Estimation de la nettete du discours et de la priorisation exprimee.",
    "emotional_load": "Estimation de l'intensite emotionnelle percue dans la parole.",
    "action_orientation": "Presence de formulations concretes, decisions et prochaines etapes.",
    "mental_dispersion": "Indice exploratoire de dispersion, confusion ou multiplication des pistes.",
    "internal_coherence": "Compatibilite apparente entre aspirations, contraintes et decisions evoquees.",
}

METHODOLOGY_TEXT = (
    "Cette lecture repose sur des heuristiques linguistiques locales : nettoyage du texte, "
    "frequences lexicales, extraction de themes, detection de signaux explicites et "
    "construction d'indicateurs exploratoires."
)

DISCLAIMER_TEXT = (
    "InnerShift fournit des tendances observees et des pistes de clarification. "
    "Il ne s'agit ni d'un diagnostic medical, ni d'une evaluation psychologique, "
    "ni d'une verite definitive sur la personne."
)

PROFILE_EMPTY_STATE = {
    "user_id": DEFAULT_USER_ID,
    "updated_at": None,
    "session_count": 0,
    "top_themes": [],
    "top_keywords": [],
    "recurring_tones": [],
    "score_trends": {},
    "recent_recommendations": [],
    "progress_signals": [],
    "recent_sessions": [],
}
