from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
import json
import re
from datetime import datetime

router = APIRouter(prefix="/api/encrypt-auto", tags=["encryption"])

def normalize_text(text: str) -> str:
    """Нормализует текст: оставляет только буквы и цифры"""
    return re.sub(r'[^A-Za-z0-9]', '', text).upper()


@router.post("/generate-grid")
async def generate_grid(
    request: Request,
    custom_alphabet: Optional[str] = Form(None)
):
    """
    Генерирует новую таблицу шифра и сохраняет её в сессии
    Поддерживает form-data
    """
    cipher = request.app.state.cipher
    
    # Генерируем новую таблицу
    if custom_alphabet:
        # Проверяем, что алфавит содержит 36 символов (6x6)
        if len(custom_alphabet) != 36:
            raise HTTPException(
                status_code=400, 
                detail=f"Custom alphabet must have exactly 36 characters, got {len(custom_alphabet)}"
            )
        cipher.generate_grid(custom_alphabet.upper())
    else:
        cipher.generate_grid()
    
    # Сохраняем в глобальном состоянии
    request.app.state.last_grid = cipher.grid
    request.app.state.grid_generated = True
    request.app.state.grid_generation_time = datetime.now().isoformat()
    
    # Экспортируем таблицу для ответа
    grid_export = {k: v[0] + v[1] for k, v in cipher.grid.items()}
    
    return {
        "message": "New grid generated successfully",
        "grid": dict(sorted(grid_export.items())),
        "grid_size": "6x6",
        "alphabet_size": len(cipher.grid),
        "stats": {
            "generated_at": request.app.state.grid_generation_time,
            "characters": list(cipher.grid.keys())[:10]
        }
    }


@router.post("/encrypt-with-keyword")
async def encrypt_with_keyword(
    request: Request,
    plaintext: Optional[str] = Form(None),
    keyword: str = Form(...),  # Обязательное поле
    file: Optional[UploadFile] = File(None)
):
    """
    Шифрование текста с указанным ключевым словом
    Поддерживает form-data:
    - plaintext: текст для шифрования
    - keyword: ключевое слово
    - file: файл для шифрования (опционально)
    """
    cipher = request.app.state.cipher
    
    # Проверяем наличие таблицы
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        raise HTTPException(
            status_code=400,
            detail="No grid available. Please generate or load a grid first using /generate-grid or /load-grid"
        )
    
    cipher.load_grid(request.app.state.last_grid)
    
    # Получаем текст
    text = None
    if plaintext:
        text = normalize_text(plaintext)
    elif file:
        content = await file.read()
        try:
            raw_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raw_text = content.decode('latin-1')
        text = normalize_text(raw_text)
    else:
        raise HTTPException(
            status_code=400, 
            detail="No text provided. Please provide 'plaintext' or 'file' parameter"
        )
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid characters to encrypt")
    
    # Шифруем с указанным ключевым словом
    try:
        encrypted_text, used_keyword = cipher.encrypt_with_keyword(text, keyword)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # СОХРАНЯЕМ В ГЛОБАЛЬНОЕ СОСТОЯНИЕ
    request.app.state.last_encrypted_text = encrypted_text
    request.app.state.last_keyword = used_keyword
    
    # Обновляем историю ключевых слов
    if not hasattr(request.app.state, 'keywords_history'):
        request.app.state.keywords_history = cipher.get_keywords_history()
    else:
        request.app.state.keywords_history = cipher.get_keywords_history()
    
    # Экспортируем таблицу для ответа
    grid_export = {k: v[0] + v[1] for k, v in cipher.grid.items()}
    
    return {
        "encrypted_text": encrypted_text,
        "keyword_used": used_keyword,
        "grid_preview": dict(list(sorted(grid_export.items()))[:10]),
        "stats": {
            "original_length": len(text),
            "encoded_length": len(text) * 2,
            "encrypted_length": len(encrypted_text),
            "keyword_length": len(used_keyword),
            "is_compatible": True,
            "grid_used": "from_session"
        },
        "keywords_history": request.app.state.keywords_history
    }


