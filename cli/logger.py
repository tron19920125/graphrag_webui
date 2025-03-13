import logging

def get_logger(name):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/cli.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(name)

