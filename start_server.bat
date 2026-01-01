@echo off
echo ================================================
echo   LL-RANKINGS LOCAL SERVER
echo ================================================
echo.
echo Starting FastAPI server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ================================================
echo.

cd api
py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
