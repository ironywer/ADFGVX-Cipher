import random
import re
from typing import List, Dict, Optional, Tuple

ADFGVX_LETTERS = ['A', 'D', 'F', 'G', 'V', 'X']

class ADFGVXCipher:
    def __init__(self):
        self.grid = None
        self.keyword = None
        self.keywords_history: List[str] = []  # История ключевых слов
    
    def generate_grid(self, custom_alphabet: str = None):
        """Генерирует случайную таблицу шифра 6x6"""
        if custom_alphabet:
            alphabet = custom_alphabet
        else:
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        shuffled = list(alphabet)
        random.shuffle(shuffled)
        
        self.grid = {}
        for i, row_char in enumerate(ADFGVX_LETTERS):
            for j, col_char in enumerate(ADFGVX_LETTERS):
                idx = i * 6 + j
                if idx < len(shuffled):
                    self.grid[shuffled[idx]] = (row_char, col_char)
        
        return self.grid
    
    def load_grid(self, grid_data):
        """Загружает таблицу шифра из словаря"""
        self.grid = grid_data
        return self.grid
    
    def add_keyword_to_history(self, keyword: str):
        """Добавляет ключевое слово в историю, если его там еще нет"""
        keyword_upper = keyword.upper()
        if keyword_upper not in self.keywords_history:
            self.keywords_history.append(keyword_upper)
        return self.keywords_history
    
    def get_keywords_history(self) -> List[str]:
        """Возвращает список всех ключевых слов в сессии"""
        return self.keywords_history
    
    def clear_keywords_history(self):
        """Очищает историю ключевых слов"""
        self.keywords_history = []
    
    def load_keywords_history(self, keywords: List[str]):
        """Загружает список ключевых слов из файла"""
        self.keywords_history = [k.upper() for k in keywords if k]
    
    def check_keyword_compatibility(self, encoded_length: int, keyword: str) -> bool:
        """
        Проверяет, подходит ли ключевое слово для шифрования текста заданной длины
        Возвращает True, если длина закодированного текста кратна длине ключевого слова
        """
        return encoded_length % len(keyword) == 0
    
    def find_compatible_keyword(self, encoded_length: int) -> Optional[str]:
        """
        Ищет в истории ключевое слово, подходящее для шифрования текста заданной длины
        """
        for keyword in self.keywords_history:
            if self.check_keyword_compatibility(encoded_length, keyword):
                return keyword
        return None
    
    def generate_permutation_table(self, keyword: str = None):
        """
        Генерирует таблицу перестановки
        Если keyword не указан, используем текущий
        """
        if keyword:
            kw = keyword.upper()
        elif self.keyword:
            kw = self.keyword
        else:
            raise ValueError("Ключевое слово не задано")
        
        # Получаем порядок сортировки столбцов
        sorted_keyword = ''.join(sorted(kw))
        
        # Создаем порядок перестановки
        permutation = []
        used_positions = set()
        
        for char in sorted_keyword:
            for i, k in enumerate(kw):
                if k == char and i not in used_positions:
                    permutation.append(i)
                    used_positions.add(i)
                    break
        
        return {
            'keyword': kw,
            'permutation_order': permutation,
            'length': len(kw)
        }
    
    def encrypt_with_keyword(self, plaintext: str, keyword: str) -> Tuple[str, str]:
        """
        Шифрование текста с указанным ключевым словом
        Возвращает (зашифрованный_текст, использованное_ключевое_слово)
        """
        if not self.grid:
            raise ValueError("Таблица шифра не сгенерирована")
        
        # Приводим к верхнему регистру и удаляем небуквенные символы
        plaintext = re.sub(r'[^A-Za-z0-9]', '', plaintext.upper())
        
        if not plaintext:
            raise ValueError("Нет допустимых символов для шифрования")
        
        # Шаг 1: Замена символов на пары ADFGVX
        encoded = []
        for char in plaintext:
            if char in self.grid:
                encoded.append(self.grid[char][0] + self.grid[char][1])
        
        encoded_str = ''.join(encoded)
        encoded_length = len(encoded_str)
        
        # Проверяем совместимость ключевого слова
        keyword_upper = keyword.upper()
        if not self.check_keyword_compatibility(encoded_length, keyword_upper):
            raise ValueError(
                f"Длина закодированного текста ({encoded_length}) "
                f"не кратна длине ключевого слова ({len(keyword_upper)})"
            )
        
        # Сохраняем ключевое слово
        self.keyword = keyword_upper
        self.add_keyword_to_history(keyword_upper)
        
        cols = len(self.keyword)
        rows = encoded_length // cols
        
        # Заполняем матрицу по строкам
        matrix = []
        idx = 0
        for i in range(rows):
            row = []
            for j in range(cols):
                if idx < encoded_length:
                    row.append(encoded_str[idx])
                    idx += 1
                else:
                    row.append('')
            matrix.append(row)
        
        # Получаем порядок перестановки столбцов
        perm_order = self.generate_permutation_table()['permutation_order']
        
        # Читаем по столбцам в порядке перестановки
        result = []
        for col_idx in perm_order:
            for row in range(rows):
                if matrix[row][col_idx]:
                    result.append(matrix[row][col_idx])
        
        return ''.join(result), self.keyword
    
    def decrypt_with_keyword(self, ciphertext: str, keyword: str) -> str:
        """Дешифрование текста с указанным ключевым словом"""
        if not self.grid:
            raise ValueError("Таблица шифра не загружена")
        
        # Инвертируем таблицу шифра
        reverse_grid = {}
        for k, v in self.grid.items():
            if isinstance(v, tuple) and len(v) == 2:
                reverse_grid[v[0] + v[1]] = k
            elif isinstance(v, str) and len(v) == 2:
                reverse_grid[v] = k
        
        keyword_upper = keyword.upper()
        cols = len(keyword_upper)
        total_len = len(ciphertext)
        
        # Проверяем, что длина шифротекста корректна
        if total_len % cols != 0:
            raise ValueError(
                f"Длина шифротекста ({total_len}) не кратна длине ключа ({cols})"
            )
        
        rows = total_len // cols
        
        # Сохраняем ключевое слово
        self.keyword = keyword_upper
        
        # Получаем порядок перестановки
        perm_order = self.generate_permutation_table()['permutation_order']
        
        # Создаем пустую матрицу
        matrix = [['' for _ in range(cols)] for _ in range(rows)]
        
        # Заполняем матрицу по столбцам
        pos = 0
        for perm_idx, col_idx in enumerate(perm_order):
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