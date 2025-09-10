import asyncpg
import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseManager:

    def __init__(self):
        self.pool = None
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD', 'root@123')
            host = os.getenv('POSTGRES_HOST', 'localhost')
            port = os.getenv('POSTGRES_PORT', '5432')
            database = os.getenv('POSTGRES_DB', 'postgres')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    async def init_pool(self):
        """Initialize asyncpg connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={'application_name': 'maha_jal_chatbot'}
            )
            # Test connection immediately
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"✅ Database connection pool initialized: {version}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise Exception("Database pool initialization failed")

    async def close_pool(self):
        """Close the connection pool gracefully"""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Database connection pool closed")
    
    async def get_grievance_status_by_unique_number(self, grievance_unique_number: str) -> Optional[Dict[str, Any]]:
        if not self.pool:
            logger.error("Database pool not initialized")
            return None
        try:
            async with self.pool.acquire() as connection:
                query = '''
                SELECT gd.*, g.grievance_unique_number
                FROM public.grievance_detail2 gd
                INNER JOIN public.grievances g ON gd.grievance_id = g.id
                WHERE g.grievance_unique_number = $1
                '''
                result = await connection.fetchrow(query, grievance_unique_number)
            if result:
                return dict(result)
            else:
                return None
        except Exception as e:
            logger.error(f"DB error fetching by unique_number: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test database connectivity"""
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error("Database connection test failed:", exc_info=True)
            return False

    async def get_database_info(self) -> Dict[str, Any]:
        """Get database and pool information"""
        if not self.pool:
            return {"connected": False}
        try:
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                db_name = await conn.fetchval("SELECT current_database()")
                user = await conn.fetchval("SELECT current_user")
                try:
                    conn_count = await conn.fetchval("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'")
                except Exception:
                    conn_count = 0
                # Pool info (using internal attributes with fallback)
                pool_info = {}
                try:
                    pool_info = {
                        "pool_max_size": getattr(self.pool, '_maxsize', 'unknown'),
                        "pool_min_size": getattr(self.pool, '_minsize', 'unknown'),
                        "pool_current_size": len(getattr(self.pool, '_con', []))
                            if hasattr(self.pool, '_con') else 'unknown'
                    }
                except Exception:
                    pool_info = {"pool_info": "unavailable"}
                return {
                    "connected": True,
                    "database_name": db_name,
                    "user": user,
                    "version": version,
                    "active_connections": conn_count,
                    **pool_info
                }
        except Exception as e:
            logger.error("Error getting database info:", exc_info=True)
            return {"connected": False, "error": str(e)}

    async def get_table_list(self) -> List[str]:
        """List all tables in public schema"""
        if not self.pool:
            return []
        try:
            async with self.pool.acquire() as conn:
                return [
                    row['table_name']
                    for row in await conn.fetch(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = 'public' ORDER BY table_name"
                    )
                ]
        except Exception as e:
            logger.error("Error getting table list:", exc_info=True)
            return []

    async def check_table_structure(self, table_name: str) -> List[str]:
        """List columns in a table"""
        if not self.pool:
            return []
        try:
            async with self.pool.acquire() as conn:
                return [
                    row['column_name']
                    for row in await conn.fetch(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = $1 AND table_schema = 'public' "
                        "ORDER BY ordinal_position", table_name
                    )
                ]
        except Exception as e:
            logger.error(f"Error checking structure for {table_name}:", exc_info=True)
            return []

# --- Global Singleton Manager ---
db_manager = DatabaseManager()

async def init_database():
    """Initialize the database connection pool"""
    await db_manager.init_pool()

async def close_database():
    """Close the database connection pool"""
    await db_manager.close_pool()

async def get_grievance_status(grievance_id: str) -> Optional[Dict[str, Any]]:
    """Get grievance status (wrapper)"""
    return await db_manager.get_grievance_status(grievance_id)

async def search_user_grievances(user_identifier: str) -> List[Dict[str, Any]]:
    """Search grievances by user (wrapper)"""
    return await db_manager.search_grievances_by_user(user_identifier)

async def get_db_statistics() -> Dict[str, Any]:
    """Get grievance statistics (wrapper)"""
    return await db_manager.get_grievance_statistics()

async def test_db_connection() -> bool:
    """Test database connection (wrapper)"""
    return await db_manager.test_connection()

async def get_db_info() -> Dict[str, Any]:
    """Get database info (wrapper)"""
    return await db_manager.get_database_info()

async def get_db_tables() -> List[str]:
    """Get list of tables (wrapper)"""
    return await db_manager.get_table_list()

async def check_table_columns(table_name: str) -> List[str]:
    """Get table columns (wrapper)"""
    return await db_manager.check_table_structure(table_name)
