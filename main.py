"""Главная точка входа агента"""
from agent.state_graph.graph import agent
from agent.parsing.parsing_llm import classification_query
from schemas.answer import Answer
from loguru import logger


def run_agent(task: str) -> Answer:
    """
    Главная функция агента для обработки запросов
    
    Args:
        task: Запрос пользователя на естественном языке
    
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
        answer_text, state = agent(task)
        
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
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        print("Agent SPC - Интеллектуальный помощник для работы с репозиториями")
        print("-" * 60)
        query = input("Введите ваш запрос: ")
    
    if query.strip():
        result = run_agent(query)
        print("\n" + "=" * 60)
        print("ОТВЕТ АГЕНТА:")
        print("=" * 60)
        print(result.text)
        
        if result.score:
            print(f"\nОценка: {result.score}")
        if result.tokens_used:
            print(f"Использовано токенов: {result.tokens_used}")
    else:
        print("Пустой запрос. Выход.")
