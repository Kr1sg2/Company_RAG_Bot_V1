@echo off
echo Clearing ChromaDB memory...

echo.
echo Attempting to force kill any process using port 8600...
REM This loop finds the PID(s) of processes using port 8600 and force kills them.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8600') do (
    echo Killing process with PID %%a...
    taskkill /F /PID %%a
)

echo.
echo Waiting a few seconds for processes to terminate...
timeout /t 5 /nobreak

echo.
echo Deleting the ChromaDB directory...
rmdir /s /q "C:\company_chatbot\chroma_db"
if exist "C:\company_chatbot\chroma_db" (
    echo ERROR: Could not delete "C:\company_chatbot\chroma_db". 
    echo It appears that some files may still be in use.
    pause
    exit /b 1
) else (
    echo "C:\company_chatbot\chroma_db" directory has been deleted.
)

echo.
echo Recreating the ChromaDB directory...
mkdir "C:\company_chatbot\chroma_db"
if exist "C:\company_chatbot\chroma_db" (
    echo "C:\company_chatbot\chroma_db" directory has been recreated.
) else (
    echo ERROR: Could not create "C:\company_chatbot\chroma_db". Please check permissions.
)

echo.
echo Done.
pause
