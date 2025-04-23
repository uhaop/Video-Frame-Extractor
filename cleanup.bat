:: cleanup_build.bat
rmdir /s /q build
rmdir /s /q __pycache__
del *.spec
echo Cleaned up build files.
