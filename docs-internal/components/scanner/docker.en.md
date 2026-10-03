# Docker & Binary Packaging

## Multi-Stage Distroless Build

* **Stage 1**: Uses PyInstaller to compile the Python application into a single standalone binary inside the Docker build container.
* **Stage 2**: Uses a distroless base image (no shell, no package manager, no Python runtime):
  * Source `.py` files are never included in the final image.
  * Even if an operator inspects the container, there is no `/bin/sh` or `cat` available.
  * Only the compiled, stripped binary is present.

```bash
docker build -t rtms-scanner-protected .
docker run --rm rtms-scanner-protected
```

## Obfuscation & Binary Stripping (Optional)
For hardened distribution environments:
* Utilize PyArmor or Nuitka alongside PyInstaller for bytecode obfuscation.
* Strip debug symbols from the final ELF binary:
```dockerfile
RUN strip /app/dist/myapp
```
