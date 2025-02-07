# db_handler.py
import pyodbc
import logging
from typing import Dict, Optional

logger = logging.getLogger('BankServer')

class DatabaseHandler:
    def __init__(self, config):
        self.connection_string = (
            f"DRIVER={{{config['DATABASE']['driver']}}};"
            f"SERVER={config['DATABASE']['server']};"
            f"DATABASE={config['DATABASE']['database']};"
            f"UID={config['DATABASE']['username']};"
            f"PWD={config['DATABASE']['password']}"
        )
        self.connection = None
        self._connect()

    def _connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            self._create_table()
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _create_table(self):
        create_table_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='bank_accounts' AND xtype='U')
        CREATE TABLE bank_accounts (
            account_number INT PRIMARY KEY,
            balance BIGINT NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            last_modified DATETIME DEFAULT GETDATE()
        )
        """
        with self.connection.cursor() as cursor:
            cursor.execute(create_table_query)
            self.connection.commit()

    def create_account(self, account_number: int, bank_ip: str) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO bank_accounts (account_number, balance)
                    VALUES (?, 0)
                """, (account_number,))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Account creation error: {e}")
            return False

    def get_bank_ip(self, account_number: int) -> Optional[str]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT bank_ip FROM bank_accounts WHERE account_number = ?", (account_number,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get bank IP: {e}")
            return None

    def get_balance(self, account_number: int) -> Optional[int]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT balance FROM bank_accounts WHERE account_number = ?", (account_number,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None

    def get_all_accounts(self) -> Dict[int, int]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT account_number, balance FROM bank_accounts")
                return {row.account_number: row.balance for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return {}

    def update_account(self, account_number: int, balance: int) -> bool:
        """Alias for update_balance"""
        return self.update_balance(account_number, balance)

    def update_balance(self, account_number: int, amount: int) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE bank_accounts SET balance = ?, last_modified = GETDATE() WHERE account_number = ?",
                    (amount, account_number)
                )
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update balance: {e}")
            return False

    def account_exists(self, account_number: int) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM bank_accounts WHERE account_number = ?", (account_number,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check account existence: {e}")
            return False

    def remove_account(self, account_number: int) -> bool:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM bank_accounts WHERE account_number = ?", (account_number,))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to remove account: {e}")
            return False