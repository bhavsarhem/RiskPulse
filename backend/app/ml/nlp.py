import re
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger("RiskPulse.NLP")

# Standard risk categories and associated keywords
RISK_KEYWORDS = {
    "bankruptcy_risk": ["bankruptcy", "bankrupt", "insolvency", "insolvent", "liquidation", "winding up", "chapter 11"],
    "legal_dispute": ["lawsuit", "legal dispute", "court case", "litigation", "suing", "sued", "arbitration", "pending suit"],
    "late_payments": ["late payment", "delay", "defaulted", "bounced emi", "cheque bounce", "overdue", "non-payment"],
    "regulatory_tax": ["tax notice", "mca penalty", "audit qualification", "fines", "compliance failure", "tax evasion"],
    "financial_stress": ["loss making", "negative cash flow", "revenue decline", "under-capitalized", "distress", "cash crunch"]
}

# Positive sentiment words
POSITIVE_WORDS = ["stable", "profitable", "growth", "surplus", "repaid", "secured", "expanding", "good", "strong", "excellent", "healthy"]
# Negative sentiment words
NEGATIVE_WORDS = ["fail", "decrease", "unpaid", "arrears", "dispute", "risk", "warning", "stress", "concern", "poor", "bad", "adversity"]

class NLPRiskEngine:
    def __init__(self):
        # We check if heavy libraries are available
        self.has_spacy = False
        self.nlp = None
        try:
            import spacy
            # Try to load a small English model
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.has_spacy = True
            except IOError:
                logger.warning("spaCy is installed but 'en_core_web_sm' model is not downloaded. Using rule-based fallbacks.")
        except ImportError:
            logger.info("spaCy not found. Using custom regex-based NLP engine.")

    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Parses text from raw bytes. If pdf or image, includes hooks.
        For simplicity in local execution, reads text/utf-8 or falls back to basic string decoder.
        """
        if filename.endswith('.pdf'):
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                return text
            except Exception:
                # PDF extractor library fallback
                return file_content.decode('utf-8', errors='ignore')
        else:
            return file_content.decode('utf-8', errors='ignore')

    def analyze_remarks(self, text: str) -> Dict[str, Any]:
        """
        Analyzes remarks text to find positive/negative sentiment, risk categories, 
        and extracts key risk parameters.
        """
        if not text:
            return {
                "sentiment_score": 0.0,
                "risk_score": 0.0,
                "risk_flags": [],
                "summary": "No remarks provided."
            }

        text_lower = text.lower()
        
        # 1. Category extraction
        detected_categories = []
        risk_weight = 0.0
        for category, keywords in RISK_KEYWORDS.items():
            found_words = []
            for word in keywords:
                if word in text_lower:
                    found_words.append(word)
            if found_words:
                detected_categories.append(category)
                risk_weight += len(found_words) * 1.5

        # 2. Simple Sentiment Lexicon Score
        pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
        neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
        
        total_sentiment_words = pos_count + neg_count
        if total_sentiment_words > 0:
            sentiment_score = (pos_count - neg_count) / total_sentiment_words
        else:
            sentiment_score = 0.0

        # Adjust risk score based on sentiment (negative sentiment increases risk)
        nlp_risk_score = min(100.0, max(0.0, (risk_weight * 10.0) + (neg_count * 5.0) - (pos_count * 2.0)))

        # 3. Summarization
        summary_bullets = []
        if detected_categories:
            summary_bullets.append(f"Identified risks in categories: {', '.join(detected_categories)}.")
        
        # Extract sentences with negative issues for summary
        sentences = re.split(r'[.!?\n]', text)
        stress_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            # Check if sentence contains any of the negative or risk keywords
            for word in list(RISK_KEYWORDS.values())[0] + NEGATIVE_WORDS:
                if re.search(r'\b' + re.escape(word) + r'\b', s_clean.lower()):
                    stress_sentences.append(s_clean)
                    break
            if len(stress_sentences) >= 3:
                break
        
        if stress_sentences:
            summary_bullets.append("Key negative excerpts:")
            for s in stress_sentences:
                summary_bullets.append(f" - {s}")
        else:
            summary_bullets.append("No critical negative stress statements detected.")

        summary = "\n".join(summary_bullets)

        return {
            "sentiment_score": sentiment_score,  # -1.0 to 1.0
            "risk_score": nlp_risk_score,        # 0.0 to 100.0
            "risk_flags": detected_categories,
            "summary": summary
        }

nlp_risk_engine = NLPRiskEngine()
