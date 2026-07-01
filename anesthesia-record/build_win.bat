@echo off
chcp 65001 >nul
echo ============================================
echo   anesthesia-record Windows ビルドスクリプト
echo ============================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [エラー] Python が見つかりません。
    echo https://www.python.org/downloads/ からインストールしてください。
    pause
    exit /b 1
)

echo [1/3] 依存ライブラリをインストール中...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [エラー] 依存ライブラリのインストールに失敗しました。
    pause
    exit /b 1
)

echo [2/3] PyInstaller をインストール中...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo [エラー] PyInstaller のインストールに失敗しました。
    pause
    exit /b 1
)

echo [3/3] 実行ファイルをビルド中...
pyinstaller --onefile --add-data "data;data" --name anesthesia_demo demo.py
if %errorlevel% neq 0 (
    echo [エラー] ビルドに失敗しました。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ビルド完了！
echo   dist\anesthesia_demo.exe が生成されました。
echo ============================================
echo.
echo 実行方法:
echo   cd dist
echo   anesthesia_demo.exe
echo.
pause
