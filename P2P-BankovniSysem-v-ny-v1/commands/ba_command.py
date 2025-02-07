# ba_command.py
from typing import List
from server.db_handler import DatabaseHandler

async def handle_ba_command(host: str, args: List[str], db: DatabaseHandler) -> str:
    """
    Handle BA command - get total amount in bank
    Args:
        host: Server's IP address
        args: [] (no arguments expected)
        db: Database handler instance
    Returns:
        "BA <total>" showing sum of all accounts
    """
    if args:
        return "ER BA command takes no arguments"
    
    try:
        # Get all accounts first, then sum their balances
        accounts = db.get_all_accounts()
        total = sum(balance for balance in accounts.values())
        return f"BA {total}"
    except Exception as e:
        return f"ER Internal server error: {str(e)}"