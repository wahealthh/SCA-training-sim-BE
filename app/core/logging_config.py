import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """Configures Loguru for application logging with enhanced formatting."""
    # Remove default handler
    logger.remove()
    
    # Add a new handler with custom format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )
    

    
    return logger
