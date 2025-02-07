import asyncio
import logging
from typing import Dict
import configparser

from server.db_handler import DatabaseHandler
from server.proxy_client import ProxyClient

from commands.bc_command import handle_bc_command
from commands.ac_command import handle_ac_command
from commands.ad_command import handle_ad_command
from commands.aw_command import handle_aw_command
from commands.ab_command import handle_ab_command
from commands.ar_command import handle_ar_command
from commands.ba_command import handle_ba_command
from commands.bn_command import handle_bn_command

logger = logging.getLogger('BankServer')

class BankServer:
    def __init__(self, config: configparser.ConfigParser):
        self.host = config['NETWORK']['ip']
        self.port = int(config['NETWORK']['port'])
        self.min_port = int(config['NETWORK']['min_port'])
        self.max_port = int(config['NETWORK']['max_port'])
        
        self.command_timeout = int(config['TIMEOUTS']['command_timeout'])
        self.client_timeout = int(config['TIMEOUTS']['client_timeout'])
        
        logging_level = getattr(logging, config['LOGGING']['level'])
        logging.basicConfig(
            level=logging_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config['LOGGING']['file']),
                logging.StreamHandler()
            ]
        )
        
        self.db = DatabaseHandler(config)
        self.accounts: Dict[int, int] = {}
        self._load_accounts()
        
        self.proxy_client = ProxyClient(
            timeout=self.command_timeout,
            min_port=self.min_port,
            max_port=self.max_port
        )
        logger.info(f"Initialized proxy client with timeout {self.command_timeout}s")
        
        self.command_handlers = {
            "BC": lambda args: handle_bc_command(self.host, args),
            "AC": lambda args: handle_ac_command(self.host, args, self.db),
            "AD": lambda args: handle_ad_command(self.host, args, self.db, self.proxy_client),
            "AW": lambda args: handle_aw_command(self.host, args, self.db, self.proxy_client),
            "AB": lambda args: handle_ab_command(self.host, args, self.db, self.proxy_client),
            "AR": lambda args: handle_ar_command(self.host, args, self.db),
            "BA": lambda args: handle_ba_command(self.host, args, self.db),
            "BN": lambda args: handle_bn_command(self.host, args, self.db)
        }
        
        logger.info(f"Bank server initialized on {self.host}:{self.port}")
        
    def _load_accounts(self) -> None:
        self.accounts = self.db.get_all_accounts()
        logger.info(f"Loaded {len(self.accounts)} accounts from database")

    def _save_accounts(self) -> None:
        try:
            for acc_number, balance in self.accounts.items():
                self.db.update_account(acc_number, balance)
            logger.info("Accounts saved to database")
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")

    async def handle_command(self, command: str) -> str:
        try:
            parts = command.strip().split()
            if not parts:
                return "ER Empty command"

            cmd = parts[0].upper()
            args = parts[1:]

            if cmd not in self.command_handlers:
                return "ER Unknown command"

            # Handle proxy routing for AD, AW, AB commands
            if cmd in ['AD', 'AW', 'AB'] and len(args) > 0:
                try:
                    account_info = args[0]
                    _, bank_ip = account_info.split('/')
                    
                    if bank_ip != self.host:
                        # Forward to correct port
                        port = self.port if bank_ip == "127.0.0.1" else 65525
                        return await self.proxy_client.forward_command(account_info, cmd, 
                            int(args[1]) if len(args) > 1 else None)
                except Exception as e:
                    logger.error(f"Proxy routing error: {e}")
                    return "ER Proxy routing failed"

            # Handle local command
            handler = self.command_handlers[cmd]
            response = await handler(args)
            
            if cmd in ['AC', 'AD', 'AW', 'AR']:
                self._save_accounts()
                
            return response
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return f"ER Internal server error"

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info('peername')
        logger.info(f"New connection from {peer}")
        
        try:
            while True:
                try:
                    data = await asyncio.wait_for(
                        reader.readuntil(b'\n'),
                        timeout=self.client_timeout
                    )
                    
                    if not data:
                        break
                        
                    command = data.decode('utf-8', errors='ignore').strip()
                    if not command or command.startswith('\x1b'):
                        continue
                        
                    logger.info(f"Received command from {peer}: {command}")
                    
                    response = await self.handle_command(command)
                    writer.write(f"{response}\n".encode())
                    await writer.drain()
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for client {peer}")
                    writer.write(b"ER Timeout\n")
                    await writer.drain()
                    break
                
        except ConnectionResetError:
            logger.info(f"Client {peer} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {peer}: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.info(f"Connection with {peer} closed")

    async def start(self) -> None:
        try:
            server = await asyncio.start_server(
                self.handle_client, 
                self.host, 
                self.port
            )
            
            logger.info(f"Server running on {self.host}:{self.port}")
            
            async with server:
                await server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise