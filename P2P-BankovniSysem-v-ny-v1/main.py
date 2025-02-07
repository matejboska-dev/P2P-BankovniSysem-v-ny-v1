import asyncio
import configparser
import argparse
from server.bank_server import BankServer

def load_config(config_path: str = "config.conf") -> configparser.ConfigParser:
    """Load configuration from file"""
    config = configparser.ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found")
    return config

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Bank Server')
    parser.add_argument('--config', 
                      default='config.conf',
                      help='Path to configuration file')
    return parser.parse_args()

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = parse_arguments()
        print(f"Loading configuration from: {args.config}")
        
        # Load configuration
        config = load_config(args.config)
        
        # Create and start server
        bank_server = BankServer(config)
        asyncio.run(bank_server.start())
        
    except KeyboardInterrupt:
        print("Server terminated by user")
    except FileNotFoundError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")