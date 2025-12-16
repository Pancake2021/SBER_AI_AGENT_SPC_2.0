"""Главная точка входа агента"""
from agent.state_graph.graph import agent
from agent.parsing.parsing_llm import classification_query
from schemas.answer import Answer
from loguru import logger


from agent.memory.conversation_memory import ConversationMemory

def run_agent(task: str, memory: ConversationMemory = None) -> Answer:
    """
    Главная функция агента для обработки запросов
    
    Args:
        task: Запрос пользователя на естественном языке
        memory: Объект памяти диалога
    
    Returns:
        Answer: Структурированный ответ агента
    """
    logger.info(f"Получен запрос: {task[:100]}...")
    
    # Проверка релевантности запроса
    query_result = classification_query(task)
    
    # Если запрос нерелевантен
    if isinstance(query_result, dict) and "not_rel" in query_result:
        logger.info("Запрос классифицирован как нерелевантный")
        return Answer(
            text=query_result["not_rel"],
            relevant_docs={},
            context="",
            score="not_relevant",
            tokens_used=0
        )
    
    # Обработка релевантного запроса через агента
    try:
        # Получаем контекст из памяти
        memory_context = memory.get_context() if memory else None
        
        answer_text, state = agent(task, memory_context=memory_context)
        
        # Сохраняем результат в память
        if memory:
            memory.add_message("user", task)
            memory.add_message("ai", answer_text)
        
        logger.info("Запрос успешно обработан")
        
        return Answer(
            text=answer_text,
            relevant_docs=state.relevant_doc if hasattr(state, "relevant_doc") else {},
            context=state.texts if hasattr(state, "texts") else "",
            score=state.score if hasattr(state, "score") else "",
            prompt_tokens_used=state.prompt_tokens if hasattr(state, "prompt_tokens") else 0,
            completion_tokens_used=state.completion_tokens if hasattr(state, "completion_tokens") else 0,
            tokens_used=state.total_tokens if hasattr(state, "total_tokens") else 0
        )
    
    except Exception as e:
        logger.error(f"Ошибка выполнения агента: {str(e)}")
        return Answer(
            text=f"Произошла ошибка при обработке запроса: {str(e)}",
            relevant_docs={},
            context="",
            score="error",
            tokens_used=0
        )


if __name__ == "__main__":
    import sys
    
    print("Agent SPC - Интеллектуальный помощник (с памятью)")
    print("-" * 60)
    print("Введите 'exit' или 'quit' для выхода")
    
    # Инициализация памяти
    memory = ConversationMemory(window_size=3)
    
    while True:
        try:
            query = input("\nВведите ваш запрос: ").strip()
            if not query:
                continue
                
            if query.lower() in ('exit', 'quit'):
                print("До свидания!")
                break
                
            result = run_agent(query, memory=memory)
            
            print("\n" + "=" * 60)
            print("ОТВЕТ АГЕНТА:")
            print("=" * 60)
            print(result.text)
            
            if result.score:
                print(f"\nОценка: {result.score}")
            if result.tokens_used:
                print(f"Использовано токенов: {result.tokens_used}")
                
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            print(f"\nОшибка: {e}")
