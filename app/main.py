from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.cipher import ADFGVXCipher
from datetime import datetime
import os

# Создаем экземпляр шифра
cipher = ADFGVXCipher()

# Создаем приложение FastAPI
app = FastAPI(title="ADFGVX Cipher API", version="2.1.0")

# Настройка CORS (для доступа из браузера)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
from app.routers import encrypt_auto, decrypt_auto

app.include_router(encrypt_auto.router)
app.include_router(decrypt_auto.router)

# Инициализируем глобальное состояние для хранения данных
app.state.cipher = cipher
app.state.last_encrypted_text = None
app.state.last_decrypted_text = None
app.state.last_keyword = None
app.state.last_grid = None  # Таблица будет сгенерирована или загружена пользователем
app.state.keywords_history = []  # История ключевых слов
app.state.grid_generated = False
app.state.grid_generation_time = datetime.now().isoformat()
app.state.grid_loaded_from_file = None

# Подключаем статические файлы
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Главная страница
@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

# API информация
@app.get("/api")
async def api_info():
    return {
        "message": "ADFGVX Cipher API v2.1",
        "version": "2.1.0",
        "description": "Шифр ADFGVX с управлением таблицей и ключевыми словами",
        "workflow": {
            "setup": [
                "1. Сгенерировать или загрузить таблицу (/api/encrypt-auto/generate-grid или /api/encrypt-auto/load-grid)",
                "2. Добавить ключевые слова в историю (/api/encrypt-auto/keywords/add)",
                "3. Шифровать текст используя таблицу и ключевые слова"
            ]
        },
        "endpoints": {
            "grid_management": {
                "generate_grid": "POST /api/encrypt-auto/generate-grid",
                "load_grid": "POST /api/encrypt-auto/load-grid",
                "grid_status": "GET /api/encrypt-auto/grid-status",
                "download_grid": "GET /api/encrypt-auto/download-grid"
            },
            "keyword_management": {
                "get_keywords": "GET /api/encrypt-auto/keywords",
                "add_keyword": "POST /api/encrypt-auto/keywords/add",
                "remove_keyword": "DELETE /api/encrypt-auto/keywords/{keyword}",
                "clear_keywords": "DELETE /api/encrypt-auto/keywords/clear",
                "download_keywords": "GET /api/encrypt-auto/keywords/download",
                "upload_keywords": "POST /api/encrypt-auto/keywords/upload"
            },
            "encryption": {
                "encrypt_with_keyword": "POST /api/encrypt-auto/encrypt-with-keyword",
                "encrypt_auto_keyword": "POST /api/encrypt-auto/encrypt-auto-keyword",
                "download_encrypted": "GET /api/encrypt-auto/download-encrypted-text",
                "check_compatibility": "GET /api/encrypt-auto/check-compatibility"
            },
            "decryption": {
                "decrypt_text_session": "POST /api/decrypt-auto/decrypt-text-session",
                "decrypt_text": "POST /api/decrypt-auto/decrypt-text",
                "decrypt_file_session": "POST /api/decrypt-auto/decrypt-file-session",
                "download_decrypted": "GET /api/decrypt-auto/download-decrypted-text"
            }
        },
        "current_session_state": {
            "grid_available": app.state.last_grid is not None,
            "keywords_count": len(app.state.keywords_history),
            "last_encrypted": app.state.last_encrypted_text is not None,
            "last_decrypted": app.state.last_decrypted_text is not None
        }
    }


# Session state endpoint for frontend
@app.get("/api/session-state")
async def session_state():
    return {
        "grid_available": app.state.last_grid is not None,
        "keywords_count": len(app.state.keywords_history),
        "last_encrypted": app.state.last_encrypted_text is not None,
        "last_decrypted": app.state.last_decrypted_text is not None
    }


@app.on_event("startup")
async def startup_event():
    """При старте приложения генерируем таблицу по умолчанию"""
    app.state.cipher.generate_grid()
    app.state.last_grid = app.state.cipher.grid
    app.state.grid_generated = True
    app.state.grid_generation_time = datetime.now().isoformat()
    print("Default grid generated on startup")