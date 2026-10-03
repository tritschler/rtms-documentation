Stage 1: uses pyinstaller to convert your Python app into a single binary
done in the dockerfile

Stage 2: uses a distroless image (has no shell, no package manager, and no Python), so:
Your .py files are never included.
Even if the client enters the container, there’s no sh or cat to read files.
They only see a binary, which is very hard to reverse-engineer.

docker build -t myapp-protected .
docker run --rm myapp-protected

Bonus: Add basic obfuscation (optional)
If you want even more protection:
Use pyarmor or nuitka instead of PyInstaller (they obfuscate Python bytecode).
Strip debug symbols from the binary:

RUN strip /app/dist/myapp
