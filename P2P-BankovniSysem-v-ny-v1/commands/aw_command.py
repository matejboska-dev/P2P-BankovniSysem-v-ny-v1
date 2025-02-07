from typing import List
import logging
from server.proxy_client import ProxyClient
from server.db_handler import DatabaseHandler

logger = logging.getLogger('BankServer')

async def handle_aw_command(host: str, args: List[str], db: DatabaseHandler, proxy_client: ProxyClient = None) -> str:
    """
    Handle AW (Account Withdrawal) command
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
        return "ER AW command requires account and amount"

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
            
            logger.info(f"Forwarding withdrawal request to bank {bank_ip} for account {account_number}")
            # Forward the request to the correct bank
            response = await proxy_client.forward_command(account_info, "AW", amount)
            logger.info(f"Received response from bank {bank_ip}: {response}")
            return response

        # Handle local withdrawal
        logger.info(f"Processing local withdrawal of {amount} from account {account_number}")
        
        # Verify account exists and has sufficient funds
        current_balance = db.get_balance(account_number)
        if current_balance is None:
            return "ER Account does not exist"

        if current_balance < amount:
            logger.info(f"Insufficient funds: account {account_number} has {current_balance}, trying to withdraw {amount}")
            return "ER Insufficient funds"

        # Update balance
        new_balance = current_balance - amount
        if db.update_balance(account_number, new_balance):
            logger.info(f"Successfully withdrew {amount} from account {account_number}")
            return "AW"
        else:
            logger.error(f"Failed to update balance for account {account_number}")
            return "ER Database update failed"

    except ValueError as e:
        logger.error(f"Value error in AW command: {e}")
        return "ER Invalid input format"
    except Exception as e:
        logger.error(f"Error processing AW command: {e}")
        return f"ER Internal server error"