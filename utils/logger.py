import logging

def setup_logger(level: str, file_path: str):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(file_path),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('BankServer')