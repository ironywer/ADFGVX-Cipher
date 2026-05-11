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
POST /api/encrypt-auto/generate-grid - сгенерировать новую таблицу шифра

POST /api/encrypt-auto/load-grid - загрузить таблицу из JSON файла

GET /api/encrypt-auto/grid-status - проверить статус текущей таблицы

GET /api/encrypt-auto/download-grid - скачать текущую таблицу

GET /api/encrypt-auto/keywords - получить список всех ключевых слов

POST /api/encrypt-auto/keywords/add - добавить новое ключевое слово

DELETE /api/encrypt-auto/keywords/{keyword} - удалить ключевое слово

DELETE /api/encrypt-auto/keywords/clear - очистить всю историю ключей

GET /api/encrypt-auto/keywords/download - скачать список ключевых слов

POST /api/encrypt-auto/keywords/upload - загрузить список ключей из файла

GET /api/encrypt-auto/keyword - получить последнее использованное ключевое слово

POST /api/encrypt-auto/encrypt-with-keyword - шифрование текста/файла с указанным ключом

POST /api/encrypt-auto/encrypt-auto-keyword - шифрование с автоматическим выбором ключа

GET /api/encrypt-auto/check-compatibility - проверить совместимость ключа с текстом

GET /api/encrypt-auto/download-encrypted-text - скачать зашифрованный текст

POST /api/decrypt-auto/decrypt-text-session - быстрое дешифрование текста (использует таблицу из сессии)

POST /api/decrypt-auto/decrypt-text - дешифрование текста с загрузкой таблицы

POST /api/decrypt-auto/decrypt-file-session - быстрое дешифрование файла (использует таблицу из сессии)

POST /api/decrypt-auto/decrypt-file - дешифрование файла с загрузкой таблицы

GET /api/decrypt-auto/download-decrypted-text - скачать расшифрованный текст
```