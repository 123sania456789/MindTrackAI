# MindTrack AI 🧠

A full-stack web application that combines advanced machine learning with intuitive journaling to help users understand their mental health patterns, track their mood, and gain valuable insights about themselves.

## ✨ Features

- **AI-Powered Journal Analysis**: Advanced BERT and spaCy models analyze journal entries for sentiment, emotions, and key themes
- **Mood Tracking**: Monitor daily mood patterns and correlate them with activities, sleep, and social interactions
- **Task Management**: Organize and track personal tasks with priority levels and due dates
- **Goal Setting**: Set and track personal goals with AI-powered insights
- **Real-time Insights**: Get instant feedback on your writing patterns and emotional trends
- **Beautiful UI**: Modern, responsive design with intuitive user experience

## 🛠️ Technology Stack

### Backend
- **Flask**: Lightweight web framework
- **PostgreSQL**: Primary database for data persistence
- **Redis**: Caching and session management
- **Celery**: Background task processing for ML analysis
- **SQLAlchemy**: Object-relational mapping

### Machine Learning
- **BERT**: Advanced sentiment analysis and emotion detection
- **spaCy**: Natural language processing and entity recognition
- **Scikit-learn**: Topic modeling and text analysis
- **TextBlob**: Additional sentiment analysis
- **NLTK**: Text processing utilities

### Frontend
- **Bootstrap 5**: Modern CSS framework
- **Chart.js**: Interactive data visualization
- **Font Awesome**: Icon library
- **jQuery**: JavaScript library for DOM manipulation

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+
- Redis 7+

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mindtrack-ai.git
   cd mindtrack-ai
   ```

2. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Web App: http://localhost:5000
   - Nginx (if enabled): http://localhost:80

### Local Development

1. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database**
   ```bash
   createdb mindtrack_ai
   ```

3. **Set up Redis**
   ```bash
   redis-server
   ```

4. **Set environment variables**
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   export DATABASE_URL=postgresql://localhost/mindtrack_ai
   export REDIS_URL=redis://localhost:6379/0
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Start the application**
   ```bash
   python app.py
   ```

7. **Start Celery worker (in another terminal)**
   ```bash
   celery -A ml_services.celery_app worker --loglevel=info
   ```

## 📁 Project Structure

```
mindtrack-ai/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── routes.py             # Route blueprints
├── ml_services.py        # Machine learning services
├── celery_config.py      # Celery configuration
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker services
├── Dockerfile           # Application container
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Landing page
│   ├── dashboard.html  # User dashboard
│   ├── login.html      # Login form
│   └── register.html   # Registration form
├── static/             # Static files (CSS, JS, images)
└── logs/              # Application logs
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env_example.txt`:

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery message broker URL
- `SPACY_MODEL`: spaCy model to use (default: en_core_web_sm)

### Database Setup

The application uses PostgreSQL with the following models:
- **Users**: User accounts and authentication
- **Journal Entries**: Text entries with AI analysis
- **Mood Entries**: Daily mood tracking
- **Tasks**: Personal task management
- **Goals**: Goal setting and progress tracking
- **ML Models**: Machine learning model metadata

## 🤖 Machine Learning Features

### Sentiment Analysis
- **BERT-based**: Advanced transformer model for sentiment classification
- **TextBlob**: Additional sentiment analysis with polarity and subjectivity
- **spaCy**: Named entity recognition and text processing

### Emotion Detection
- **Multi-label classification**: Detect multiple emotions in text
- **Confidence scoring**: Provide confidence levels for predictions
- **Real-time analysis**: Instant feedback on journal entries

### Topic Modeling
- **LDA (Latent Dirichlet Allocation)**: Extract key topics from text
- **TF-IDF vectorization**: Identify important keywords
- **Clustering**: Group similar entries by content

## 📊 API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User authentication
- `GET /logout` - User logout

### Journal
- `GET /journal/` - List journal entries
- `POST /journal/new` - Create new entry
- `GET /journal/<id>` - View specific entry

### Mood Tracking
- `GET /mood/` - List mood entries
- `POST /mood/new` - Create mood entry

### Tasks & Goals
- `GET /tasks/` - List tasks
- `POST /tasks/new` - Create task
- `GET /goals/` - List goals
- `POST /goals/new` - Create goal

### ML Services
- `GET /ml/insights` - View AI insights
- `POST /ml/sentiment_analysis` - Analyze text sentiment

## 🐳 Docker Services

The application runs in multiple containers:

- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **web**: Flask web application
- **celery_worker**: Background task processing
- **celery_beat**: Scheduled task management
- **nginx**: Reverse proxy (optional)

## 📈 Monitoring & Logging

- **Application logs**: Stored in `./logs/` directory
- **Database logs**: PostgreSQL logs via Docker
- **Celery logs**: Background task processing logs
- **Health checks**: Container health monitoring

## 🔒 Security Features

- **Password hashing**: Secure password storage with bcrypt
- **Session management**: Flask-Login for user sessions
- **CSRF protection**: Built-in CSRF token validation
- **Input validation**: Comprehensive form validation
- **SQL injection protection**: SQLAlchemy ORM protection

## 🚀 Deployment

### Production Considerations

1. **Environment variables**: Use secure, production-ready values
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **SSL/TLS**: Enable HTTPS with proper certificates
5. **Monitoring**: Implement application monitoring
6. **Backup**: Regular database backups

### Scaling

- **Horizontal scaling**: Multiple web containers behind load balancer
- **Database**: Read replicas for read-heavy operations
- **Caching**: Redis cluster for high availability
- **CDN**: Static asset delivery optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Hugging Face**: BERT models and transformers
- **spaCy**: Natural language processing
- **Bootstrap**: UI framework
- **Chart.js**: Data visualization

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Contact: support@mindtrack-ai.com
- Documentation: https://docs.mindtrack-ai.com

---

**MindTrack AI** - Track Your Mind, Understand Your Soul 🧠✨


