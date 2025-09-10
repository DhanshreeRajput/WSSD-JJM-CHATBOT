import asyncpg
import asyncio
import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Set
from enum import Enum

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseManager:

    def __init__(self):
        self.pool = None
        self.database_url = os.getenv('DATABASE_URL')
        # Fallback to individual environment variables
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

    async def get_grievance_status(self, grievance_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed grievance status and information from grievance_detail2.

        Args:
            grievance_id: The grievance identifier to fetch details for.

        Returns:
            Dict of grievance details (all fields from grievance_detail2) if found,
            None if not found or on error.
        """
        if not self.pool:
            logger.error("Database pool not initialized")
            return None

        query = """
        SELECT
            grievance_id,
            grievance_status,
            organization_name,
            district_name,
            block_name,
            grampanchayat_name,
            habitation_name,
            village_name,
            sub_grievance_name,
            citizen_name,
            mobile_number,
            landline_number,
            aadhar_number,
            address,
            pincode,
            grievance_logged_date,
            resolved_date,
            resolved_user_name,
            closed_date,
            verified_user_name,
            citizen_feedback,
            rating,
            district_id,
            block_id,
            grampanchayat_id,
            village_id,
            subgrievance_type_id,
            grievance_type_id,
            resolvedby_user_id,
            last_update_at,
            accepted_by_hierarchy,
            assigned_to_hierarchy
        FROM grievance_detail2
        WHERE grievance_id = $1 OR grievance_id LIKE '%' || $1 || '%'
        """
        try:
            async with self.pool.acquire() as conn:
                # Test connection
                await conn.fetchval("SELECT 1")
                result = await conn.fetchrow(query, grievance_id.strip())
                if result:
                    logger.info(f"Found grievance data for ID: {grievance_id}")
                    return dict(result)
                else:
                    logger.warning(f"No grievance found with ID: {grievance_id}")
                    return None
        except Exception as e:
            logger.error(f"Database error while fetching grievance {grievance_id}:", exc_info=True)
            return None

    async def search_grievances_by_user(self, user_identifier: str) -> List[Dict[str, Any]]:
        """Search grievances by user mobile, email, or name."""
        if not self.pool:
            logger.error("Database pool not initialized")
            return []
        try:
            async with self.pool.acquire() as conn:
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
                LIMIT 10
                """
                results = await conn.fetch(query, user_identifier.strip())
                return [
                    {
                        'grievance_id': str(row['id']),
                        'grievance_number': row['grievance_unique_number'] or f"GR{row['id']}",
                        'citizen_name': row['citizen_name'] or 'N/A',
                        'status': row['grievance_status'] or 'Pending',
                        'category': row['category_name'] or 'General',
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    }
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Database error while searching grievances for {user_identifier}:", exc_info=True)
            return []

    async def get_grievance_statistics(self) -> Dict[str, Any]:
        """Fetch grievance statistics: total, status distribution, category distribution, etc."""
        if not self.pool:
            logger.error("Database pool not initialized")
            return {}
        try:
            async with self.pool.acquire() as conn:
                # Total active grievances
                total = await conn.fetchval("SELECT COUNT(*) FROM grievances WHERE is_active = true")
                # Status distribution
                status_dist = {
                    row['status']: row['count']
                    for row in await conn.fetch(
                        "SELECT grievance_status as status, COUNT(*) as count FROM grievances "
                        "WHERE grievance_status IS NOT NULL AND is_active = true GROUP BY grievance_status"
                    )
                }
                # Category distribution (top 10)
                category_dist = {
                    row['category']: row['count']
                    for row in await conn.fetch(
                        "SELECT gc.grievance_name as category, COUNT(*) as count "
                        "FROM grievances g LEFT JOIN grievance_categories gc ON g.grievance_type_id = gc.id "
                        "WHERE g.is_active = true GROUP BY gc.grievance_name ORDER BY count DESC LIMIT 10"
                    )
                }
                # Recent grievances (last 30 days)
                recent = await conn.fetchval(
                    "SELECT COUNT(*) FROM grievances WHERE created_at >= NOW() - INTERVAL '30 days' AND is_active = true"
                )
                # Resolved grievances
                resolved = await conn.fetchval(
                    "SELECT COUNT(*) FROM grievances "
                    "WHERE grievance_status IN ('Resolved', 'Closed', 'Completed') AND is_active = true"
                )
                return {
                    'total_grievances': total,
                    'recent_grievances_30_days': recent,
                    'resolved_grievances': resolved,
                    'status_distribution': status_dist,
                    'category_distribution': category_dist
                }
        except Exception as e:
            logger.error("Error fetching grievance statistics:", exc_info=True)
            return {"error": str(e)}

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
