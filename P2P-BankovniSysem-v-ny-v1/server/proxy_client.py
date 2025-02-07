import asyncio
import logging
from typing import Optional, Dict, List

logger = logging.getLogger('BankServer')

class ProxyClient:
    def __init__(self, timeout: int = 5, min_port: int = 65525, max_port: int = 65535):
        self.timeout = timeout
        self.min_port = min_port
        self.max_port = max_port
        self.connection_cache: Dict[str, int] = {}
        
    async def try_port(self, bank_ip: str, port: int) -> Optional[int]:
        """Try to connect to a specific port"""
        try:
            reader, writer = await asyncio.open_connection(bank_ip, port)
            writer.write(b"BC\n")
            await writer.drain()
            
            response = await asyncio.wait_for(reader.readline(), timeout=1.5)
            writer.close()
            await writer.wait_closed()
            
            if response.startswith(b"BC"):
                return port
        except:
            pass
        return None

    async def find_bank_port(self, bank_ip: str) -> Optional[int]:
        """Find correct port using parallel scanning"""
        # Check cache first
        if bank_ip in self.connection_cache:
            if await self.try_port(bank_ip, self.connection_cache[bank_ip]):
                return self.connection_cache[bank_ip]
            del self.connection_cache[bank_ip]

        # Try all ports in parallel
        tasks = []
        for port in range(self.min_port, self.max_port + 1):
            tasks.append(self.try_port(bank_ip, port))
        
        # Wait for first successful response or all failures
        for result in asyncio.as_completed(tasks):
            port = await result
            if port is not None:
                self.connection_cache[bank_ip] = port
                return port
        
        return None

    async def forward_command(self, account_info: str, command: str, amount: Optional[int] = None) -> str:
        """Forward command to appropriate bank"""
        try:
            acc_number, bank_ip = account_info.split('/')
            
            # Find correct port
            port = await self.find_bank_port(bank_ip)
            if port is None:
                return "ER Cannot connect to target bank"
            
            # Forward command
            reader, writer = await asyncio.open_connection(bank_ip, port)
            
            # Construct command
            cmd = f"{command} {account_info}"
            if amount is not None:
                cmd += f" {amount}"
            cmd += "\n"
            
            # Send and wait for response
            writer.write(cmd.encode())
            await writer.drain()
            
            response = await asyncio.wait_for(
                reader.readline(),
                timeout=self.timeout
            )
            
            result = response.decode().strip()
            
            writer.close()
            await writer.wait_closed()
            
            return result
            
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return f"ER Proxy error: {str(e)}"