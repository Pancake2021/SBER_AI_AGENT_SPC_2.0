"""
Модуль управления памятью диалога (Conversation Buffer Window)
"""
from typing import List, Dict, Optional
from agent.tools.run_giga import llm
from agent.prompts.prompts import sys_prompt_summary

class ConversationMemory:
    """
    Память диалога с буфером и суммаризацией.
    Хранит последние N сообщений и саммари предыдущих.
    """
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.messages: List[Dict[str, str]] = []  # [{"role": "user", "content": "..."}, ...]
        self.summary: str = ""
        
    def add_message(self, role: str, content: str):
        """Добавить сообщение в историю"""
        self.messages.append({"role": role, "content": content})
        
        # Если превышен размер окна (умножаем на 2, т.к. пары user-ai)
        if len(self.messages) > self.window_size * 2:
            self._summarize_oldest()
            
    def get_context(self) -> Dict:
        """Получить текущий контекст для промпта"""
        return {
            "summary": self.summary,
            "history": self.messages
        }
        
    def get_history_string(self) -> str:
        """Получить историю в виде строки для промпта"""
        lines = []
        if self.summary:
            lines.append(f"Summary of previous conversation:\n{self.summary}\n")
            lines.append("-" * 20)
            
        for msg in self.messages:
            role = "User" if msg["role"] == "user" else "AI"
            lines.append(f"{role}: {msg['content']}")
            
        return "\n".join(lines)
        
    def _summarize_oldest(self):
        """Сжатие старых сообщений в саммари"""
        # Берем сообщения, которые выходят за рамки окна
        # Оставляем последние window_size * 2
        keep_count = self.window_size * 2
        to_summarize = self.messages[:-keep_count]
        self.messages = self.messages[-keep_count:]
        
        if not to_summarize:
            return
            
        # Формируем текст для суммаризации
        text_lines = []
        for msg in to_summarize:
            role = "User" if msg["role"] == "user" else "AI"
            text_lines.append(f"{role}: {msg['content']}")
            
        new_text = "\n".join(text_lines)
        
        # Вызываем LLM для обновления саммари
        try:
            prompt = sys_prompt_summary.format(
                summary=self.summary if self.summary else "Нет предыдущего саммари.",
                new_lines=new_text
            )
            # Используем пустой sys_prompt, так как инструкция уже в prompt
            new_summary = llm(prompt, "")
            self.summary = new_summary
        except Exception as e:
            print(f"Ошибка суммаризации памяти: {e}")
            # Если ошибка, просто добавляем текст к саммари (fallback)
            self.summary += "\n" + new_text
