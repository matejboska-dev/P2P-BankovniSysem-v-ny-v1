# bn_command.py
from typing import List
from server.db_handler import DatabaseHandler

async def handle_bn_command(host: str, args: List[str], db: DatabaseHandler) -> str:
    """
    Handle BN command - get number of clients in bank
    Args:
        host: Server's IP address
        args: [] (no arguments expected)
        db: Database handler instance
    Returns:
        "BN <count>" showing total number of accounts
    """
    if args:
        return "ER BN command takes no arguments"
    
    try:
        # Get all accounts first, then count them
        accounts = db.get_all_accounts()
        count = len(accounts)
        return f"BN {count}"
    except Exception as e:
        return f"ER Internal server error: {str(e)}"