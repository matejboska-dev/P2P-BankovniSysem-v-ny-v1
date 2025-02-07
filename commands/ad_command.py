from typing import List
import logging
from server.proxy_client import ProxyClient
from server.db_handler import DatabaseHandler

logger = logging.getLogger('BankServer')

async def handle_ad_command(host: str, args: List[str], db: DatabaseHandler, proxy_client: ProxyClient = None) -> str:
    """
    Handle AD (Account Deposit) command
    Args:
        host: This bank's IP address
        args: Command arguments [account_info amount]
        db: Database handler
        proxy_client: Optional proxy client for forwarding requests
    Returns:
        Command response string
    """
    # Validate arguments
    if len(args) != 2:
        return "ER AD command requires account and amount"

    try:
        # Parse account info and amount
        account_info, amount_str = args
        account_number, bank_ip = account_info.split('/')
        
        # Validate amount
        try:
            amount = int(amount_str)
            if amount <= 0:
                return "ER Amount must be positive"
        except ValueError:
            return "ER Invalid amount format"

        # Validate account number
        try:
            account_number = int(account_number)
            if not (10000 <= account_number <= 99999):
                return "ER Invalid account number range"
        except ValueError:
            return "ER Invalid account number format"

        # Check if this is a request for another bank
        if bank_ip != host:
            if proxy_client is None:
                return "ER Proxy functionality not available"
            
            logger.info(f"Forwarding deposit request to bank {bank_ip} for account {account_number}")
            # Forward the request to the correct bank
            response = await proxy_client.forward_command(account_info, "AD", amount)
            logger.info(f"Received response from bank {bank_ip}: {response}")
            return response

        # Handle local deposit
        logger.info(f"Processing local deposit of {amount} to account {account_number}")
        
        # Verify account exists
        current_balance = db.get_balance(account_number)
        if current_balance is None:
            return "ER Account does not exist"

        # Update balance
        new_balance = current_balance + amount
        if new_balance > 9223372036854775807:  # max value for BIGINT
            return "ER Deposit would exceed maximum balance"
            
        if db.update_balance(account_number, new_balance):
            logger.info(f"Successfully deposited {amount} to account {account_number}")
            return "AD"
        else:
            logger.error(f"Failed to update balance for account {account_number}")
            return "ER Database update failed"

    except ValueError as e:
        logger.error(f"Value error in AD command: {e}")
        return "ER Invalid input format"
    except Exception as e:
        logger.error(f"Error processing AD command: {e}")
        return f"ER Internal server error"