# ac_command.py
from typing import List
import random
import logging
from server.db_handler import DatabaseHandler

logger = logging.getLogger('BankServer')

async def handle_ac_command(host: str, args: List[str], db: DatabaseHandler) -> str:
    if args:
        return "ER AC command takes no arguments"
    
    try:
        # Generate unique account number with explicit logging
        for attempt in range(10):
            acc_number = random.randint(10000, 99999)
            
            # Log each attempt
            logger.info(f"Attempting to create account {acc_number}")
            
            if not db.account_exists(acc_number):
                result = db.create_account(acc_number, host)
                if result:
                    logger.info(f"Successfully created account {acc_number}")
                    return f"AC {acc_number}/{host}"
                else:
                    logger.error(f"Failed to create account {acc_number}")
        
        return "ER Failed to create account after multiple attempts"
    except Exception as e:
        logger.error(f"Unexpected error in account creation: {e}")
        return "ER Unexpected error"