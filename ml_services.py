import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import pickle
import os

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

# Preprocessing pipeline using spaCy/NLTK
def preprocess_text(text: str):
    """Apply full preprocessing pipeline: tokenization, lemmatization, stopword filtering"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text.lower())
        
        # Tokenization, lemmatization, stopword filtering
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
        return " ".join(tokens)
    except Exception:
        # Fallback to NLTK
        try:
            _ensure_nltk_data()
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            # Download required NLTK data
            import nltk
            try:
                nltk.download('wordnet')
                nltk.download('stopwords')
            except:
                pass
            
            # Tokenization
            tokens = word_tokenize(text.lower())
            
            # Stopword filtering
            stop_words = set(stopwords.words('english'))
            tokens = [word for word in tokens if word.isalpha() and word not in stop_words]
            
            # Lemmatization
            lemmatizer = WordNetLemmatizer()
            tokens = [lemmatizer.lemmatize(word) for word in tokens]
            
            return " ".join(tokens)
        except Exception:
            # Final fallback: basic cleaning
            return text.lower().strip()

# TF-IDF + Random Forest Baseline Model
class BaselineMLModel:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.pipeline = None
        self.model_path = 'models/baseline_model.pkl'
        self.vectorizer_path = 'models/tfidf_vectorizer.pkl'
        
    def create_pipeline(self):
        """Create TF-IDF + Random Forest pipeline"""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )
        
        self.pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('classifier', self.model)
        ])
        
    def train(self, texts, labels):
        """Train the baseline model"""
        if not os.path.exists('models'):
            os.makedirs('models')
            
        # Preprocess texts
        processed_texts = [preprocess_text(text) for text in texts]
        
        # Create and train pipeline
        self.create_pipeline()
        self.pipeline.fit(processed_texts, labels)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
            
        return self.evaluate(processed_texts, labels)
    
    def predict(self, text):
        """Make prediction on new text"""
        if self.pipeline is None:
            self.load_model()
            
        processed_text = preprocess_text(text)
        prediction = self.pipeline.predict([processed_text])[0]
        probability = self.pipeline.predict_proba([processed_text])[0]
        
        return {
            'prediction': prediction,
            'confidence': float(max(probability)),
            'probabilities': probability.tolist()
        }
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                self.pipeline = pickle.load(f)
            self.vectorizer = self.pipeline.named_steps['tfidf']
            self.model = self.pipeline.named_steps['classifier']
        except FileNotFoundError:
            raise Exception("Model not found. Please train the model first.")
    
    def evaluate(self, texts, labels):
        """Evaluate model performance"""
        if self.pipeline is None:
            raise Exception("Model not trained yet.")
            
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # Train on training set
        self.pipeline.fit(X_train, y_train)
        
        # Predict on test set
        y_pred = self.pipeline.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Cross-validation
        cv_scores = cross_val_score(self.pipeline, texts, labels, cv=5)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'cross_validation_mean': float(cv_scores.mean()),
            'cross_validation_std': float(cv_scores.std()),
            'confusion_matrix': cm.tolist(),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }

# Initialize baseline model
baseline_model = BaselineMLModel()

def analyze_journal_entry(entry_id, text):
    """Enhanced journal entry analysis using baseline ML model"""
    # Basic sentiment analysis
    sentiment_result = analyze_sentiment(text)
    
    # Preprocess text
    processed_text = preprocess_text(text)
    
    # Extract features
    features = {
        'text_length': len(text),
        'word_count': len(text.split()),
        'processed_length': len(processed_text.split()),
        'sentiment': sentiment_result['sentiment'],
        'confidence': sentiment_result['confidence']
    }
    
    # Try to use ML model for mood prediction if available
    try:
        # This would require training data - placeholder for now
        ml_prediction = "neutral"  # Placeholder
    except:
        ml_prediction = "neutral"
    
    return {
        'entry_id': entry_id,
        'sentiment': sentiment_result['sentiment'],
        'emotions': [sentiment_result['sentiment']],
        'topics': extract_topics(processed_text),
        'features': features,
        'ml_prediction': ml_prediction
    }

def extract_topics(text):
    """Extract main topics from text using keyword matching"""
    topics = []
    text_lower = text.lower()
    
    topic_keywords = {
        'anxiety': ['anxious', 'worry', 'stress', 'nervous', 'panic'],
        'depression': ['sad', 'depressed', 'hopeless', 'worthless', 'tired'],
        'sleep': ['sleep', 'insomnia', 'awake', 'tired', 'rest'],
        'relationships': ['friend', 'family', 'partner', 'relationship', 'social'],
        'work': ['work', 'job', 'career', 'office', 'professional'],
        'health': ['health', 'exercise', 'diet', 'physical', 'body']
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            topics.append(topic)
    
    return topics if topics else ['general']

def get_model_performance():
    """Get current model performance metrics"""
    try:
        # This would return actual metrics if model is trained
        return {
            'status': 'Model not trained yet',
            'message': 'Train the model with sample data to see performance metrics'
        }
    except Exception as e:
        return {
            'status': 'Error',
            'message': str(e)
        }

def train_sample_model():
    """Train model with sample data for demonstration"""
    # Sample data for demonstration
    sample_texts = [
        "I feel happy and excited about today",
        "I'm feeling really sad and hopeless",
        "I'm anxious about my upcoming presentation",
        "I had a great time with my friends",
        "I'm stressed about work deadlines",
        "I feel calm and peaceful",
        "I'm worried about my health",
        "I'm grateful for my family"
    ]
    
    sample_labels = [
        'positive', 'negative', 'negative', 'positive', 
        'negative', 'positive', 'negative', 'positive'
    ]
    
    try:
        results = baseline_model.train(sample_texts, sample_labels)
        return {
            'status': 'success',
            'message': 'Model trained successfully with sample data',
            'metrics': results
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Training failed: {str(e)}'
        }


