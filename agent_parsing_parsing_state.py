"""Обработка результатов инструментов"""
from agent.memory.memory_state import State


def post_form_instrument(
    action_input: dict,
    output_tool: str or list or dict,
    state: State
) -> None:
    """Обработка результата выполнения инструмента"""
    name_tool = action_input["name_tool"]
    if isinstance(output_tool, dict):
        if output_tool["status"] == 200:
            if name_tool == "search_content":
                state.relevant_doc = output_tool["relevant_doc"]
                state.texts = output_tool["chunks"]
                state.score = output_tool["score"]
            state.history_tools[name_tool] = (
                f"**Инструмент {name_tool}** -> успешно выполнено! Ответ получен!\n"
                f"{output_tool['answer'] if name_tool == 'show_files' else 'Файл открыт!' if name_tool == 'read_file' else 'Генерация readme завершена!' if name_tool == 'gen_readme' else ''}\n"
            )
            state.result_tools[name_tool] = (
                f"Готово! Измените текст, которые выделенны красным шрифтом на ваши актуальные данные. {output_tool['answer']}" 
                if name_tool == "gen_readme" 
                else output_tool["answer"]
            )
        else:
            state.history_tools[name_tool] = (
                f"**Инструмент {name_tool}** -> выполнился с ошибкой! Ошибка: {output_tool['answer']}!\n"
            )
            state.result_tools[name_tool] = output_tool["answer"]
    else:
        raise KeyError("Ошибка в формате output_tool")
