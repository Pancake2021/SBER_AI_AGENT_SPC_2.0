"""Flask API сервер для Agent SPC"""
from flask import Flask, request, jsonify
from loguru import logger
import threading

# Импорты инструментов
from tools.search_content import Search
from tools.bitbucket import ConnectionAPI
from tools.gen_main import GenReadme
from tools.info_tool import InfoTools
from tools.evalution_repo.evalution_repo import EvalutionRepo
from tools.evalution_code.awerage_main import EvalutionCode
from tools.tools import TOOLS_DESCRIPTION
from tools.feedback import FeedbackCollector
from agent.memory.conversation_memory import ConversationMemory
from main import run_agent

app = Flask(__name__)

# Хранилище сессий памяти
# {session_id: ConversationMemory}
SESSIONS = {}


@app.route("/show_tools", methods=["GET"])
def show_tools():
    """Получить список доступных инструментов"""
    return jsonify({
        "status": 200,
        "tools": TOOLS_DESCRIPTION
    })


@app.route("/search_content", methods=["POST"])
def search_content():
    """Семантический поиск по базе знаний"""
    data = request.json or {}
    query = data.get("query", "")
    
    if not query:
        return jsonify({"status": 400, "answer": "Не указан поисковый запрос"})
    
    try:
        search = Search()
        result = search.run_tool(query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка search_content: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/read_file", methods=["POST"])
def read_file():
    """Чтение файла из репозитория BitBucket"""
    data = request.json or {}
    
    if not data.get("repository") or not data.get("file_path"):
        return jsonify({"status": 400, "answer": "Не указан repository или file_path"})
    
    try:
        api = ConnectionAPI()
        result = api.read_file_bb(data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка read_file: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/show_files", methods=["POST"])
def show_files():
    """Получить список файлов репозитория"""
    data = request.json or {}
    repo = data.get("repository", "")
    
    if not repo:
        return jsonify({"status": 400, "answer": "Не указан repository"})
    
    try:
        api = ConnectionAPI()
        result = api.get_files(repo)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка show_files: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/gen_readme", methods=["POST"])
def gen_readme():
    """Генерация README.md для репозитория"""
    data = request.json or {}
    
    if not data.get("repository"):
        return jsonify({"status": 400, "answer": "Не указан repository"})
    
    try:
        gen = GenReadme(data)
        result = gen.run_tool()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка gen_readme: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/awerage_repo", methods=["POST"])
def awerage_repo():
    """Оценка оформления репозитория"""
    data = request.json or {}
    
    if not data.get("repository"):
        return jsonify({"status": 400, "answer": "Не указан repository"})
    
    try:
        ev = EvalutionRepo(data)
        result = ev.run_tool()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка awerage_repo: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/rate_repository", methods=["POST"])
def rate_repository():
    """Оценка качества кода репозитория"""
    data = request.json or {}
    
    if not data.get("repository"):
        return jsonify({"status": 400, "answer": "Не указан repository"})
    
    try:
        ev = EvalutionCode(data)
        result = ev.run_tool()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка rate_repository: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/info_tools", methods=["POST", "GET"])
def info_tools():
    """Информация о возможностях агента"""
    try:
        info = InfoTools()
        result = info.result()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка info_tools: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/feedback", methods=["POST"])
def feedback():
    """Сохранение обратной связи (Active Learning)"""
    data = request.json or {}
    
    # Валидация
    required = ["query", "response", "rating"]
    if not all(k in data for k in required):
        return jsonify({"status": 400, "answer": f"Неполные данные. Требуются: {required}"})
    
    try:
        collector = FeedbackCollector()
        record = collector.save_feedback(
            query=data["query"],
            response=data["response"],
            rating=int(data["rating"]),
            feedback_text=data.get("feedback", ""),
            meta=data.get("meta", {})
        )
        
        # Получаем обновленную статистику
        stats = collector.get_stats()
        
        return jsonify({
            "status": 200, 
            "answer": "Feedback saved",
            "record_id": record.get("id"),
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Ошибка feedback: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/agent", methods=["POST"])
def agent_endpoint():
    """Запуск агента с поддержкой памяти"""
    data = request.json or {}
    query = data.get("query", "")
    session_id = data.get("session_id", "default")
    
    if not query:
        return jsonify({"status": 400, "answer": "Не указан query"})
    
    try:
        # Получаем или создаем память для сессии
        if session_id not in SESSIONS:
            SESSIONS[session_id] = ConversationMemory(window_size=5)
        
        memory = SESSIONS[session_id]
        
        # Запускаем агента
        result = run_agent(query, memory=memory)
        
        return jsonify({
            "status": 200,
            "answer": result.text,
            "score": result.score,
            "tokens_used": result.tokens_used,
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Ошибка agent_endpoint: {str(e)}")
        return jsonify({"status": 500, "answer": f"Ошибка: {str(e)}"})


@app.route("/health", methods=["GET"])
def health():
    """Проверка здоровья сервера"""
    return jsonify({"status": "ok"})


def run_mlflow():
    """Запуск MLflow UI в отдельном потоке"""
    try:
        import mlflow
        mlflow.set_tracking_uri("http://localhost:5000")
        # MLflow UI запускается отдельно командой: mlflow ui --port 5000
    except ImportError:
        logger.warning("MLflow не установлен")


if __name__ == "__main__":
    # Запуск MLflow в фоне
    mlflow_thread = threading.Thread(target=run_mlflow, daemon=True)
    mlflow_thread.start()
    
    logger.info("Запуск Flask API сервера на порту 5001")
    logger.info("MLflow UI доступен на http://localhost:5000")
    logger.info("API endpoints:")
    logger.info("  GET  /show_tools - список инструментов")
    logger.info("  POST /search_content - поиск контента")
    logger.info("  POST /read_file - чтение файла")
    logger.info("  POST /show_files - список файлов")
    logger.info("  POST /gen_readme - генерация README")
    logger.info("  POST /awerage_repo - оценка оформления")
    logger.info("  POST /rate_repository - оценка кода")
    logger.info("  POST /feedback - обратная связь (Active Learning)")
    logger.info("  POST /agent - умный агент с памятью")
    logger.info("  GET  /info_tools - информация")
    
    app.run(host="0.0.0.0", port=5001, debug=False)
