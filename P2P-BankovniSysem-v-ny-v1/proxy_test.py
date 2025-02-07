import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'proxy_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ProxyTest')

async def send_command(host: str, port: int, command: str) -> str:
    """Send a command to a bank and return the response"""
    try:
        reader, writer = await asyncio.open_connection(host, port)
        logger.info(f"Sending to {host}:{port}: {command}")
        
        writer.write(f"{command}\n".encode())
        await writer.drain()
        
        response = await asyncio.wait_for(
            reader.readline(),
            timeout=5.0
        )
        result = response.decode().strip()
        logger.info(f"Received from {host}:{port}: {result}")
        
        writer.close()
        await writer.wait_closed()
        return result
    except Exception as e:
        logger.error(f"Command failed {host}:{port} - {command}: {str(e)}")
        return f"ER {str(e)}"

async def test_proxy_functionality():
    # Bank configurations
    BANK1 = ("127.0.0.1", 65525)
    BANK2 = ("127.0.0.1", 65526)
    
    logger.info("=== Starting Proxy Functionality Test ===")
    
    try:
        # Test 1: Bank Availability
        logger.info("\nTest 1/5: Checking Bank Availability...")
        bank1_bc = await send_command(BANK1[0], BANK1[1], "BC")
        bank2_bc = await send_command(BANK2[0], BANK2[1], "BC")
        
        if not bank1_bc.startswith("BC") or not bank2_bc.startswith("BC"):
            logger.error("FAIL: One or both banks are not responding!")
            return
        logger.info("PASS: Both banks are responsive")

        # Test 2: Account Creation
        logger.info("\nTest 2/5: Creating Test Accounts...")
        acc1_response = await send_command(BANK1[0], BANK1[1], "AC")
        if not acc1_response.startswith("AC"):
            logger.error(f"FAIL: Could not create account on Bank1: {acc1_response}")
            return
            
        acc2_response = await send_command(BANK2[0], BANK2[1], "AC")
        if not acc2_response.startswith("AC"):
            logger.error(f"FAIL: Could not create account on Bank2: {acc2_response}")
            return
            
        account1 = acc1_response.split()[1]
        account2 = acc2_response.split()[1]
        logger.info(f"Created accounts: Bank1: {account1}, Bank2: {account2}")

        # Test 3: Proxy Deposit Test
        logger.info("\nTest 3/5: Testing Cross-Bank Deposit...")
        # Try to deposit to Bank2's account through Bank1
        deposit_result = await send_command(BANK1[0], BANK1[1], f"AD {account2} 1000")
        logger.info(f"Cross-bank deposit result: {deposit_result}")
        
        # Verify deposit succeeded
        balance_check = await send_command(BANK2[0], BANK2[1], f"AB {account2}")
        logger.info(f"Balance after deposit: {balance_check}")
        
        if not deposit_result.startswith("AD") or not balance_check.startswith("AB 1000"):
            logger.error("FAIL: Cross-bank deposit test failed")
            return
        logger.info("PASS: Cross-bank deposit successful")

        # Test 4: Proxy Withdrawal Test
        logger.info("\nTest 4/5: Testing Cross-Bank Withdrawal...")
        # Try to withdraw from Bank2's account through Bank1
        withdraw_result = await send_command(BANK1[0], BANK1[1], f"AW {account2} 500")
        logger.info(f"Cross-bank withdrawal result: {withdraw_result}")
        
        # Verify withdrawal succeeded
        balance_check = await send_command(BANK2[0], BANK2[1], f"AB {account2}")
        logger.info(f"Balance after withdrawal: {balance_check}")
        
        if not withdraw_result.startswith("AW") or not balance_check.startswith("AB 500"):
            logger.error("FAIL: Cross-bank withdrawal test failed")
            return
        logger.info("PASS: Cross-bank withdrawal successful")

        # Test 5: Error Cases
        logger.info("\nTest 5/5: Testing Error Cases...")
        
        # Test insufficient funds
        big_withdrawal = await send_command(BANK1[0], BANK1[1], f"AW {account2} 100000")
        if not big_withdrawal.startswith("ER"):
            logger.error("FAIL: Large withdrawal should have failed")
            return
        
        # Test invalid account
        invalid_acc = f"99999/{BANK2[0]}"
        invalid_check = await send_command(BANK1[0], BANK1[1], f"AB {invalid_acc}")
        if not invalid_check.startswith("ER"):
            logger.error("FAIL: Invalid account check should have failed")
            return
        
        logger.info("PASS: Error cases handled correctly")
        
        logger.info("\n=== All Proxy Tests Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(test_proxy_functionality())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")