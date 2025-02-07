from typing import List
import logging
from server.proxy_client import ProxyClient
from server.db_handler import DatabaseHandler

logger = logging.getLogger('BankServer')

async def handle_ab_command(host: str, args: List[str], db: DatabaseHandler, proxy_client: ProxyClient = None) -> str:
    """
    Handle AB (Account Balance) command
    Args:
        host: This bank's IP address
        args: Command arguments [account_info]
        db: Database handler
        proxy_client: Optional proxy client for forwarding requests
    Returns:
        Command response string
    """
    # Validate arguments
    if len(args) != 1:
        return "ER AB command requires account"

    try:
        # Parse account info
        account_info = args[0]
        account_number, bank_ip = account_info.split('/')
        
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
            
            logger.info(f"Forwarding balance request to bank {bank_ip} for account {account_number}")
            # Forward the request to the correct bank
            response = await proxy_client.forward_command(account_info, "AB")
            logger.info(f"Received response from bank {bank_ip}: {response}")
            return response

        # Handle local balance check
        logger.info(f"Checking local balance for account {account_number}")
        
        # Get account balance
        balance = db.get_balance(account_number)
        if balance is None:
            return "ER Account does not exist"

        logger.info(f"Balance for account {account_number}: {balance}")
        return f"AB {balance}"

    except ValueError as e:
        logger.error(f"Value error in AB command: {e}")
        return "ER Invalid input format"
    except Exception as e:
        logger.error(f"Error processing AB command: {e}")
        return f"ER Internal server error"