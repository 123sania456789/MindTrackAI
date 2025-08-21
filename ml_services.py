import json

# Lightweight, practical sentiment using NLTK VADER with TextBlob fallback
def _ensure_nltk_data():
    try:
        import nltk  # noqa: F401
        from nltk.data import find
        try:
            find('sentiment/vader_lexicon.zip')
        except LookupError:
            import nltk as _nltk
            _nltk.download('vader_lexicon')
        try:
            find('tokenizers/punkt')
        except LookupError:
            import nltk as _nltk
            _nltk.download('punkt')
    except Exception:
        pass


def analyze_sentiment(text: str):
    """Return sentiment label and confidence for the given text.

    Prefers NLTK VADER; falls back to TextBlob if VADER unavailable.
    Output schema: { sentiment: 'positive'|'negative'|'neutral', confidence: float, text }
    """
    if not text:
        return {'sentiment': 'neutral', 'confidence': 0.0, 'text': text}

    # Try VADER
    try:
        _ensure_nltk_data()
        from nltk.sentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        compound = float(scores.get('compound', 0.0))
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        return {
            'sentiment': label,
            'confidence': round(abs(compound), 3),
            'text': text
        }
    except Exception:
        pass

    # Fallback: TextBlob
    try:
        from textblob import TextBlob
        blob = TextBlob(text)
        polarity = float(blob.sentiment.polarity)
        if polarity > 0.05:
            label = 'positive'
        elif polarity < -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        return {
            'sentiment': label,
            'confidence': round(abs(polarity), 3),
            'text': text
        }
    except Exception:
        # Final safety
        return {'sentiment': 'neutral', 'confidence': 0.0, 'text': text}


def analyze_journal_entry(entry_id):
    """Placeholder for journal entry analysis"""
    return {
        'entry_id': entry_id,
        'sentiment': 'neutral',
        'emotions': ['neutral'],
        'topics': ['general']
    }


