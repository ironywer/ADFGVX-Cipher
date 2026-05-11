from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import PlainTextResponse
from typing import Optional
import json
import re

router = APIRouter(prefix="/api/decrypt-auto", tags=["decryption"])


@router.post("/decrypt-text")
async def decrypt_text(
    request: Request,
    ciphertext: str = Form(...),
    keyword: str = Form(...),
    grid_file: UploadFile = File(...)
):
    """Дешифрование текста из поля с загрузкой ключа и таблицы"""
    cipher = request.app.state.cipher
    
    # Загружаем таблицу
    grid = await load_grid_from_file(grid_file)
    cipher.load_grid(grid)
    cipher.keyword = keyword.upper()
    
    # Нормализуем шифротекст
    text = re.sub(r'[^ADFGVX]', '', ciphertext.upper())
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid ciphertext")
    
    # Дешифруем
    decrypted = perform_decryption(cipher, text)
    
    # Сохраняем результат
    request.app.state.last_decrypted_text = decrypted
    
    return {
        "decrypted_text": decrypted,
        "stats": {
            "cipher_length": len(text),
            "decrypted_length": len(decrypted),
            "keyword_used": cipher.keyword
        }
    }


@router.post("/decrypt-file")
async def decrypt_file(
    request: Request,
    cipher_file: UploadFile = File(...),
    keyword: str = Form(...),
    grid_file: UploadFile = File(...)
):
    """Дешифрование текста из файла с загрузкой ключа и таблицы"""
    cipher = request.app.state.cipher
    
    # Загружаем таблицу
    grid = await load_grid_from_file(grid_file)
    cipher.load_grid(grid)
    cipher.keyword = keyword.upper()
    
    # Читаем файл с шифротекстом
    content = await cipher_file.read()
    try:
        raw_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raw_text = content.decode('latin-1')
    
    # Нормализуем шифротекст
    text = re.sub(r'[^ADFGVX]', '', raw_text.upper())
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid ciphertext")
    
    # Дешифруем
    decrypted = perform_decryption(cipher, text)
    
    # Сохраняем результат
    request.app.state.last_decrypted_text = decrypted
    
    return {
        "decrypted_text": decrypted,
        "stats": {
            "cipher_length": len(text),
            "decrypted_length": len(decrypted),
            "keyword_used": cipher.keyword,
            "file_name": cipher_file.filename
        }
    }

@router.post("/decrypt-text-session")
async def decrypt_text_session(
    request: Request,
    ciphertext: str = Form(...)
):
    """
    Дешифрование текста из поля ИСПОЛЬЗУЯ ПОСЛЕДНИЕ СОХРАНЕННЫЕ таблицу и ключевое слово.
    (Работает только после выполнения шифрования в текущей сессии)
    """
    cipher = request.app.state.cipher
    
    # Проверяем, есть ли сохраненные данные
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        raise HTTPException(
            status_code=400, 
            detail="No grid available. Please encrypt something first in this session."
        )
    
    if not hasattr(request.app.state, 'last_keyword') or request.app.state.last_keyword is None:
        raise HTTPException(
            status_code=400, 
            detail="No keyword available. Please encrypt something first in this session."
        )
    
    # Загружаем сохраненные таблицу и ключевое слово
    cipher.load_grid(request.app.state.last_grid)
    cipher.keyword = request.app.state.last_keyword
    
    # Нормализуем шифротекст
    text = re.sub(r'[^ADFGVX]', '', ciphertext.upper())
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid ciphertext")
    
    # Дешифруем
    decrypted = perform_decryption(cipher, text)
    
    # Сохраняем результат
    request.app.state.last_decrypted_text = decrypted
    
    return {
        "decrypted_text": decrypted,
        "stats": {
            "cipher_length": len(text),
            "decrypted_length": len(decrypted),
            "keyword_used": cipher.keyword,
            "grid_used": "from_session"
        }
    }


