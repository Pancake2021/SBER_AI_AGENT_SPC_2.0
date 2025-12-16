"""Семантический поиск по базе знаний с GraphRAG"""
from tools.bitbucket import ConnectionAPI
from agent.tools.run_giga import llm
from agent.prompts.prompts import sys_prompt_search
from pathlib import Path
import pickle
import os

# GraphRAG для расширения контекста
try:
    from tools.graph_rag import GraphRAG
    HAS_GRAPH_RAG = True
except ImportError:
    HAS_GRAPH_RAG = False

try:
    from FlagEmbedding import BGEM3FlagModel
    HAS_FLAG_EMBEDDING = True
except ImportError:
    HAS_FLAG_EMBEDDING = False


class Search(ConnectionAPI):
    """Класс для семантического поиска с BGEM3FlagModel"""

    def __init__(self, top_k: int = 7, use_graph: bool = True):
        super().__init__()
        self.top_k = top_k
        self.model = None
        self.texts = []
        self.vecs = None
        
        # GraphRAG для расширения контекста
        self.use_graph = use_graph and HAS_GRAPH_RAG
        self.graph_rag = GraphRAG() if self.use_graph else None
        
        if HAS_FLAG_EMBEDDING and self.path_model:
            self.initial_model()

    def initial_model(self):
        """Инициализация модели BGEM3FlagModel"""
        if not HAS_FLAG_EMBEDDING:
            return
        
        try:
            self.model = BGEM3FlagModel(
                self.path_model,
                use_fp16=True
            )
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            self.model = None

    def get_texts(self) -> list:
        """Загрузка текстов из базы знаний (data_cards)"""
        texts = []
        card_path = Path(self.path_card)
        
        if not card_path.exists():
            return texts
        
        for file_path in card_path.glob("**/*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    texts.append({
                        "file": str(file_path),
                        "content": content
                    })
            except Exception:
                continue
        
        self.texts = texts
        
        # Строим граф знаний если включен GraphRAG
        if self.use_graph and self.graph_rag and texts:
            self.graph_rag.build_graph(texts, use_llm=False)
        
        return texts

    def get_vecs_bge(self) -> dict:
        """Получение/кэширование векторов в pickle файл"""
        pickle_path = Path(self.path_pickle)
        
        # Попытка загрузить из кэша
        if pickle_path.exists():
            try:
                with open(pickle_path, "rb") as f:
                    self.vecs = pickle.load(f)
                return self.vecs
            except Exception:
                pass
        
        # Генерация новых векторов
        if not self.model or not self.texts:
            self.get_texts()
        
        if not self.model:
            return {}
        
        contents = [t["content"] for t in self.texts]
        
        try:
            self.vecs = self.model.encode(
                contents,
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=True
            )
            
            # Сохранение в кэш
            with open(pickle_path, "wb") as f:
                pickle.dump(self.vecs, f)
            
            return self.vecs
        except Exception as e:
            print(f"Ошибка кодирования: {e}")
            return {}

    def get_dense_score(self, query: str) -> list:
        """Получение оценки плотных векторов"""
        if not self.model or not self.vecs:
            return []
        
        try:
            q_vecs = self.model.encode(
                [query],
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False
            )
            
            scores = (q_vecs["dense_vecs"] @ self.vecs["dense_vecs"].T)[0]
            top_indices = scores.argsort()[-self.top_k:][::-1]
            
            return [(int(i), float(scores[i])) for i in top_indices]
        except Exception:
            return []

    def get_lexical_score(self, query: str) -> list:
        """Получение оценки разреженных (лексических) векторов"""
        if not self.model or not self.vecs:
            return []
        
        try:
            q_vecs = self.model.encode(
                [query],
                return_dense=False,
                return_sparse=True,
                return_colbert_vecs=False
            )
            
            scores = self.model.compute_lexical_matching_score(
                q_vecs["lexical_weights"][0],
                self.vecs["lexical_weights"]
            )
            
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.top_k]
            
            return [(int(i), float(scores[i])) for i in top_indices]
        except Exception:
            return []

    def get_colbert_score(self, query: str, idx: int) -> float:
        """Получение ColBERT оценки для конкретного документа"""
        if not self.model or not self.vecs:
            return 0.0
        
        try:
            q_vecs = self.model.encode(
                [query],
                return_dense=False,
                return_sparse=False,
                return_colbert_vecs=True
            )
            
            score = self.model.colbert_score(
                q_vecs["colbert_vecs"][0],
                self.vecs["colbert_vecs"][idx]
            )
            
            return float(score)
        except Exception:
            return 0.0

    def answer_llm(self, query: str, chunks: list) -> str:
        """Генерация ответа через LLM на основе найденных чанков"""
        content = "\n\n---\n\n".join(chunks)
        prompt = sys_prompt_search.format(content=content)
        
        try:
            answer = llm(query, prompt)
            return answer
        except Exception as e:
            return f"Ошибка генерации ответа: {str(e)}"

    def run_tool(self, quest: str) -> dict:
        """Главная функция поиска"""
        if not quest:
            return {"status": 400, "answer": "Пустой запрос"}
        
        # Загрузка данных если нужно
        if not self.texts:
            self.get_texts()
        
        if not self.texts:
            return {
                "status": 404,
                "answer": "База знаний пуста",
                "relevant_doc": {},
                "chunks": [],
                "score": "0"
            }
        
        # Если нет модели - простой поиск по ключевым словам
        if not self.model:
            matching = []
            query_lower = quest.lower()
            
            for i, text in enumerate(self.texts):
                if query_lower in text["content"].lower():
                    matching.append({
                        "idx": i,
                        "file": text["file"],
                        "content": text["content"][:500]
                    })
            
            if matching:
                chunks = [m["content"] for m in matching[:self.top_k]]
                answer = self.answer_llm(quest, chunks)
                
                return {
                    "status": 200,
                    "answer": answer,
                    "relevant_doc": {m["file"]: {"content": m["content"]} for m in matching[:3]},
                    "chunks": chunks,
                    "score": "keyword_match"
                }
            
            return {
                "status": 404,
                "answer": "Информация не найдена",
                "relevant_doc": {},
                "chunks": [],
                "score": "0"
            }
        
        # Векторный поиск
        if not self.vecs:
            self.get_vecs_bge()
        
        # Получаем тройную оценку
        dense_scores = self.get_dense_score(quest)
        lexical_scores = self.get_lexical_score(quest)
        
        # Объединяем результаты
        combined = {}
        for idx, score in dense_scores:
            combined[idx] = combined.get(idx, 0) + score * 0.5
        for idx, score in lexical_scores:
            combined[idx] = combined.get(idx, 0) + score * 0.3
        
        # Добавляем ColBERT для топ кандидатов
        for idx in list(combined.keys())[:5]:
            colbert = self.get_colbert_score(quest, idx)
            combined[idx] += colbert * 0.2
        
        # Сортируем по финальному скору
        sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:self.top_k]
        
        # === GraphRAG: расширение контекста ===
        base_indices = [idx for idx, _ in sorted_results]
        graph_indices = []
        
        if self.use_graph and self.graph_rag and self.graph_rag.is_ready():
            # Получаем дополнительные документы через граф
            graph_indices = self.graph_rag.get_context_expansion(
                base_indices, quest, max_additional=2
            )
        
        # Собираем результаты
        relevant_doc = {}
        chunks = []
        
        for idx, score in sorted_results:
            if idx < len(self.texts):
                text_data = self.texts[idx]
                relevant_doc[text_data["file"]] = {
                    "content": text_data["content"][:500],
                    "score": f"{score:.4f}",
                    "source": "vector"
                }
                chunks.append(text_data["content"])
        
        # Добавляем документы из графа
        for idx in graph_indices:
            if idx < len(self.texts) and idx not in base_indices:
                text_data = self.texts[idx]
                relevant_doc[text_data["file"]] = {
                    "content": text_data["content"][:500],
                    "score": "graph",
                    "source": "graph_rag"
                }
                chunks.append(text_data["content"])
        
        if not chunks:
            return {
                "status": 404,
                "answer": "Информация не найдена",
                "relevant_doc": {},
                "chunks": [],
                "score": "0"
            }
        
        # Генерируем ответ
        answer = self.answer_llm(quest, chunks)
        avg_score = sum(s for _, s in sorted_results) / len(sorted_results)
        
        return {
            "status": 200,
            "answer": answer,
            "relevant_doc": relevant_doc,
            "chunks": chunks,
            "score": f"{avg_score:.4f}"
        }
