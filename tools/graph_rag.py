"""
GraphRAG - Граф знаний для контекстного поиска

Простая реализация GraphRAG на основе LLM-извлечения сущностей
и построения графа связей между документами.
"""
import pickle
import os
import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

try:
    from agent.tools.run_giga import llm
    HAS_LLM = True
except ImportError:
    HAS_LLM = False


# Промпт для извлечения сущностей
ENTITY_EXTRACTION_PROMPT = """Извлеки ключевые сущности из текста документации/кода.

Типы сущностей для извлечения:
- Функции и методы (названия)
- Классы и модули
- Технологии и библиотеки
- Ключевые концепции и термины

Текст:
{text}

ВАЖНО: Верни ТОЛЬКО JSON без markdown разметки:
{{"entities": ["сущность1", "сущность2"], "relations": [["сущность1", "связан_с", "сущность2"]]}}
"""


class GraphRAG:
    """
    Граф знаний для расширения контекста поиска.
    
    Строит граф связей между сущностями в документах,
    позволяя находить связанный контекст при поиске.
    """
    
    def __init__(self, cache_path: str = "output/knowledge_graph.pkl"):
        """
        Args:
            cache_path: Путь для кеширования графа
        """
        self.cache_path = cache_path
        
        # Граф связей: entity -> set of related entities
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Маппинг: entity -> list of document indices
        self.entity_to_docs: Dict[str, List[int]] = defaultdict(list)
        
        # Маппинг: doc_index -> list of entities
        self.doc_to_entities: Dict[int, List[str]] = {}
        
        # Тексты документов (ссылка на внешние данные)
        self.texts: List[dict] = []
        
        self._load_cache()
    
    def _load_cache(self) -> bool:
        """Загрузка графа из кеша"""
        cache_file = Path(self.cache_path)
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    self.graph = defaultdict(set, data.get("graph", {}))
                    self.entity_to_docs = defaultdict(list, data.get("entity_to_docs", {}))
                    self.doc_to_entities = data.get("doc_to_entities", {})
                return True
            except Exception as e:
                print(f"Ошибка загрузки кеша графа: {e}")
        return False
    
    def _save_cache(self):
        """Сохранение графа в кеш"""
        try:
            cache_file = Path(self.cache_path)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_file, "wb") as f:
                pickle.dump({
                    "graph": dict(self.graph),
                    "entity_to_docs": dict(self.entity_to_docs),
                    "doc_to_entities": self.doc_to_entities
                }, f)
        except Exception as e:
            print(f"Ошибка сохранения кеша графа: {e}")
    
    def extract_entities(self, text: str, use_llm: bool = True) -> Tuple[List[str], List[Tuple[str, str, str]]]:
        """
        Извлечение сущностей из текста.
        
        Args:
            text: Текст документа
            use_llm: Использовать LLM или эвристики
            
        Returns:
            (entities, relations) - списки сущностей и связей
        """
        if use_llm and HAS_LLM:
            return self._extract_with_llm(text)
        else:
            return self._extract_with_heuristics(text)
    
    def _extract_with_llm(self, text: str) -> Tuple[List[str], List[Tuple[str, str, str]]]:
        """Извлечение через LLM"""
        # Ограничиваем текст для экономии токенов
        truncated_text = text[:2000] if len(text) > 2000 else text
        
        try:
            prompt = ENTITY_EXTRACTION_PROMPT.format(text=truncated_text)
            response = llm(prompt, "")
            
            # Парсим JSON из ответа
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                entities = data.get("entities", [])
                relations_raw = data.get("relations", [])
                
                # Преобразуем relations в tuples
                relations = []
                for rel in relations_raw:
                    if len(rel) >= 3:
                        relations.append((rel[0], rel[1], rel[2]))
                
                return entities, relations
        except Exception as e:
            print(f"Ошибка извлечения через LLM: {e}")
        
        # Fallback на эвристики
        return self._extract_with_heuristics(truncated_text)
    
    def _extract_with_heuristics(self, text: str) -> Tuple[List[str], List[Tuple[str, str, str]]]:
        """Эвристическое извлечение сущностей"""
        entities = []
        
        # Извлекаем заголовки markdown
        headers = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
        entities.extend([h.strip() for h in headers])
        
        # Извлекаем имена функций/классов (Python-style)
        functions = re.findall(r'(?:def|class)\s+(\w+)', text)
        entities.extend(functions)
        
        # Извлекаем слова в бэктиках (технические термины)
        backticks = re.findall(r'`([^`]+)`', text)
        entities.extend([b for b in backticks if len(b) < 50])
        
        # Уникализируем и нормализуем
        entities = list(set(e.lower().strip() for e in entities if e.strip()))
        
        # Связи на основе совместного упоминания (простая эвристика)
        relations = []
        for i, e1 in enumerate(entities[:10]):  # Лимит для производительности
            for e2 in entities[i+1:10]:
                if e1 != e2:
                    relations.append((e1, "related_to", e2))
        
        return entities[:30], relations  # Лимит сущностей
    
    def build_graph(self, texts: List[dict], use_llm: bool = False):
        """
        Построение графа знаний из документов.
        
        Args:
            texts: Список документов [{"file": path, "content": text}, ...]
            use_llm: Использовать LLM для извлечения (дорого по токенам)
        """
        self.texts = texts
        
        # Если граф уже построен и размер совпадает - пропускаем
        if len(self.doc_to_entities) == len(texts) and self.graph:
            return
        
        print(f"Построение графа знаний для {len(texts)} документов...")
        
        # Очищаем старый граф
        self.graph = defaultdict(set)
        self.entity_to_docs = defaultdict(list)
        self.doc_to_entities = {}
        
        for idx, doc in enumerate(texts):
            content = doc.get("content", "")
            
            # Извлекаем сущности
            entities, relations = self.extract_entities(content, use_llm=use_llm)
            
            # Сохраняем маппинги
            self.doc_to_entities[idx] = entities
            
            for entity in entities:
                self.entity_to_docs[entity].append(idx)
            
            # Добавляем связи в граф
            for e1, _, e2 in relations:
                e1_lower = e1.lower()
                e2_lower = e2.lower()
                self.graph[e1_lower].add(e2_lower)
                self.graph[e2_lower].add(e1_lower)
            
            # Связываем сущности в одном документе
            for i, e1 in enumerate(entities):
                for e2 in entities[i+1:]:
                    self.graph[e1].add(e2)
                    self.graph[e2].add(e1)
        
        print(f"Граф построен: {len(self.graph)} узлов, "
              f"{sum(len(v) for v in self.graph.values())} связей")
        
        self._save_cache()
    
    def find_entities_in_query(self, query: str) -> List[str]:
        """Поиск сущностей из графа в запросе"""
        query_lower = query.lower()
        found = []
        
        for entity in self.graph.keys():
            if entity in query_lower:
                found.append(entity)
        
        return found
    
    def get_related_docs(self, query: str, depth: int = 1, max_docs: int = 5) -> List[int]:
        """
        Получение индексов связанных документов через обход графа.
        
        Args:
            query: Поисковый запрос
            depth: Глубина обхода графа
            max_docs: Максимум документов
            
        Returns:
            Список индексов документов
        """
        # Находим сущности в запросе
        seed_entities = self.find_entities_in_query(query)
        
        if not seed_entities:
            return []
        
        # BFS обход графа
        visited_entities: Set[str] = set()
        current_level = set(seed_entities)
        all_entities: Set[str] = set(seed_entities)
        
        for _ in range(depth):
            next_level: Set[str] = set()
            for entity in current_level:
                if entity not in visited_entities:
                    visited_entities.add(entity)
                    neighbors = self.graph.get(entity, set())
                    next_level.update(neighbors - visited_entities)
            
            all_entities.update(next_level)
            current_level = next_level
            
            if not current_level:
                break
        
        # Собираем документы
        doc_scores: Dict[int, int] = defaultdict(int)
        
        for entity in all_entities:
            for doc_idx in self.entity_to_docs.get(entity, []):
                doc_scores[doc_idx] += 1
        
        # Сортируем по количеству совпадений
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [doc_idx for doc_idx, _ in sorted_docs[:max_docs]]
    
    def get_context_expansion(self, base_indices: List[int], query: str, max_additional: int = 3) -> List[int]:
        """
        Расширение контекста: добавляем связанные документы к базовым результатам.
        
        Args:
            base_indices: Индексы документов из обычного поиска
            query: Исходный запрос
            max_additional: Максимум дополнительных документов
            
        Returns:
            Дополнительные индексы документов
        """
        # Собираем сущности из базовых документов
        base_entities: Set[str] = set()
        for idx in base_indices:
            entities = self.doc_to_entities.get(idx, [])
            base_entities.update(entities)
        
        # Находим связанные через граф
        related_entities: Set[str] = set()
        for entity in base_entities:
            related_entities.update(self.graph.get(entity, set()))
        
        # Собираем документы для связанных сущностей
        additional_docs: Set[int] = set()
        for entity in related_entities:
            for doc_idx in self.entity_to_docs.get(entity, []):
                if doc_idx not in base_indices:
                    additional_docs.add(doc_idx)
        
        return list(additional_docs)[:max_additional]
    
    def is_ready(self) -> bool:
        """Проверка готовности графа"""
        return bool(self.graph) and bool(self.entity_to_docs)
