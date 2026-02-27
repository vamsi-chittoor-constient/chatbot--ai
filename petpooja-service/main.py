"""
Production Server - A24 Restaurant Data Pipeline
Start the application
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    """Start API server"""

    server_config = {
        "app": "app.main:app",
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "workers": int(os.getenv("API_WORKERS", "1")),
        "reload": os.getenv("API_RELOAD", "true").lower() == "true",
        "log_level": os.getenv("API_LOG_LEVEL", "info"),
        "access_log": True,
        "proxy_headers": True,
        "forwarded_allow_ips": "*",
    }

    print("=" * 70)
    print("A24 RESTAURANT DATA PIPELINE")
    print("=" * 70)
    print(f"Environment: {'Development' if server_config['reload'] else 'Production'}")
    print(f"Host: {server_config['host']}")
    print(f"Port: {server_config['port']}")
    print(f"Workers: {server_config['workers']}")
    print("=" * 70)
    print(f"API Docs: http://{server_config['host']}:{server_config['port']}/docs")
    print(f"Health: http://{server_config['host']}:{server_config['port']}/health")
    print("=" * 70)

    uvicorn.run(**server_config)


if __name__ == "__main__":
    main()
