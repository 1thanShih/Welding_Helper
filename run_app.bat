@echo off
setlocal

:: --- Configuration ---
set "ENV_NAME=solder_helper"
set "SCRIPT_NAME=main.py"

echo [INFO] Detect Conda installation...

:: 1. Find the base directory of Conda dynamically
:: We use 'conda info --base' to get the installation path
for /f "tokens=*" %%i in ('conda info --base') do set "CONDA_BASE=%%i"

if "%CONDA_BASE%"=="" (
    echo [ERROR] 'conda' command not found or not in PATH.
    echo [HINT] Please install Anaconda/Miniconda first.
    pause
    exit /b 1
)

echo [INFO] Conda found at: %CONDA_BASE%

:: 2. Configure path to the activation script
set "ACTIVATE_SCRIPT=%CONDA_BASE%\Scripts\activate.bat"

if not exist "%ACTIVATE_SCRIPT%" (
    echo [ERROR] Activation script not found at %ACTIVATE_SCRIPT%
    pause
    exit /b 1
)

:: 3. Attempt to activate environment DIRECTLY using the script
:: This bypasses the need for 'conda init'
echo [INFO] Activating environment: %ENV_NAME%
call "%ACTIVATE_SCRIPT%" %ENV_NAME%

if %errorlevel% neq 0 (
    echo [WARN] Environment '%ENV_NAME%' not found.
    echo [INFO] Creating environment '%ENV_NAME%'...
    
    call conda create -n %ENV_NAME% python=3.9 tk -y
    
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create environment.
        pause
        exit /b 1
    )
    
    echo [INFO] Activating newly created environment...
    call "%ACTIVATE_SCRIPT%" %ENV_NAME%
)

:: 4. Run the Python application
if exist "%SCRIPT_NAME%" (
    echo [INFO] Starting PCB Studio...
    echo ---------------------------------------------------
    python %SCRIPT_NAME%
    echo ---------------------------------------------------
) else (
    echo [ERROR] %SCRIPT_NAME% not found in current directory.
)

if %errorlevel% neq 0 (
    echo [ERROR] Program crashed or closed unexpectedly.
) else (
    echo [INFO] Done.
)

pause
endlocal