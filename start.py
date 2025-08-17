#!/usr/bin/env python3
"""
AI Powered Mental Health Prediction and Personalized Assistance System Startup Script
"""

import os
import sys
from app import app, db
from models import User, JournalEntry, MoodEntry, Task, Goal
from sqlalchemy import text

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
                    email='admin@ai-mental-health.com',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Admin user created (username: admin, password: admin123)")
            

            
            print("🎉 Database initialization complete!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required services are available"""
    print("🔍 Checking dependencies...")
    
    # Check SQLite database
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            print("✅ SQLite database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 AI Powered Mental Health Prediction and Personalized Assistance System Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        print("\n❌ Database initialization failed.")
        sys.exit(1)
    
    print("\n🎯 Starting AI Powered Mental Health Prediction and Personalized Assistance System...")
    print("📱 Web application will be available at: http://localhost:5000")
    print("🔑 Admin login: admin / admin123")
    print("\n💡 To stop the application, press Ctrl+C")
    print("=" * 50)
    
    # Start the Flask application
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n\n👋 AI Powered Mental Health Prediction and Personalized Assistance System stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



