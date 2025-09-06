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
        """Get grievance status and details from your actual database schema"""
        if not self.pool:
            logger.error("Database pool not initialized")
            return None
            
        try:
            async with self.pool.acquire() as connection:
                # Query using your actual table structure with typo fix
                query = """
                    SELECT 
                        g.id,
                        g.grievance_unique_number,
                        g.citizen_name,
                        g.mobile_number,
                        g.landline_number,
                        g.email,
                        g.address,
                        g.pincode,
                        g.grievance_remark,
                        g.grievance_status,
                        g.rating,
                        g.citizen_feedback,
                        g.resolved_date,
                        g.closed_date,
                        g.created_at,
                        g.updated_at,
                        gc.grievance_name as category_name,
                        sgc.sub_grievance_name as sub_category_name,
                        d.district_name,
                        b.block_name,
                        gp.grampanchayat_name,
                        v.village_name
                    FROM grievances g
                    LEFT JOIN grievance_categories gc ON g.grievance_type_id = gc.id
                    LEFT JOIN sub_grievance_categories sgc ON g.subgrievance_type_id = sgc.id
                    LEFT JOIN districts d ON g.district_id = d.id
                    LEFT JOIN blocks b ON g.block_id = b.id
                    LEFT JOIN grampanchayats gp ON g.grampanchayayt_id = gp.id
                    LEFT JOIN villages v ON g.village_id = v.id
                    WHERE UPPER(g.grievance_unique_number) = UPPER($1) 
                       OR g.id::text = $1 
                       OR UPPER(g.grievance_unique_number) LIKE '%' || UPPER($1) || '%'
                    ORDER BY g.created_at DESC
                    LIMIT 1
                """
                
                result = await connection.fetchrow(query, grievance_id.strip())
                
                if result:
                    # Get tracking information from grievance_resolve_tracks
                    tracks_query = """
                        SELECT 
                            grt.grievance_status,
                            grt.grievance_resolved_remark,
                            grt.grievance_reject_reason,
                            grt.start_date_time,
                            grt.end_date_time,
                            grt.created_at,
                            grt.updated_at,
                            grt.grievance_belongs_to
                        FROM grievance_resolve_tracks grt
                        WHERE grt.grievance_id = $1
                        ORDER BY grt.created_at DESC
                        LIMIT 10
                    """
                    
                    tracks = await connection.fetch(tracks_query, result['id'])
                    
                    return {
                        'grievance_id': str(result['id']),
                        'grievance_number': result['grievance_unique_number'] or f"GR{result['id']}",
                        'title': result['sub_category_name'] or result['category_name'] or 'General Grievance',
                        'description': result['grievance_remark'] or 'No description available',
                        'status': result['grievance_status'] or 'Pending',
                        'priority': 'Normal',  # Not available in your schema
                        'category': result['category_name'] or 'General',
                        'sub_category': result['sub_category_name'] or 'N/A',
                        'user_name': result['citizen_name'] or 'N/A',
                        'user_email': result['email'] or 'N/A',
                        'user_phone': result['mobile_number'] or 'N/A',
                        'landline': result['landline_number'] or 'N/A',
                        'address': result['address'] or 'N/A',
                        'pincode': result['pincode'] or 'N/A',
                        'district': result['district_name'] or 'N/A',
                        'block': result['block_name'] or 'N/A',
                        'grampanchayat': result['grampanchayat_name'] or 'N/A',
                        'village': result['village_name'] or 'N/A',
                        'rating': result['rating'],
                        'feedback': result['citizen_feedback'],
                        'resolved_date': result['resolved_date'].isoformat() if result['resolved_date'] else None,
                        'closed_date': result['closed_date'].isoformat() if result['closed_date'] else None,
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None,
                        'tracking_history': [
                            {
                                'status': track['grievance_status'] or 'N/A',
                                'comments': track['grievance_resolved_remark'] or track['grievance_reject_reason'] or 'No comments',
                                'belongs_to': track['grievance_belongs_to'] or 'N/A',
                                'start_date': track['start_date_time'].isoformat() if track['start_date_time'] else None,
                                'end_date': track['end_date_time'].isoformat() if track['end_date_time'] else None,
                                'date': track['created_at'].isoformat() if track['created_at'] else None,
                                'updated_date': track['updated_at'].isoformat() if track['updated_at'] else None
                            }
                            for track in tracks
                        ]
                    }
                
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
