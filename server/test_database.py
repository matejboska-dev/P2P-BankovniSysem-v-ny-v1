import logging
import configparser
from db_handler import DatabaseHandler

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger('DatabaseTest')

def load_test_config():
    """Load configuration for testing"""
    config = configparser.ConfigParser()
    config.read('config.conf')
    return config

def test_database_connection():
    """Test basic database connectivity"""
    logger.info("Testing database connection...")
    try:
        config = load_test_config()
        db = DatabaseHandler(config)
        logger.info("✅ Database connection successful")
        return db
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def test_account_operations(db):
    """Test basic account operations"""
    test_account = 12345
    
    logger.info("\nTesting account operations:")
    
    # Test account creation
    try:
        logger.info(f"Creating account {test_account}...")
        db.update_account(test_account, 0)
        logger.info("✅ Account creation successful")
    except Exception as e:
        logger.error(f"❌ Account creation failed: {e}")
        return
    
    # Test account balance update
    try:
        logger.info(f"Updating account {test_account} balance...")
        db.update_account(test_account, 1000)
        accounts = db.get_all_accounts()
        if accounts[test_account] == 1000:
            logger.info("✅ Account balance update successful")
        else:
            logger.error("❌ Account balance update failed")
    except Exception as e:
        logger.error(f"❌ Account balance update failed: {e}")
        return
    
    # Test account retrieval
    try:
        logger.info("Testing account retrieval...")
        accounts = db.get_all_accounts()
        if test_account in accounts:
            logger.info("✅ Account retrieval successful")
        else:
            logger.error("❌ Account retrieval failed")
    except Exception as e:
        logger.error(f"❌ Account retrieval failed: {e}")
        return
    
    # Test account deletion
    try:
        logger.info(f"Deleting account {test_account}...")
        db.delete_account(test_account)
        accounts = db.get_all_accounts()
        if test_account not in accounts:
            logger.info("✅ Account deletion successful")
        else:
            logger.error("❌ Account deletion failed")
    except Exception as e:
        logger.error(f"❌ Account deletion failed: {e}")
        return

def main():
    logger.info("Starting database tests...")
    
    # Test connection
    db = test_database_connection()
    if db is None:
        return
    
    # Test operations
    test_account_operations(db)
    
    logger.info("\nDatabase tests completed")

if __name__ == "__main__":
    main()