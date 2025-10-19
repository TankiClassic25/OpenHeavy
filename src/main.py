"""
Main entry point for OpenHeavy application.
Initializes and runs the Flask application with all components.
"""
import sys
from pathlib import Path
from typing import Optional, Tuple
import logging

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_socketio import SocketIO

from src.api.app import create_app, run_app
from src.log_config.config import (
    setup_logging,
    log_application_startup,
    log_application_shutdown,
)
from src.container import Container, initialize_container
from src.tools import initialize_tools
from src.tools.registry import ToolRegistry
from config.settings import Settings, get_settings


BootstrapResult = Tuple[Flask, SocketIO, Container, ToolRegistry, Settings]


def bootstrap_application(
    *,
    config_override: Optional[dict] = None,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    emit_startup_log: bool = True,
) -> BootstrapResult:
    """Initialize logging, tools, container, and create the Flask app."""

    settings = get_settings()

    # Configure logging first so subsequent steps emit structured logs
    setup_logging(log_level=log_level, log_format=log_format)

    if emit_startup_log:
        log_application_startup()

    logger = logging.getLogger(__name__)
    logger.info("Starting OpenHeavy application initialization...")

    logger.info("Initializing tools system...")
    tools_registry = initialize_tools()
    logger.info(
        "Tools initialized: %d enabled",
        len(tools_registry.get_enabled_tools()),
    )

    logger.info("Initializing dependency injection container...")
    container = initialize_container()
    logger.info("Dependency injection container initialized")

    logger.info("Creating Flask application...")
    app, socketio = create_app(
        config_override=config_override,
        container=container,
    )
    logger.info("Flask application created successfully")

    return app, socketio, container, tools_registry, settings


def main() -> None:
    """
    Main application entry point.
    Sets up logging, initializes components, and starts the server.
    """

    try:
        app, socketio, _container, tools_registry, settings = bootstrap_application()

        logger = logging.getLogger(__name__)
        logger.info("=" * 50)
        logger.info("OpenHeavy Application Ready")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Port: {settings.FLASK_PORT}")
        logger.info(f"Debug Mode: {settings.FLASK_DEBUG}")
        logger.info("=" * 50)
        logger.info(
            "Available tools: %d total, %d enabled",
            len(tools_registry.get_all_tools()),
            len(tools_registry.get_enabled_tools()),
        )

        run_app(
            app=app,
            socketio=socketio,
            port=settings.FLASK_PORT,
            debug=settings.FLASK_DEBUG,
        )

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Application stopped by user (Ctrl+C)")
        log_application_shutdown()

    except Exception as exc:  # pragma: no cover - startup failures should exit
        logger = logging.getLogger(__name__)
        logger.error("Application startup failed: %s", exc, exc_info=True)
        log_application_shutdown()
        sys.exit(1)


def create_application() -> Tuple[Flask, SocketIO]:
    """
    Factory function to create the application without running it.
    Useful for testing and deployment scenarios.

    Returns:
        Tuple of (Flask app, SocketIO instance)
    """

    app, socketio, *_ = bootstrap_application(emit_startup_log=False)
    return app, socketio


def run_development_server() -> None:
    """Run the development server with debug settings."""

    settings = get_settings()

    # Override settings for development
    dev_config = {
        "DEBUG": True,
        "FLASK_DEBUG": True,
    }

    logger = logging.getLogger(__name__)
    logger.info("Starting OpenHeavy in DEVELOPMENT mode")

    app, socketio, *_ = bootstrap_application(
        config_override=dev_config,
        log_level="DEBUG",
        log_format="text",
    )

    run_app(
        app=app,
        socketio=socketio,
        host="127.0.0.1",
        port=settings.FLASK_PORT,
        debug=True,
    )


def run_production_server() -> None:
    """Run the production server with optimized settings."""

    settings = get_settings()

    # Override settings for production
    prod_config = {
        "DEBUG": False,
        "FLASK_DEBUG": False,
    }

    logger = logging.getLogger(__name__)
    logger.info("Starting OpenHeavy in PRODUCTION mode")

    app, socketio, *_ = bootstrap_application(
        config_override=prod_config,
        log_level="INFO",
        log_format="json",
    )

    run_app(
        app=app,
        socketio=socketio,
        host="0.0.0.0",  # Bind to all interfaces in production
        port=settings.FLASK_PORT,
        debug=False,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "dev":
            run_development_server()
        elif command == "prod":
            run_production_server()
        elif command == "test":
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
        main()
