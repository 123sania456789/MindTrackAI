#!/usr/bin/env python3
"""
MindTrack AI Startup Script
Initializes the database and starts the Flask application
"""

import os
import sys
from app import app, db
from models import User, JournalEntry, MoodEntry, Task, Goal, MLModel

def init_database():
    """Initialize the database with tables"""
    print("🔧 Initializing database...")
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                # Create admin user
                from werkzeug.security import generate_password_hash
                admin_user = User(
                    username='admin',
                    email='admin@mindtrack-ai.com',
                    password_hash=generate_password_hash('admin123'),
                    first_name='Admin',
                    last_name='User'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created (username: admin, password: admin123)")
            
            # Check if ML model records exist
            if not MLModel.query.first():
                # Create default ML model records
                models = [
                    MLModel(
                        name='sentiment_analysis',
                        version='1.0.0',
                        model_type='sentiment',
                        accuracy=0.85,
                        is_active=True
                    ),
                    MLModel(
                        name='emotion_detection',
                        version='1.0.0',
                        model_type='emotion',
                        accuracy=0.78,
                        is_active=True
                    ),
                    MLModel(
                        name='topic_modeling',
                        version='1.0.0',
                        model_type='topic_modeling',
                        accuracy=0.82,
                        is_active=True
                    )
                ]
                
                for model in models:
                    db.session.add(model)
                
                db.session.commit()
                print("✅ ML model records created")
            
            print("🎉 Database initialization complete!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required services are available"""
    print("🔍 Checking dependencies...")
    
    # Check PostgreSQL connection
    try:
        with app.app_context():
            db.engine.execute('SELECT 1')
            print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Make sure PostgreSQL is running and accessible")
        return False
    
    # Check Redis connection
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running and accessible")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 MindTrack AI Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        print("\n❌ Database initialization failed.")
        sys.exit(1)
    
    print("\n🎯 Starting MindTrack AI...")
    print("📱 Web application will be available at: http://localhost:5000")
    print("🔑 Admin login: admin / admin123")
    print("\n💡 To stop the application, press Ctrl+C")
    print("=" * 50)
    
    # Start the Flask application
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n\n👋 MindTrack AI stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()


