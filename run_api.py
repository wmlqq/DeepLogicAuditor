"""Start the FastAPI service from the project root."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.logic_auditor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
