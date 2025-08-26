@echo off

:: Batch file to open PowerShell as Administrator and run the rename script

:: Step 1: Open PowerShell as Administrator and run the script
PowerShell -NoProfile -ExecutionPolicy Bypass -File "C:\company_chatbot\Tools_for_running_chatbot\Rename_files_IN CB_FS01 so the sync will work\rename_files.ps1"

pause