@router.post("/encrypt-auto-keyword")
async def encrypt_auto_keyword(
    request: Request,
    plaintext: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Шифрование текста с автоматическим выбором подходящего ключевого слова из истории
    Поддерживает form-data
    """
    cipher = request.app.state.cipher
    
    # Проверяем наличие таблицы
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        raise HTTPException(
            status_code=400,
            detail="No grid available. Please generate or load a grid first using /generate-grid or /load-grid"
        )
    
    cipher.load_grid(request.app.state.last_grid)
    
    # Получаем текст
    text = None
    if plaintext:
        text = normalize_text(plaintext)
    elif file:
        content = await file.read()
        try:
            raw_text = content.decode('utf-8')
        except UnicodeDecodeError:
            raw_text = content.decode('latin-1')
        text = normalize_text(raw_text)
    else:
        raise HTTPException(
            status_code=400, 
            detail="No text provided. Please provide 'plaintext' or 'file' parameter"
        )
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid characters to encrypt")
    
    # Проверяем все ли символы есть в таблице
    missing_chars = []
    for char in text:
        if char not in cipher.grid:
            missing_chars.append(char)
    
    if missing_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Characters not found in grid: {', '.join(set(missing_chars))}"
        )
    
    # Кодируем в пары ADFGVX
    encoded_pairs = []
    for char in text:
        if char in cipher.grid:
            encoded_pairs.append(cipher.grid[char][0] + cipher.grid[char][1])
    
    encoded_str = ''.join(encoded_pairs)
    encoded_length = len(encoded_str)
    
    # Проверяем наличие истории ключевых слов
    if not hasattr(request.app.state, 'keywords_history') or not request.app.state.keywords_history:
        raise HTTPException(
            status_code=400,
            detail="No keywords available. Please add keywords using /keywords/add"
        )
    
    # Используем первое ключевое слово из истории (ключи универсальны)
    compatible_keyword = cipher.find_compatible_keyword(encoded_length)
    
    if not compatible_keyword:
        raise HTTPException(
            status_code=400,
            detail="No keywords available. Please add keywords using /keywords/add"
        )
    
    # Шифруем с найденным ключевым словом
    try:
        encrypted_text, used_keyword = cipher.encrypt_with_keyword(text, compatible_keyword)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # СОХРАНЯЕМ В ГЛОБАЛЬНОЕ СОСТОЯНИЕ
    request.app.state.last_encrypted_text = encrypted_text
    request.app.state.last_keyword = used_keyword
    request.app.state.keywords_history = cipher.get_keywords_history()
    
    grid_export = {k: v[0] + v[1] for k, v in cipher.grid.items()}
    
    return {
        "encrypted_text": encrypted_text,
        "keyword_used": used_keyword,
        "grid_preview": dict(list(sorted(grid_export.items()))[:10]),
        "stats": {
            "original_length": len(text),
            "encoded_length": encoded_length,
            "encrypted_length": len(encrypted_text),
            "keyword_length": len(used_keyword),
            "is_compatible": True,
            "auto_selected": True
        },
        "keywords_history": request.app.state.keywords_history
    }


@router.post("/keywords/add")
async def add_keyword(
    request: Request, 
    keyword: str = Form(...)
):
    """Добавляет новое ключевое слово в историю (form-data)"""
    cipher = request.app.state.cipher
    keyword_upper = keyword.upper()
    
    # Проверяем длину ключевого слова
    if len(keyword_upper) < 2:
        raise HTTPException(status_code=400, detail="Keyword must be at least 2 characters")
    
    if len(keyword_upper) > 20:
        raise HTTPException(status_code=400, detail="Keyword must be at most 20 characters")
    
    # Добавляем в историю
    keywords = cipher.add_keyword_to_history(keyword_upper)
    
    # Обновляем глобальное состояние
    if not hasattr(request.app.state, 'keywords_history'):
        request.app.state.keywords_history = keywords
    else:
        request.app.state.keywords_history = keywords
    
    return {
        "message": f"Keyword '{keyword_upper}' added successfully",
        "keywords": keywords,
        "count": len(keywords)
    }


@router.post("/keywords/upload")
async def upload_keywords(
    request: Request,
    file: UploadFile = File(...),
    merge: bool = Form(True)
):
    """
    Загружает список ключевых слов из JSON файла
    merge=True - добавляет к существующим
    merge=False - заменяет существующие
    """
    cipher = request.app.state.cipher
    
    try:
        content = await file.read()
        data = json.loads(content)
        
        # Поддерживаем разные форматы файлов
        if isinstance(data, list):
            keywords = data
        elif isinstance(data, dict) and 'keywords' in data:
            keywords = data['keywords']
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Expected list or object with 'keywords' field")
        
        if not merge:
            cipher.clear_keywords_history()
        
        added_count = 0
        for kw in keywords:
            if kw and kw.upper() not in cipher.keywords_history:
                cipher.add_keyword_to_history(kw)
                added_count += 1
        
        request.app.state.keywords_history = cipher.get_keywords_history()
        
        return {
            "message": f"Keywords {'merged' if merge else 'loaded'} successfully",
            "keywords": request.app.state.keywords_history,
            "count": len(request.app.state.keywords_history),
            "added_count": added_count
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading file: {str(e)}")


@router.post("/load-grid")
async def load_grid(
    request: Request,
    grid_file: UploadFile = File(...)
):
    """
    Загружает таблицу шифра из JSON файла и сохраняет её в сессии
    """
    cipher = request.app.state.cipher
    
    try:
        content = await grid_file.read()
        grid_data = json.loads(content)
        
        # Восстанавливаем таблицу из формата {"A": "AD", "B": "AF", ...}
        restored_grid = {}
        
        # Поддерживаем два формата:
        # 1. Прямой: {"A": "AD", "B": "AF", ...}
        # 2. С метаданными: {"grid": {"A": "AD", ...}, "metadata": {...}}
        if isinstance(grid_data, dict) and 'grid' in grid_data:
            grid_data = grid_data['grid']
        
        for k, v in grid_data.items():
            if isinstance(v, str) and len(v) == 2:
                restored_grid[k.upper()] = (v[0].upper(), v[1].upper())
            elif isinstance(v, list) and len(v) == 2:
                restored_grid[k.upper()] = (v[0].upper(), v[1].upper())
            else:
                raise ValueError(f"Invalid grid format for key {k}")
        
        # Проверяем размер таблицы
        if len(restored_grid) != 36:
            raise ValueError(f"Grid must have 36 entries, got {len(restored_grid)}")
        
        # Загружаем таблицу
        cipher.load_grid(restored_grid)
        
        # Сохраняем в глобальном состоянии
        request.app.state.last_grid = cipher.grid
        request.app.state.grid_generated = True
        request.app.state.grid_loaded_from_file = grid_file.filename
        request.app.state.grid_loaded_time = datetime.now().isoformat()
        
        # Экспортируем для ответа
        grid_export = {k: v[0] + v[1] for k, v in cipher.grid.items()}
        
        return {
            "message": f"Grid loaded successfully from {grid_file.filename}",
            "grid": dict(sorted(grid_export.items())),
            "grid_size": "6x6",
            "characters_count": len(cipher.grid),
            "source_file": grid_file.filename,
            "loaded_at": request.app.state.grid_loaded_time
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file format")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading grid: {str(e)}")


# Остальные эндпоинты (GET запросы) остаются без изменений
@router.get("/grid-status")
async def get_grid_status(request: Request):
    """Возвращает информацию о текущей таблице в сессии"""
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        return {
            "exists": False,
            "message": "No grid available. Please generate or load a grid first.",
            "grid_generated": False
        }
    
    cipher = request.app.state.cipher
    grid_export = {k: v[0] + v[1] for k, v in cipher.grid.items()}
    
    response = {
        "exists": True,
        "grid_generated": True,
        "grid_size": len(grid_export),
        "sample": dict(list(sorted(grid_export.items()))[:10]),
    }
    
    if hasattr(request.app.state, 'grid_loaded_from_file') and request.app.state.grid_loaded_from_file:
        response["loaded_from_file"] = request.app.state.grid_loaded_from_file
        response["loaded_at"] = getattr(request.app.state, 'grid_loaded_time', None)
    
    if hasattr(request.app.state, 'grid_generation_time') and request.app.state.grid_generation_time:
        response["generated_at"] = request.app.state.grid_generation_time
    
    return response


@router.get("/download-grid")
async def download_grid(request: Request):
    """Скачивает текущую таблицу шифра в JSON файл"""
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        raise HTTPException(
            status_code=404, 
            detail="No grid available. Please generate or load a grid first."
        )
    
    grid_export = {k: v[0] + v[1] for k, v in request.app.state.last_grid.items()}
    sorted_grid = dict(sorted(grid_export.items()))
    
    grid_time = None
    if hasattr(request.app.state, 'grid_generation_time'):
        grid_time = request.app.state.grid_generation_time
    elif hasattr(request.app.state, 'grid_loaded_time'):
        grid_time = request.app.state.grid_loaded_time
    
    export_data = {
        "grid": sorted_grid,
        "metadata": {
            "export_date": datetime.now().isoformat(),
            "size": len(sorted_grid),
            "type": "ADFGVX 6x6 grid",
            "created_at": grid_time
        }
    }
    
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": "attachment; filename=adfgvx_grid.json"}
    )


@router.get("/keywords")
async def get_keywords(request: Request):
    """Возвращает список всех ключевых слов в сессии"""
    if not hasattr(request.app.state, 'keywords_history'):
        request.app.state.keywords_history = []
    
    return {
        "keywords": request.app.state.keywords_history,
        "count": len(request.app.state.keywords_history),
        "exists": len(request.app.state.keywords_history) > 0
    }


@router.delete("/keywords/{keyword}")
async def remove_keyword(request: Request, keyword: str):
    """Удаляет ключевое слово из истории"""
    cipher = request.app.state.cipher
    keyword_upper = keyword.upper()
    
    if keyword_upper in cipher.keywords_history:
        cipher.keywords_history.remove(keyword_upper)
        request.app.state.keywords_history = cipher.keywords_history
        return {
            "message": f"Keyword '{keyword_upper}' removed successfully",
            "keywords": cipher.keywords_history,
            "count": len(cipher.keywords_history)
        }
    else:
        raise HTTPException(status_code=404, detail=f"Keyword '{keyword_upper}' not found")


@router.delete("/keywords/clear")
async def clear_keywords(request: Request):
    """Очищает всю историю ключевых слов"""
    cipher = request.app.state.cipher
    cipher.clear_keywords_history()
    request.app.state.keywords_history = []
    
    return {
        "message": "Keywords history cleared successfully",
        "keywords": [],
        "count": 0
    }


@router.get("/keywords/download")
async def download_keywords(request: Request):
    """Скачивает список ключевых слов в JSON файл"""
    if not hasattr(request.app.state, 'keywords_history') or not request.app.state.keywords_history:
        raise HTTPException(status_code=404, detail="No keywords available")
    
    grid_time = None
    if hasattr(request.app.state, 'grid_generation_time'):
        grid_time = request.app.state.grid_generation_time
    elif hasattr(request.app.state, 'grid_loaded_time'):
        grid_time = request.app.state.grid_loaded_time
    
    export_data = {
        "keywords": request.app.state.keywords_history,
        "count": len(request.app.state.keywords_history),
        "export_date": datetime.now().isoformat(),
        "metadata": {
            "format_version": "1.0",
            "type": "adfgvx_keywords",
            "grid_created_at": grid_time
        }
    }
    
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": "attachment; filename=adfgvx_keywords.json"}
    )


@router.get("/check-compatibility")
async def check_compatibility(
    text_length: int,
    keyword: str
):
    """Проверяет совместимость ключевого слова с текстом. Ключи всегда совместимы."""
    encoded_length = text_length * 2
    keyword_length = len(keyword)
    
    return {
        "text_length": text_length,
        "encoded_length": encoded_length,
        "keyword": keyword.upper(),
        "keyword_length": keyword_length,
        "is_compatible": True,
        "remainder": 0
    }


@router.get("/download-encrypted-text")
async def download_encrypted_text(request: Request):
    """Скачивает последний зашифрованный текст в файл"""
    if not hasattr(request.app.state, 'last_encrypted_text') or request.app.state.last_encrypted_text is None:
        raise HTTPException(status_code=404, detail="No encrypted text available. Please encrypt something first.")
    
    return PlainTextResponse(
        content=request.app.state.last_encrypted_text,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=encrypted_text.txt"}
    )


@router.get("/keyword")
async def get_keyword(request: Request):
    """Возвращает последнее использованное ключевое слово"""
    if not hasattr(request.app.state, 'last_keyword') or request.app.state.last_keyword is None:
        return {"keyword": None, "exists": False, "message": "No keyword available. Please encrypt something first."}
    
    return {
        "keyword": request.app.state.last_keyword, 
        "exists": True, 
        "length": len(request.app.state.last_keyword)
    }