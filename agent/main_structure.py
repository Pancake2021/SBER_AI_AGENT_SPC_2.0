"""Главная структура агента"""
from agent.prompts.prompts import history_prompt, sys_prompt
from agent.memory.get_prompts import get_history_prompt, final_answer
from agent.parsing.parsing_state import post_form_instrument
from agent.parsing.parsing_llm import ParseLLM
from tools.tools import run_tools
from loguru import logger


def main_agent(data: dict):
    """Главная функция агента для обработки запроса"""
    query = data.get("user_query")
    tools = data.get("list_tools")
    state = data.get("pars_quest")
    parsing = ParseLLM()
    
    prompt = get_history_prompt(state, history_prompt, tools, query)
    answer_llm = parsing.get_main_answer_agent(
        new_prompt=prompt,
        prompt=sys_prompt
    )
    
    action_input = answer_llm["Инструмент"]
    state.thought = answer_llm["Мысли"]
    logger.info(f"Action: {action_input}")
    logger.info(f"Thought: {state.thought}")
    
    name_tool = action_input.get("name_tool")
    if name_tool and name_tool != "answer":
        if name_tool in ("search_content", "create_repo"):
            action_input["query"] = query
            output_tool = run_tools(content=action_input)
            post_form_instrument(action_input, output_tool, state)
            return final_answer(query, state)
        output_tool = run_tools(content=action_input)
        post_form_instrument(action_input, output_tool, state)
        state.count_add()
        if state.count_steps == 7:
            logger.info("Достигнут максимум шагов (7)")
            return final_answer(query, state)
        return {
            "user_query": query
        }
    elif name_tool and name_tool == "answer":
        if state.count_steps == 0:
            output_tool = run_tools(content={
                "name_tool": "search_content",
                "query": query
            })
            post_form_instrument(action_input, output_tool, state)
            return final_answer(query, state)
        return final_answer(query, state)
    return {
        "user_query": query
    }