@router.post("/decrypt-file-session")
async def decrypt_file_session(
    request: Request,
    cipher_file: UploadFile = File(...)
):
    """
    Дешифрование текста из файла ИСПОЛЬЗУЯ ПОСЛЕДНИЕ СОХРАНЕННЫЕ таблицу и ключевое слово.
    (Работает только после выполнения шифрования в текущей сессии)
    """
    cipher = request.app.state.cipher
    
    # Проверяем, есть ли сохраненные данные
    if not hasattr(request.app.state, 'last_grid') or request.app.state.last_grid is None:
        raise HTTPException(
            status_code=400, 
            detail="No grid available. Please encrypt something first in this session."
        )
    
    if not hasattr(request.app.state, 'last_keyword') or request.app.state.last_keyword is None:
        raise HTTPException(
            status_code=400, 
            detail="No keyword available. Please encrypt something first in this session."
        )
    
    # Загружаем сохраненные таблицу и ключевое слово
    cipher.load_grid(request.app.state.last_grid)
    cipher.keyword = request.app.state.last_keyword
    
    # Читаем файл с шифротекстом
    content = await cipher_file.read()
    try:
        raw_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raw_text = content.decode('latin-1')
    
    # Нормализуем шифротекст
    text = re.sub(r'[^ADFGVX]', '', raw_text.upper())
    
    if not text:
        raise HTTPException(status_code=400, detail="No valid ciphertext")
    
    # Дешифруем
    decrypted = perform_decryption(cipher, text)
    
    # Сохраняем результат
    request.app.state.last_decrypted_text = decrypted
    
    return {
        "decrypted_text": decrypted,
        "stats": {
            "cipher_length": len(text),
            "decrypted_length": len(decrypted),
            "keyword_used": cipher.keyword,
            "grid_used": "from_session",
            "file_name": cipher_file.filename
        }
    }


@router.get("/download-decrypted-text")
async def download_decrypted_text(request: Request):
    """Скачивает последний расшифрованный текст в файл"""
    if not hasattr(request.app.state, 'last_decrypted_text') or request.app.state.last_decrypted_text is None:
        raise HTTPException(status_code=404, detail="No decrypted text available. Please decrypt something first.")
    
    return PlainTextResponse(
        content=request.app.state.last_decrypted_text,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=decrypted_text.txt"}
    )


# Вспомогательные функции
async def load_grid_from_file(grid_file):
    """Загружает таблицу шифра из файла"""
    try:
        content = await grid_file.read()
        grid_data = json.loads(content)
        
        # Поддерживаем два формата:
        # 1. Прямой: {"A": "AD", "B": "AF", ...}
        # 2. С метаданными: {"grid": {"A": "AD", ...}, "metadata": {...}}
        if isinstance(grid_data, dict) and 'grid' in grid_data:
            grid_data = grid_data['grid']
        
        restored_grid = {}
        for k, v in grid_data.items():
            if isinstance(v, str) and len(v) == 2:
                restored_grid[k.upper()] = (v[0].upper(), v[1].upper())
            elif isinstance(v, list) and len(v) == 2:
                restored_grid[k.upper()] = (v[0].upper(), v[1].upper())
        return restored_grid
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading grid: {str(e)}")


def perform_decryption(cipher, ciphertext: str) -> str:
    """Выполняет дешифрование и возвращает текст"""
    # Инвертируем таблицу
    reverse_grid = {v[0] + v[1]: k for k, v in cipher.grid.items()}
    
    cols = len(cipher.keyword)
    total_len = len(ciphertext)
    rows = total_len // cols
    
    # Порядок столбцов
    col_order = sorted(range(cols), key=lambda i: cipher.keyword[i])
    
    # Заполняем матрицу
    matrix = [['' for _ in range(cols)] for _ in range(rows)]
    pos = 0
    for i, col_idx in enumerate(col_order):
        for row in range(rows):
            if pos < total_len:
                matrix[row][col_idx] = ciphertext[pos]
                pos += 1
    
    # Читаем по строкам
    encoded = []
    for row in range(rows):
        for col in range(cols):
            if matrix[row][col]:
                encoded.append(matrix[row][col])
    
    encoded_str = ''.join(encoded)
    
    # Декодируем пары
    result = []
    for i in range(0, len(encoded_str), 2):
        if i + 1 < len(encoded_str):
            pair = encoded_str[i] + encoded_str[i+1]
            if pair in reverse_grid:
                result.append(reverse_grid[pair])
    
    return ''.join(result)