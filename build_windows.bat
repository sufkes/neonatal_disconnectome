@echo off
REM Build script for Disconnectome Windows application
REM Usage: build_windows.bat [clean|build|both]

setlocal EnableDelayedExpansion

REM Configuration
set "BUILD_TYPE=%~1"
if "%BUILD_TYPE%"=="" set "BUILD_TYPE=both"
set "SPEC_FILE=Disconnectome.spec"

REM Colors (using PowerShell for colored output)
set "PS_GREEN=[System.ConsoleColor]::Green"
set "PS_YELLOW=[System.ConsoleColor]::Yellow"
set "PS_RED=[System.ConsoleColor]::Red"

echo.
echo ========================================
echo   Disconnectome Windows Build Script
echo ========================================
echo.

REM Check for required files
if not exist "%SPEC_FILE%" (
    call :print_error "Spec file not found: %SPEC_FILE%"
    exit /b 1
)

if not exist "app.py" (
    call :print_error "app.py not found"
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    call :print_error "PyInstaller not found. Install with: pip install pyinstaller"
    exit /b 1
)

call :print_status "Requirements check passed"

REM Execute based on build type
if "%BUILD_TYPE%"=="clean" (
    call :clean_build
) else if "%BUILD_TYPE%"=="build" (
    call :check_data_size
    call :create_icon
    call :build_app
) else if "%BUILD_TYPE%"=="both" (
    call :clean_build
    call :check_data_size
    call :create_icon
    call :build_app
) else if "%BUILD_TYPE%"=="test" (
    call :test_app
) else if "%BUILD_TYPE%"=="installer" (
    call :create_installer
) else (
    echo Usage: %~nx0 [clean^|build^|both^|test^|installer]
    echo.
    echo Options:
    echo   clean      - Remove build artifacts
    echo   build      - Build the application
    echo   both       - Clean then build (default^)
    echo   test       - Test the built application
    echo   installer  - Create installer (requires Inno Setup^)
    exit /b 1
)

call :print_status "Done!"
pause
exit /b 0

REM ============================================================================
REM Functions
REM ============================================================================

:print_status
powershell -Command "Write-Host '[*] %~1' -ForegroundColor Green"
goto :eof

:print_warning
powershell -Command "Write-Host '[!] %~1' -ForegroundColor Yellow"
goto :eof

:print_error
powershell -Command "Write-Host '[ERROR] %~1' -ForegroundColor Red"
goto :eof

:clean_build
call :print_status "Cleaning build artifacts..."

if exist "build\" rmdir /s /q "build\"
if exist "dist\" rmdir /s /q "dist\"
if exist "__pycache__\" rmdir /s /q "__pycache__"

REM Clean Python cache files
for /r %%i in (__pycache__) do (
    if exist "%%i" rmdir /s /q "%%i"
)
for /r %%i in (*.pyc) do (
    if exist "%%i" del /q "%%i"
)

call :print_status "Clean complete"
goto :eof

:check_data_size
call :print_status "Checking data directory sizes..."

if exist "data\" (
    for /f "tokens=3" %%a in ('dir "data" /s /-c ^| find "File(s)"') do set DATA_SIZE=%%a
    call :print_warning "data\ directory size: !DATA_SIZE! bytes"

    if exist "data\controls\" (
        for /f "tokens=3" %%a in ('dir "data\controls" /s /-c ^| find "File(s)"') do set CONTROLS_SIZE=%%a
        call :print_warning "data\controls\ directory size: !CONTROLS_SIZE! bytes"
        call :print_warning "Large controls directory may cause build issues"

        set /p "CONTINUE=Continue anyway? (y/n): "
        if /i not "!CONTINUE!"=="y" (
            call :print_status "Build cancelled"
            exit /b 0
        )
    )
)
goto :eof

