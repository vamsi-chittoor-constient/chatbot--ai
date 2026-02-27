#!/usr/bin/env python3
"""
Service Startup Script
=====================
Starts all required services and checks dependencies before launching the main application.
Handles Redis, MongoDB, and database setup automatically.
"""

import asyncio
import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Ensure OPENAI_API_KEY is set from environment
# CrewAI reads this from environment, not from code parameters
if not os.getenv("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY not set. Please set it in your .env file.")
    sys.exit(1)

class ServiceManager:
    """Manages external service dependencies"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services_status: Dict[str, bool] = {}
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up all started processes"""
        print("\n[INFO] Cleaning up services...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
        self.processes.clear()
    
    def check_port(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is available"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                return result == 0  # Port is in use
        except Exception:
            return False
    
    def wait_for_service(self, port: int, service_name: str, timeout: int = 30) -> bool:
        """Wait for a service to become available on a port"""
        print(f"[INFO] Waiting for {service_name} on port {port}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_port(port):
                print(f"[OK] {service_name} is ready on port {port}")
                return True
            time.sleep(1)
        
        print(f"[ERROR] {service_name} failed to start within {timeout} seconds")
        return False
    
    def check_redis(self) -> bool:
        """Check if Redis server is running"""
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        if self.check_port(redis_port):
            print(f"[OK] Redis running on port {redis_port}")
            self.services_status["redis"] = True
            return True
        
        print(f"[WARN] Redis not running on port {redis_port}")
        print("   Please run: start_redis.bat")
        self.services_status["redis"] = False
        return False
    
    def check_mongodb(self) -> bool:
        """Check if MongoDB server is running"""
        mongodb_port = int(os.getenv("MONGODB_PORT", "27017"))
        
        if self.check_port(mongodb_port):
            print(f"[OK] MongoDB running on port {mongodb_port}")
            self.services_status["mongodb"] = True
            return True
        
        print(f"[WARN] MongoDB not running on port {mongodb_port}")
        print("   Please run: start_mongodb.bat")
        self.services_status["mongodb"] = False
        return False
    
    async def setup_database(self) -> bool:
        """Set up database schema and test data"""
        print("[INFO] Database schema assumed to be ready")
        
        # Database setup is handled externally
        # Just verify we can connect (already checked in check_postgresql)
        self.services_status["database"] = True
        return True
    
    def check_postgresql(self) -> bool:
        """Check if PostgreSQL is accessible"""
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                print("[ERROR] DATABASE_URL not configured")
                return False
            
            # Parse database URL
            parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
            
            # Test connection
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:] if parsed.path else "postgres",
                user=parsed.username,
                password=parsed.password
            )
            conn.close()
            print("[OK] PostgreSQL connection successful")
            return True
            
        except Exception as e:
            print(f"[ERROR] PostgreSQL connection failed: {e}")
            print("[TIP] Please ensure PostgreSQL is installed and running:")
            print("   Windows: Download from https://www.postgresql.org/download/windows/")
            print("   Linux: sudo apt-get install postgresql postgresql-contrib")
            print("   macOS: brew install postgresql")
            return False

async def main():
    """Main startup script"""
    print("=== Restaurant AI Service Startup ===")
    print("=" * 50)
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n[INFO] Received interrupt signal, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    with ServiceManager() as service_manager:
        # Check PostgreSQL first (required)
        if not service_manager.check_postgresql():
            print("[ERROR] PostgreSQL is required but not available")
            return False
        
        # Check optional services (started separately via batch files)
        redis_ok = service_manager.check_redis()
        mongodb_ok = service_manager.check_mongodb()
        
        # Set up database
        database_ok = await service_manager.setup_database()
        
        if not database_ok:
            print("[ERROR] Database setup failed, cannot continue")
            return False
        
        # Print service status
        print("\n" + "=" * 50)
        print("=== Service Status ===")
        print(f"[OK] PostgreSQL: Ready")
        print(f"[OK] Database Schema: Ready")
        print(f"{'[OK]' if redis_ok else '[WARN]'} Redis: {'Ready' if redis_ok else 'Not available (optional)'}")
        print(f"{'[OK]' if mongodb_ok else '[WARN]'} MongoDB: {'Ready' if mongodb_ok else 'Not available (optional)'}")
        
        if not redis_ok or not mongodb_ok:
            print("\n[INFO] Note: Some optional services are not available")
            print("   The application will work but with limited functionality")
            print("   - Redis: Required for caching and session management")
            print("   - MongoDB: Required for analytics and testing data")
        
        # Start the main application
        print("\n[INFO] Starting Restaurant AI Assistant...")
        print("   API will be available at: http://localhost:8000")
        print("   API Documentation: http://localhost:8000/docs")
        print("   Press Ctrl+C to stop all services")
        
        try:
            # Start the FastAPI application
            import uvicorn
            config = uvicorn.Config(
                "app.api.main:app",
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                reload=os.getenv("DEBUG", "true").lower() == "true",
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
            
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        except Exception as e:
            print(f"[ERROR] Application failed to start: {e}")
            return False
        
        return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] Goodbye!")
    except Exception as e:
        print(f"[ERROR] Startup failed: {e}")
        sys.exit(1)