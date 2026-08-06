"""
Startup script that sets event loop policy before importing main
This fixes Python 3.13 + Windows + Playwright compatibility
"""
import sys
import asyncio

# Set event loop policy BEFORE any imports
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now import and run main
import main
if __name__ == "__main__":
    import uvicorn
    from config import settings
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )