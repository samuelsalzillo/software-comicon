"""
Main application entry point for the Comicon Stand Management System.

This module initializes the Flask application, configures database connections,
and starts background threads for queue management and backup operations.
"""
import sys
import logging
import os
import socket

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate

from src.database.init import init
from src.database.load import load
from src.batch import thread_queue
import src.routes.import_routes as routes
import src.batch.thread_backup as thread_backup
from src.database.initialize_table import db
from src.batch import treasure_hunt_php

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_python_path() -> None:
    """Add src directory to Python path if not already present."""
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        logger.info(f"Added {src_path} to Python path")


def create_app() -> Flask:
    """
    Application factory pattern for creating Flask app.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(
        '../', os.environ.get('SQLITE_DB_PATH', 'stand.db')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.urandom(12)

    # Initialize database
    db.init_app(app)

    # Initialize migrations
    migrate = Migrate(app, db)

    # Create all tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

    return app


def initialize_database() -> None:
    """Initialize and load database data."""
    try:
        init.init_database()
        load.load_database()
        logger.info("Database initialized and loaded successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def start_background_threads(app: Flask) -> None:
    """
    Start all background threads for the application.

    Args:
        app: Flask application instance
    """
    try:
        thread_queue.start_thread()
        logger.info("Queue thread started")

        thread_backup.start_thread_backup()
        logger.info("Backup thread started")

        if os.environ.get('TREASURE_HUNT_ACTIVE'):
            treasure_hunt_php.start_thread_treasure_hunt(app)
            logger.info("Treasure hunt thread started")
    except Exception as e:
        logger.error(f"Failed to start background threads: {e}", exc_info=True)
        raise


def print_server_info(port: int = 2000) -> None:
    """
    Print server startup information.

    Args:
        port: Port number the server is running on
    """
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        logger.info(f"Server running on localhost:{port}")
        logger.info(f"Server IP address: http://{ip_address}:{port}")
    except Exception as e:
        logger.warning(f"Could not determine IP address: {e}")


# Initialize Python path
setup_python_path()

# Create application instance
app = create_app()

# Initialize database
initialize_database()

# Register routes
routes.register_root(app)



if __name__ == '__main__':
    # Start background threads
    start_background_threads(app)

    # Print server information
    print_server_info(port=2000)

    # Run application
    try:
        app.run(host='0.0.0.0', port=2000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
