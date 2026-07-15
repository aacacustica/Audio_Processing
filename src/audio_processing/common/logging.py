import logging
from pathlib import Path


def setup_logging( log_dir: str | Path, name: str = "audio_processing") -> logging.Logger:
    
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter( "%(asctime)s | %(levelname)s | %(name)s | %(message)s" )
        

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler( log_dir / "campaign.log", encoding="utf-8" )
        
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger