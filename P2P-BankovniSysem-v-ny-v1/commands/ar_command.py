# AR <account>/<ip> - returns AR

# ar_command.py

from typing import List, Dict
import re
from server.db_handler import DatabaseHandler

async def handle_ar_command(host: str, args: List[str], db: DatabaseHandler) -> str:
    if len(args) != 1:
        return "ER AR command requires account"
        
    account_info = args[0]
    try:
        acc_number, bank_ip = account_info.split('/')
        acc_number = int(acc_number)
            
        if bank_ip != host:
            return "ER Wrong bank code"
            
        balance = db.get_balance(acc_number)
        if balance is None:
            return "ER Account does not exist"
            
        if balance != 0:
            return "ER Cannot remove account with non-zero balance"
            
        if db.remove_account(acc_number):
            return "AR"
        return "ER Failed to remove account"
            
    except ValueError:
        return "ER Invalid number format"