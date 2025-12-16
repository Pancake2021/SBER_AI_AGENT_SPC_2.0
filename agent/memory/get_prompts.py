"""История и получение промптов"""
from agent.memory.memory_state import State
from agent.prompts.prompts import sys_final_answer
from agent.tools.run_giga import llm


def get_history_prompt(
    state: State,
    prompt: str,
    tools: str,
    quest: str
) -> str:
    """Слияние Prompt и историей предыдущих действий (Use memory)"""
    tools_out = ""
    empty = "Инструменты не использовались"
    get_tools = state.history_tools
    if get_tools:
        for name_tool, out_tool in get_tools.items():
            tools_out += f"Получен ответ от инструмента: **{name_tool}**\n{out_tool}\n{'-'*80}\n"
            
    # Добавляем контекст диалога (Conversation Memory)
    conversation_context = ""
    if hasattr(state, 'conversation_summary') and state.conversation_summary:
        conversation_context += f"САММАРИ ПРЕДЫДУЩЕГО ДИАЛОГА:\n{state.conversation_summary}\n\n"
    
    if hasattr(state, 'conversation_history') and state.conversation_history:
        conversation_context += "ПОСЛЕДНИЕ СООБЩЕНИЯ:\n"
        for msg in state.conversation_history:
            role = "User" if msg["role"] == "user" else "AI"
            conversation_context += f"{role}: {msg['content']}\n"
        conversation_context += "\n" + "-"*80 + "\n"
            
    full_context = conversation_context + (empty if not tools_out else tools_out)
            
    new_prompt = prompt.format(
        question=quest,
        tools=tools,
        run_tools=full_context
    )
    return new_prompt


def final_answer(query: str, state: State) -> dict:
    """Формирование финального ответа от агента"""
    awer = "Вернуть статус генерации readme.md. Объяснить что нужно заменить данные, которые выделены красным на свои."
    awerage_repo = "Дай подробный отчет оценки ОФОРМЛЕНИЯ репозитория. Верни все комментарии, расскажи обо всех ошибках и дай рекомендации по их исправлению."
    score_repo_code = "Выведи структурированную таблицу по оценке кода. А так же предложи исправить код в репозитории, если код не соответствует стандартам."
    dop_inst = ""
    if state.result_tools.get("search_content"):
        state.final = state.result_tools.get("search_content")
        return {"final_answer": state.result_tools.get("search_content")}
    if state.result_tools.get("gen_readme"):
        dop_inst += f"\n- {awer}"
    if state.result_tools.get("awerage_repo"):
        dop_inst += f"\n- {awerage_repo}"
    if state.result_tools.get("rate_repository"):
        dop_inst += f"\n- {score_repo_code}"
    tools = ""
    for name_tool, out in state.result_tools.items():
        tools += f"*Инструмент: {name_tool}*\n\n{out}\n{'-'*80}\n\n"
    final_prompt = sys_final_answer.format(
        query_user=query,
        run_tools=tools,
        dop=dop_inst,
    )
    fi_answer = llm(f"Верни структурированный ответ на запрос пользователя в формате Markdown. Последнее действие: {state.thought}", final_prompt)
    state.final = fi_answer
    return {"final_answer": fi_answer}
