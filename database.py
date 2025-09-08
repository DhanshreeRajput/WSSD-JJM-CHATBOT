import asyncpg
import asyncio
import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            # Fallback to individual environment variables
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD', 'root@123')
            host = os.getenv('POSTGRES_HOST', 'localhost')
            port = os.getenv('POSTGRES_PORT', '5432')
            database = os.getenv('POSTGRES_DB', 'postgres')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'maha_jal_chatbot',
                }
            )
            logger.info("✅ Database connection pool initialized successfully")
            
            # Test the connection immediately
            async with self.pool.acquire() as connection:
                result = await connection.fetchval("SELECT version()")
                logger.info(f"Connected to: {result}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise

    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("🔒 Database connection pool closed")

    async def get_grievance_status(self, grievance_id: str) -> Optional[Dict[str, Any]]:
        """Get grievance status and details from the database"""
        if not self.pool:
            logger.error("Database pool not initialized")
            return None
            
        try:
            logger.info(f"Attempting to fetch grievance status for ID: {grievance_id}")
            async with self.pool.acquire() as connection:
                # Test database connection first
                await connection.fetchval('SELECT 1')
                logger.info("Database connection is working")
                
                # Get grievance details
                query = """
SELECT 
    grievance_id,
    grievance_status,
    grievance_logged_date,
    organization_name,
    grievance_name,
    sub_grievance_name,
    district_name,
    block_name,
    grampanchayat_name,
    village_name,
    resolved_date,
    resolved_user_name,
    closed_date,
    verified_user_name
FROM grievance_detail2
WHERE grievance_id = $1
   OR grievance_id LIKE '%' || $1 || '%'
"""
                
                # Execute query with cleaned grievance ID
                result = await connection.fetchrow(query, grievance_id.strip())
                
                if result:
                    logger.info(f"Found grievance data: {dict(result)}")
                    return dict(result)
                    
                logger.warning(f"No grievance found with ID: {grievance_id}")
                return None
                    
        except Exception as e:
            logger.error(f"Database error while fetching grievance {grievance_id}: {e}")
            return None

    async def search_grievances_by_user(self, user_identifier: str) -> List[Dict[str, Any]]:
        """Search grievances by user mobile number, email, or name"""
        if not self.pool:
            logger.error("Database pool not initialized")
            return []
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT DISTINCT
                        g.id,
                        g.grievance_unique_number,
                        g.citizen_name,
                        g.grievance_status,
                        g.created_at,
                        gc.grievance_name as category_name
                    FROM grievances g
                    LEFT JOIN grievance_categories gc ON g.grievance_type_id = gc.id
                    WHERE LOWER(g.mobile_number) LIKE '%' || LOWER($1) || '%'
                       OR LOWER(g.email) LIKE '%' || LOWER($1) || '%'
                       OR LOWER(g.citizen_name) LIKE '%' || LOWER($1) || '%'
                    ORDER BY g.created_at DESC
                    LIMIT 5
                """
                
                results = await connection.fetch(query, user_identifier.strip())
                
                return [
                    {
                        'grievance_id': str(result['id']),
                        'grievance_number': result['grievance_unique_number'] or f"GR{result['id']}",
                        'citizen_name': result['citizen_name'] or 'N/A',
                        'status': result['grievance_status'] or 'Pending',
                        'category': result['category_name'] or 'General',
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None
                    }
                    for result in results
                ]
                
        except Exception as e:
            logger.error(f"Database error while searching grievances for {user_identifier}: {e}")
            return []

    async def get_grievance_statistics(self) -> Dict[str, Any]:
        """Get grievance statistics from your database - FIXED BOOLEAN COMPARISON"""
        if not self.pool:
            logger.error("Database pool not initialized")
            return {}
            
        try:
            async with self.pool.acquire() as connection:
                # Get total counts - FIXED: Use boolean literal true instead of string
                total_query = "SELECT COUNT(*) as total FROM grievances WHERE is_active = true"
                total_result = await connection.fetchrow(total_query)
                
                # Get status distribution - FIXED: Use boolean literal true
                status_query = """
                    SELECT grievance_status as status, COUNT(*) as count 
                    FROM grievances 
                    WHERE grievance_status IS NOT NULL AND is_active = true
                    GROUP BY grievance_status
                    ORDER BY count DESC
                """
                status_results = await connection.fetch(status_query)
                
                # Get category distribution - FIXED: Use boolean literal true
                category_query = """
                    SELECT gc.grievance_name as category, COUNT(*) as count 
                    FROM grievances g
                    LEFT JOIN grievance_categories gc ON g.grievance_type_id = gc.id
                    WHERE g.is_active = true
                    GROUP BY gc.grievance_name
                    ORDER BY count DESC
                    LIMIT 10
                """
                category_results = await connection.fetch(category_query)
                
                # Get recent grievances count (last 30 days) - FIXED: Use boolean literal true
                recent_query = """
                    SELECT COUNT(*) as recent_count 
                    FROM grievances 
                    WHERE created_at >= NOW() - INTERVAL '30 days' AND is_active = true
                """
                recent_result = await connection.fetchrow(recent_query)
                
                # Get resolved grievances count - FIXED: Use boolean literal true
                resolved_query = """
                    SELECT COUNT(*) as resolved_count 
                    FROM grievances 
                    WHERE grievance_status IN ('Resolved', 'Closed', 'Completed') AND is_active = true
                """
                resolved_result = await connection.fetchrow(resolved_query)
                
                return {
                    'total_grievances': total_result['total'] if total_result else 0,
                    'recent_grievances_30_days': recent_result['recent_count'] if recent_result else 0,
                    'resolved_grievances': resolved_result['resolved_count'] if resolved_result else 0,
                    'status_distribution': {
                        result['status']: result['count'] 
                        for result in status_results if result['status']
                    },
                    'category_distribution': {
                        result['category']: result['count'] 
                        for result in category_results if result['category']
                    }
                }
                
        except Exception as e:
            logger.error(f"Database error while fetching statistics: {e}")
            return {"error": str(e)}

    async def test_connection(self) -> bool:
        """Test database connection"""
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as connection:
                await connection.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information with safe pool size calculation"""
        if not self.pool:
            return {"connected": False}
            
        try:
            async with self.pool.acquire() as connection:
                # Get PostgreSQL version
                version = await connection.fetchval("SELECT version()")
                
                # Get current database name
                db_name = await connection.fetchval("SELECT current_database()")
                
                # Get current user
                user = await connection.fetchval("SELECT current_user")
                
                # Get connection count
                try:
                    conn_count = await connection.fetchval("""
                        SELECT count(*) 
                        FROM pg_stat_activity 
                        WHERE state = 'active'
                    """)
                except:
                    conn_count = 0
                
                # Get pool information safely
                pool_info = {}
                if self.pool:
                    try:
                        # Use safer methods to get pool info
                        pool_info = {
                            "pool_max_size": getattr(self.pool, '_maxsize', 'unknown'),
                            "pool_min_size": getattr(self.pool, '_minsize', 'unknown'),
                            "pool_current_size": len(getattr(self.pool, '_con', [])) if hasattr(self.pool, '_con') else 'unknown'
                        }
                    except Exception as pool_error:
                        logger.warning(f"Could not get pool info: {pool_error}")
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
            logger.error(f"Error getting database info: {e}")
            return {"connected": False, "error": str(e)}

    async def get_table_list(self) -> List[str]:
        """Get list of all tables in the database"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """
                results = await connection.fetch(query)
                return [row['table_name'] for row in results]
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []

    async def check_table_structure(self, table_name: str) -> List[str]:
        """Check what columns exist in a table"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as connection:
                query = """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """
                results = await connection.fetch(query, table_name)
                return [row['column_name'] for row in results]
        except Exception as e:
            logger.error(f"Error checking table structure for {table_name}: {e}")
            return []

# Create global database manager instance
db_manager = DatabaseManager()

# Convenience functions for external use
async def init_database():
    """Initialize database connection"""
    await db_manager.init_pool()

async def close_database():
    """Close database connection"""
    await db_manager.close_pool()

async def get_grievance_status(grievance_id: str) -> Optional[Dict[str, Any]]:
    """Get grievance status - wrapper function"""
    return await db_manager.get_grievance_status(grievance_id)

async def search_user_grievances(user_identifier: str) -> List[Dict[str, Any]]:
    """Search user grievances - wrapper function"""
    return await db_manager.search_grievances_by_user(user_identifier)

async def get_db_statistics() -> Dict[str, Any]:
    """Get database statistics - wrapper function"""
    return await db_manager.get_grievance_statistics()

async def test_db_connection() -> bool:
    """Test database connection - wrapper function"""
    return await db_manager.test_connection()

async def get_db_info() -> Dict[str, Any]:
    """Get database info - wrapper function"""
    return await db_manager.get_database_info()

async def get_db_tables() -> List[str]:
    """Get database tables - wrapper function"""
    return await db_manager.get_table_list()

async def check_table_columns(table_name: str) -> List[str]:
    """Check table columns - wrapper function"""
    return await db_manager.check_table_structure(table_name)
