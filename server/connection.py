import asyncio
import logging
from typing import Optional, Tuple

logger = logging.getLogger('BankServer')

class BankConnection:
    """Handles connections to other banks"""
    
    def __init__(self, timeout: int = 5):
        """
        Initialize connection handler
        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def connect(self, host: str, port: int) -> bool:
        """
        Establish connection to another bank
        Args:
            host: Bank's IP address
            port: Bank's port
        Returns:
            bool: True if connection successful
        """
        try:
            self._reader, self._writer = await asyncio.open_connection(host, port)
            logger.info(f"Connected to bank at {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to bank at {host}:{port}: {e}")
            return False

    async def disconnect(self):
        """Close the connection"""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

    async def send_command(self, host: str, port: int, command: str) -> Optional[str]:
        """
        Send command to another bank and get response
        Args:
            host: Bank's IP address
            port: Bank's port
            command: Command to send
        Returns:
            Optional[str]: Response from bank or None if failed
        """
        try:
            # Connect if not connected
            if not self._writer or self._writer.is_closing():
                success = await self.connect(host, port)
                if not success:
                    return "ER Connection failed"

            # Send command
            self._writer.write(f"{command}\n".encode())
            await self._writer.drain()
            logger.info(f"Sent command to {host}: {command}")

            # Wait for response
            try:
                data = await asyncio.wait_for(
                    self._reader.readuntil(b'\n'),
                    timeout=self.timeout
                )
                response = data.decode().strip()
                logger.info(f"Received response from {host}: {response}")
                return response

            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response from {host}")
                return "ER Response timeout"

        except Exception as e:
            logger.error(f"Error in send_command: {e}")
            return "ER Command failed"

        finally:
            await self.disconnect()

    @staticmethod
    async def parse_bank_address(account_info: str) -> Tuple[Optional[str], Optional[int]]:
        """
        Parse bank address from account info (number/ip)
        Args:
            account_info: String in format "number/ip"
        Returns:
            Tuple of (host, account_number) or (None, None) if invalid
        """
        try:
            acc_number, bank = account_info.split('/')
            return bank, int(acc_number)
        except ValueError:
            logger.error(f"Invalid account info format: {account_info}")
            return None, None

    async def proxy_command(self, command: str, account_info: str, *args) -> str:
        """
        Proxy command to appropriate bank
        Args:
            command: Command type (AD, AW, AB)
            account_info: Account information (number/ip)
            args: Additional command arguments
        Returns:
            str: Response from remote bank or error message
        """
        bank_host, _ = await self.parse_bank_address(account_info)
        if not bank_host:
            return "ER Invalid bank address"

        # Construct full command
        full_command = f"{command} {account_info}"
        if args:
            full_command += f" {' '.join(map(str, args))}"

        return await self.send_command(bank_host, 65525, full_command)