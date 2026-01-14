from flask import Flask
from flask_cors import CORS
from flask_caching import Cache
from routes import api_bp

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    #------------------
print("🔍 Starting app... loading blueprint...")

    try:
        from routes import api_bp
        app.register_blueprint(api_bp, url_prefix="/api")
        print("✅ Blueprint registered successfully!")
    except Exception as e:
        print("❌ Blueprint failed to register:", e)
#--------------------
    # Configure caching
    cache_config = {
        'CACHE_TYPE': 'simple',  # In-memory cache (works for single instance)
        'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes cache timeout
    }
    app.config.from_mapping(cache_config)
    cache = Cache(app)
    
    # Make cache available to routes
    app.cache = cache

    # Register Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Dynamic Pricing API is running!"
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint for monitoring and keep-alive"""
        return {
            'status': 'healthy',
            'service': 'Dynamic Pricing API',
            'message': 'Server is running'
        }, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
