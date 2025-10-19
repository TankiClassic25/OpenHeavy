"""
Flask application factory.
Creates and configures the Flask application with all extensions.
"""
import os
from typing import Optional

from flask import Flask, render_template
from flask_socketio import SocketIO

from config.settings import get_settings
from src.container import Container, initialize_container
from src.utils.error_handlers import (
    register_flask_error_handlers,
    register_socketio_error_handlers,
)
import logging


logger = logging.getLogger(__name__)


def create_app(
    config_override: Optional[dict] = None,
    *,
    container: Optional[Container] = None,
) -> tuple[Flask, SocketIO]:
    """
    Create and configure Flask application with SocketIO.
    
    Args:
        config_override: Optional configuration overrides
        
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    # Create Flask app
    app = Flask(__name__, template_folder='../../frontend/templates')
    
    # Load configuration
    settings = get_settings()
    
    # Configure Flask
    app.config['SECRET_KEY'] = settings.FLASK_SECRET_KEY
    app.config['DEBUG'] = settings.FLASK_DEBUG
    
    # Apply config overrides if provided
    if config_override:
        app.config.update(config_override)
    
    logger.info(f"Created Flask app in {settings.ENVIRONMENT} mode")
    
    # Initialize dependency injection container
    if container is None:
        container = initialize_container()
    
    # Store container in app for access in routes
    app.container = container
    
    # Create SocketIO instance with threading mode (avoid eventlet conflicts)
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='threading'  # Force threading mode instead of eventlet
    )
    
    # Register error handlers
    register_flask_error_handlers(app)
    register_socketio_error_handlers(socketio)
    
    # Register routes
    register_routes(app)
    
    # Register WebSocket handlers
    register_websocket_handlers(socketio, container)
    
    logger.info("Flask application configuration completed")
    
    return app, socketio


def register_routes(app: Flask) -> None:
    """
    Register HTTP routes.
    
    Args:
        app: Flask application
    """
    @app.route('/')
    def index():
        """Main page route - preserves original behavior"""
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy', 'service': 'openheavy'}
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint with service information"""
        from src.tools.registry import get_tool_registry
        
        tool_registry = get_tool_registry()
        enabled_tools = tool_registry.get_enabled_tools()
        
        return {
            'status': 'running',
            'service': 'openheavy',
            'tools': {
                'total': len(tool_registry.get_all_tools()),
                'enabled': len(enabled_tools),
                'available': [tool.name for tool in enabled_tools]
            }
        }
    
    logger.info("HTTP routes registered")


def register_websocket_handlers(socketio: SocketIO, container) -> None:
    """
    Register WebSocket event handlers.
    
    Args:
        socketio: SocketIO instance
        container: Dependency injection container
    """
    from src.api.websocket.handlers import register_handlers
    
    register_handlers(socketio, container)
    logger.info("WebSocket handlers registered")


def configure_logging(app: Flask) -> None:
    """
    Configure application logging.
    
    Args:
        app: Flask application
    """
    settings = get_settings()
    
    # Configure logging level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure Flask logging
    if not app.debug:
        app.logger.setLevel(log_level)
    
    logger.info(f"Logging configured at {settings.LOG_LEVEL} level")


def run_app(
    app: Flask = None, 
    socketio: SocketIO = None, 
    host: str = '127.0.0.1', 
    port: int = None,
    debug: bool = None
) -> None:
    """
    Run the Flask application with SocketIO.
    
    Args:
        app: Flask application (will create if None)
        socketio: SocketIO instance (will create if None)
        host: Host to bind to
        port: Port to bind to
        debug: Debug mode
    """
    # Create app if not provided
    if app is None or socketio is None:
        app, socketio = create_app()
    
    # Get settings for defaults
    settings = get_settings()
    
    if port is None:
        port = settings.FLASK_PORT
    
    if debug is None:
        debug = settings.FLASK_DEBUG
    
    # Configure logging
    configure_logging(app)
    
    logger.info(f"Starting OpenHeavy server on {host}:{port}")
    
    try:
        # Run with SocketIO - preserves original behavior
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=debug,
            allow_unsafe_werkzeug=True  # For development
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise


# Factory function for backward compatibility
def create_application() -> tuple[Flask, SocketIO]:
    """
    Create application - alias for create_app for backward compatibility.
    
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    return create_app()