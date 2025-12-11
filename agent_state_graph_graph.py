"""Граф состояний агента"""
from agent.memory.memory_state import State, AgentState, should_continue
from agent.main_structure import main_agent
from agent.parsing.parsing_text import parsing_html
from tools.tools import get_tools
from langgraph.graph import StateGraph, END


def agent(text: str):
    """Главная функция граф агента с StateGraph"""
    graph = StateGraph(AgentState)
    graph.add_node("show_tools", get_tools)
    graph.add_node("run_tool", main_agent)
    graph.add_conditional_edges(
        "run_tool",
        should_continue,
        {
            "failed": "run_tool",
            "success": END,
        }
    )
    graph.set_entry_point("show_tools")
    graph.add_edge("show_tools", "run_tool")
    grap = graph.compile()
    state = State()
    result = grap.invoke(
        {
            "user_query": text,
            "pars_quest": state,
        }
    )
    if result["pars_quest"].final:
        return parsing_html(result["pars_quest"].final), result["pars_quest"]
    answer = parsing_html(
        result.get("final_answer")
    ) if result.get("final_answer") else "Нет ответа"
    return answer, result["pars_quest"]
