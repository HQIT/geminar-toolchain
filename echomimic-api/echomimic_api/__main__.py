"""
模块入口 - python -m echomimic_api
"""

import uvicorn
from .config import get_api_config

if __name__ == "__main__":
    config = get_api_config()
    uvicorn.run(
        "echomimic_api.app:app",
        host=config.host,
        port=config.port,
        reload=False,
    )

