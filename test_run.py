from app import app

if __name__ == '__main__':
    print("Starting Flask app...")
    print("App will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5000)
