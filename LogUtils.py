import os
import logging
from TimeUtils import get_current_time

def initialize_log() -> None:
    '''Initialize the logging package and create the log file for this session'''
    log_dir: str = os.path.join(os.getcwd(), "Logs")
    os.makedirs(log_dir, exist_ok=True)

    log_name: str = f"log_{get_current_time()}.log"

    logging.basicConfig(filename=os.path.join(log_dir, log_name), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def print_log(text: str, is_error: bool = False, is_debug: bool = False) -> None:
    '''An extension of 'print' that logs the statement printed'''
    if is_error:
        logging.error(text)
    elif is_debug:
        logging.debug(text)
    else:
        logging.info(text)

    print(text)

def raise_log(text: str) -> None:
    '''An extension of 'raise' that logs the statement before raising it'''
    logging.error(text)
    raise Exception(text)