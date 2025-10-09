"""
Main entry point for OpenHeavy application.
Initializes and runs the Flask application with all components.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import create_app, run_app
from src.log_config.config import setup_logging, log_application_startup, log_application_shutdown
from src.container import initialize_container
from src.tools import initialize_tools
from config.settings import get_settings
import logging


def main():
    """
    Main application entry point.
    Sets up logging, initializes components, and starts the server.
    """
    try:
        # Get application settings
        settings = get_settings()
        
        # Set up logging first
        setup_logging()
        
        # Log application startup
        log_application_startup()
        
        logger = logging.getLogger(__name__)
        logger.info("Starting OpenHeavy application initialization...")
        
        
        # Initialize tools system
        logger.info("Initializing tools system...")
        tools_registry = initialize_tools()
        logger.info(f"Tools initialized: {len(tools_registry.get_enabled_tools())} enabled")
        
        # Initialize dependency injection container
        logger.info("Initializing dependency injection container...")
        container = initialize_container()
        logger.info("Dependency injection container initialized")
        
        # Create Flask application
        logger.info("Creating Flask application...")
        app, socketio = create_app()
        logger.info("Flask application created successfully")
        
        # Log final startup information
        logger.info("=" * 50)
        logger.info("OpenHeavy Application Ready")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Port: {settings.FLASK_PORT}")
        logger.info(f"Debug Mode: {settings.FLASK_DEBUG}")
        logger.info("=" * 50)
        
        # Start the application
        run_app(
            app=app,
            socketio=socketio,
            port=settings.FLASK_PORT,
            debug=settings.FLASK_DEBUG
        )
        
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Application stopped by user (Ctrl+C)")
        log_application_shutdown()
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Application startup failed: {str(e)}", exc_info=True)
        log_application_shutdown()
        sys.exit(1)


def create_application():
    """
    Factory function to create the application without running it.
    Useful for testing and deployment scenarios.
    
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    # Set up logging
    setup_logging()
    
    # Initialize tools
    initialize_tools()
    
    # Initialize container
    initialize_container()
    
    # Create and return app
    return create_app()


def run_development_server():
    """
    Run the development server with debug settings.
    """
    settings = get_settings()
    
    # Override settings for development
    dev_config = {
        'DEBUG': True,
        'FLASK_DEBUG': True
    }
    
    # Set up logging for development
    setup_logging(log_level="DEBUG", log_format="text")
    
    logger = logging.getLogger(__name__)
    logger.info("Starting OpenHeavy in DEVELOPMENT mode")
    
    # Initialize components
    initialize_tools()
    initialize_container()
    
    # Create app with development config
    app, socketio = create_app(config_override=dev_config)
    
    # Run with development settings
    run_app(
        app=app,
        socketio=socketio,
        host='127.0.0.1',
        port=settings.FLASK_PORT,
        debug=True
    )


def run_production_server():
    """
    Run the production server with optimized settings.
    """
    settings = get_settings()
    
    # Override settings for production
    prod_config = {
        'DEBUG': False,
        'FLASK_DEBUG': False
    }
    
    # Set up logging for production
    setup_logging(log_level="INFO", log_format="json")
    
    logger = logging.getLogger(__name__)
    logger.info("Starting OpenHeavy in PRODUCTION mode")
    
    # Initialize components
    initialize_tools()
    initialize_container()
    
    # Create app with production config
    app, socketio = create_app(config_override=prod_config)
    
    # Run with production settings
    run_app(
        app=app,
        socketio=socketio,
        host='0.0.0.0',  # Bind to all interfaces in production
        port=settings.FLASK_PORT,
        debug=False
    )


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "dev":
            run_development_server()
        elif command == "prod":
            run_production_server()
        elif command == "test":
            # Run in test mode (minimal logging, no server start)
            setup_logging(log_level="WARNING")
            app, socketio = create_application()
            print("Application created successfully for testing")
        else:
            print("Usage: python main.py [dev|prod|test]")
            print("  dev  - Run in development mode")
            print("  prod - Run in production mode") 
            print("  test - Create app for testing")
            print("  (no args) - Run with default settings")
            sys.exit(1)
    else:
        # Default behavior - run with current settings
        main()