:create_icon
if not exist "icon.ico" (
    if exist "app_icon.png" (
        call :print_status "Creating .ico icon from app_icon.png..."

        REM Try to use ImageMagick if available
        magick convert app_icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico 2>nul

        if errorlevel 1 (
            call :print_warning "ImageMagick not found. Using PNG as fallback."
            call :print_warning "Install ImageMagick for better icon quality:"
            call :print_warning "  https://imagemagick.org/script/download.php"
        ) else (
            call :print_status "Icon created: icon.ico"
        )
    )
)
goto :eof

:build_app
call :print_status "Starting PyInstaller build..."

REM Set environment variables
set PYTHONOPTIMIZE=1

REM Run PyInstaller
pyinstaller --clean --noconfirm "%SPEC_FILE%" 2>&1 | tee build.log

if errorlevel 1 (
    call :print_error "Build failed. Check build.log for details"
    exit /b 1
)

call :print_status "Build completed successfully!"

if exist "dist\Disconnectome\" (
    for /f "tokens=3" %%a in ('dir "dist\Disconnectome" /s /-c ^| find "File(s)"') do (
        set /a SIZE_MB=%%a/1024/1024
        call :print_status "Application size: !SIZE_MB! MB"
    )
    call :print_status "Application location: %CD%\dist\Disconnectome"
)
goto :eof

:test_app
call :print_status "Testing application..."

if not exist "dist\Disconnectome\Disconnectome.exe" (
    call :print_error "Application not found"
    exit /b 1
)

call :print_status "Launching application..."
start "" "dist\Disconnectome\Disconnectome.exe"

call :print_status "Application launched. Check if it opens correctly."
timeout /t 5 /nobreak >nul
goto :eof

:create_installer
if not exist "dist\Disconnectome\Disconnectome.exe" (
    call :print_error "Application not found. Build first."
    exit /b 1
)

call :print_status "Creating Windows installer..."

REM Check for Inno Setup
where iscc >nul 2>&1
if errorlevel 1 (
    call :print_error "Inno Setup not found."
    call :print_error "Download from: https://jrsoftware.org/isinfo.php"
    exit /b 1
)

REM Create Inno Setup script if it doesn't exist
if not exist "installer.iss" (
    call :create_inno_script
)

REM Compile installer
iscc installer.iss

if errorlevel 1 (
    call :print_error "Failed to create installer"
    exit /b 1
)

call :print_status "Installer created successfully!"
goto :eof

:create_inno_script
call :print_status "Creating Inno Setup script..."

(
echo #define MyAppName "Disconnectome"
echo #define MyAppVersion "1.0.0"
echo #define MyAppPublisher "Your Organization"
echo #define MyAppURL "https://yourwebsite.com"
echo #define MyAppExeName "Disconnectome.exe"
echo.
echo [Setup]
echo AppId={{YOUR-UNIQUE-GUID-HERE}}
echo AppName={#MyAppName}
echo AppVersion={#MyAppVersion}
echo AppPublisher={#MyAppPublisher}
echo AppPublisherURL={#MyAppURL}
echo AppSupportURL={#MyAppURL}
echo AppUpdatesURL={#MyAppURL}
echo DefaultDirName={autopf}\{#MyAppName}
echo DisableProgramGroupPage=yes
echo LicenseFile=LICENSE.txt
echo OutputDir=.
echo OutputBaseFilename=DisconnectomeSetup
echo Compression=lzma
echo SolidCompression=yes
echo WizardStyle=modern
echo.
echo [Languages]
echo Name: "english"; MessagesFile: "compiler:Default.isl"
echo.
echo [Tasks]
echo Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
echo.
echo [Files]
echo Source: "dist\Disconnectome\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
echo Source: "dist\Disconnectome\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
echo.
echo [Icons]
echo Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
echo Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
echo.
echo [Run]
echo Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
) > installer.iss

call :print_status "Inno Setup script created: installer.iss"
call :print_warning "Edit installer.iss to customize the installer"
goto :eof
