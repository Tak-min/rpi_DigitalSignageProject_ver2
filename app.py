# To install Flask, run: pip install Flask
from flask import Flask, render_template

# Initialize the Flask application
app = Flask(__name__)

@app.route('/')
def index():
    """Renders and returns the main HTML page."""
    return render_template('index.html')

if __name__ == '__main__':
    # Runs the application, making it accessible on the local network
    app.run(host='0.0.0.0', port=5000, debug=True)