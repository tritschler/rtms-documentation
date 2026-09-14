# RTMS-Web Startup Guide

To start the different parts of the `rtms-web` project, you can use the following commands:

### 1. Frontend (React / Vite)
Open a terminal, navigate to the `frontend` folder, and start the development server:
```bash
cd frontend
npm run dev
```
*(If you are using `yarn` or `pnpm`, use `yarn dev` or `pnpm dev` respectively).*
The frontend will be accessible by default at `http://localhost:5173`.

### 2. Backend (FastAPI)
Open another terminal, navigate to the `backend` folder, and start the application with `uvicorn` (the standard ASGI server for FastAPI):
```bash
cd backend
uv run uvicorn main:app --reload
```
*(Make sure `uv` is installed. The `uv run` command will automatically use the project's virtual environment).*
The backend will be accessible by default at `http://localhost:8000`.
