"""
Модуль сбора обратной связи (Active Learning / RLHF)
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from tools.settings import Configure

class FeedbackCollector:
    """
    Класс для сбора и управления обратной связью от пользователей.
    Сохраняет данные в JSONL формате для последующего анализа или дообучения.
    """
    
    def __init__(self):
        self.config = Configure()
        self.file_path = Path(self.config.path_feedback)
        self._ensure_dir()
        
    def _ensure_dir(self):
        """Создание директории для логов если не существует"""
        if not self.file_path.parent.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
    def save_feedback(self, 
                      query: str, 
                      response: str, 
                      rating: int, 
                      feedback_text: str = "",
                      meta: Optional[Dict] = None) -> Dict:
        """
        Сохранение единицы обратной связи.
        
        Args:
            query: Запрос пользователя
            response: Ответ агента
            rating: Оценка (например, 1 - Good, -1 - Bad, или 1-5)
            feedback_text: Текстовый комментарий пользователя
            meta: Дополнительные метаданные (использованные инструменты, время выполнения и т.д.)
            
        Returns:
            Сохраненная запись
        """
        record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "rating": rating,
            "feedback": feedback_text,
            "meta": meta or {}
        }
        
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return record
        except Exception as e:
            print(f"Ошибка сохранения фидбека: {e}")
            return {}

    def get_stats(self) -> Dict:
        """Получение статистики по фидбеку"""
        if not self.file_path.exists():
            return {"total": 0, "positive": 0, "negative": 0}
            
        total = 0
        positive = 0
        negative = 0
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        total += 1
                        rating = data.get("rating", 0)
                        if rating > 0:
                            positive += 1
                        elif rating < 0:
                            negative += 1
                    except:
                        continue
                        
            return {
                "total": total,
                "positive": positive,
                "negative": negative,
                "positive_rate": f"{(positive/total)*100:.1f}%" if total > 0 else "0%"
            }
        except Exception:
            return {"error": "Не удалось прочитать файл статистики"}

    def get_negative_examples(self, limit: int = 5) -> List[Dict]:
        """
        Получение последних негативных примеров для анализа или In-context learning.
        """
        examples = []
        if not self.file_path.exists():
            return examples
            
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                # Читаем все строки
                lines = f.readlines()
                
                # Идем с конца
                for line in reversed(lines):
                    try:
                        data = json.loads(line)
                        if data.get("rating", 0) < 0:
                            examples.append(data)
                            if len(examples) >= limit:
                                break
                    except:
                        continue
        except Exception:
            pass
            
        return examples
