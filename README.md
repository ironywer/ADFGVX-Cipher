# ADFGVX-Cipher
Реализация шифра ADFGVX.

## Установка и запуск

```bash
# Создание виртуального окружения
python -m venv .venv

# Активация на Windows
.venv\\Scripts\\activate 

# Активация на Linux, Mac
source .venv/bin/activate 

# Установка зависимостей
pip install -r requirements.txt 

# Запуск сервера
python -m uvicorn app.main:app --reload
```
Документация API после запуска доступна по адресу: http://127.0.0.1:8000/docs


## Методы
```bash
POST /api/encrypt-auto/ - шифрование

GET /api/encrypt-auto/download-encrypted-text - скачать зашифрованный текст

GET /api/encrypt-auto/download-grid - скачать таблицу

GET /api/encrypt-auto/keyword - получить ключевое слово

POST /api/decrypt-auto/decrypt-text - дешифрование текста (с загрузкой)

POST /api/decrypt-auto/decrypt-file - дешифрование файла (с загрузкой)

POST /api/decrypt-auto/decrypt-text-session - НОВЫЙ быстрое дешифрование текста

POST /api/decrypt-auto/decrypt-file-session - НОВЫЙ быстрое дешифрование файла

GET /api/decrypt-auto/download-decrypted-text - скачать расшифрованный текст
```