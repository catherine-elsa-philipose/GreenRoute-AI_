import truststore
truststore.inject_into_ssl()
import os
import sqlite3
import ssl
from datetime import datetime
from pathlib import Path

import httpx

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# =========================================
# 1. LOAD ENVIRONMENT VARIABLES
# =========================================

load_dotenv(override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()


# =========================================
# 2. INITIALIZE AI PROVIDERS
# =========================================

groq_http_client = (
    httpx.Client(
        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        timeout=20.0,
        trust_env=True
    )
    if GROQ_API_KEY else None
)

groq_client = (
    Groq(
        api_key=GROQ_API_KEY,
        http_client=groq_http_client,
        timeout=20.0,
        max_retries=0
    )
    if groq_http_client else None
)

openrouter_client = (
    OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1"
    )
    if OPENROUTER_API_KEY else None
)


# =========================================
# 3. INITIALIZE FASTAPI
# =========================================

app = FastAPI(
    title="GreenRoute AI",
    description="Explainable, Confidence-Aware Adaptive Multi-LLM Orchestration",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# PHASE 10: SQLITE DATABASE
# =========================================

DATABASE_NAME = "greenroute_history.db"


# 4. Initialize database

def initialize_database():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            task_type TEXT,
            selected_model TEXT,
            initial_model TEXT,
            fallback_used INTEGER,
            status TEXT,
            execution_time TEXT

        )
    """)

    connection.commit()
    connection.close()

    print("SQLite database initialized successfully.")


# 5. Save execution history

def save_execution(
    prompt,
    task_type,
    selected_model,
    initial_model,
    fallback_used,
    status
):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO execution_history (
            prompt,
            task_type,
            selected_model,
            initial_model,
            fallback_used,
            status,
            execution_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt,
        task_type,
        selected_model,
        initial_model,
        int(fallback_used),
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()



# 6. Retrieve recent execution history

def get_execution_history():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM execution_history
        ORDER BY id DESC
        LIMIT 10
    """)

    history = cursor.fetchall()
    connection.close()

    return history


# 7. Get total execution count

def get_total_execution_count():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM execution_history
    """)

    total = cursor.fetchone()[0]

    connection.close()

    return total



# 7. Calculate historical provider success rates

def get_provider_success_rates(task_type):

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            initial_model,
            COUNT(*) AS total_attempts,

            SUM(
                CASE
                    WHEN status = 'Success'
                         AND fallback_used = 0
                    THEN 1
                    ELSE 0
                END
            ) AS successful_attempts

        FROM execution_history

        WHERE task_type = ?
          AND initial_model IN ('Groq', 'OpenRouter')

        GROUP BY initial_model
    """, (task_type,))

    rows = cursor.fetchall()

    connection.close()

    performance = {}

    for provider, total, successful in rows:

        success_rate = successful / total if total else 0

        performance[provider] = {
            "total_attempts": total,
            "successful_attempts": successful,
            "success_rate": success_rate
        }

    return performance


# Initialize database when backend starts

initialize_database()


# =========================================
# 8. REQUEST MODEL
# =========================================

class PromptRequest(BaseModel):

    prompt: str


# =========================================
# PHASE 5: PROMPT UNDERSTANDING
# =========================================

def classify_task(prompt):

    prompt = prompt.lower()

    coding_keywords = [
        "code", "python", "javascript", "program",
        "function", "debug", "error", "sql",
        "html", "css", "api"
    ]

    writing_keywords = [
        "write", "essay", "email", "story",
        "article", "paragraph", "rewrite",
        "summarize", "content"
    ]

    reasoning_keywords = [
        "explain", "why", "how", "analyze",
        "compare", "difference", "reason",
        "calculate", "solve", "logic"
    ]

    if any(word in prompt for word in coding_keywords):
        return "Coding"

    elif any(word in prompt for word in writing_keywords):
        return "Writing"

    elif any(word in prompt for word in reasoning_keywords):
        return "Reasoning"

    else:
        return "General"


# =========================================
# PHASE 6: MODEL CAPABILITY REGISTRY
# =========================================

model_capabilities = {

    "Groq": {
        "Coding": 0.95,
        "Writing": 0.88,
        "Reasoning": 0.90,
        "General": 0.92
    },

    "OpenRouter": {
        "Coding": 0.90,
        "Writing": 0.93,
        "Reasoning": 0.95,
        "General": 0.90
    }

}


# =========================================
# PHASE 10: ADAPTIVE MODEL SELECTION
# =========================================

def select_best_model(task_type):

    # Get historical performance for this task
    performance = get_provider_success_rates(task_type)

    final_scores = {}

    # Weight given to fixed capability scores
    capability_weight = 0.80

    # Weight given to historical success rates
    history_weight = 0.20

    for provider in model_capabilities:

        capability_score = model_capabilities[provider][task_type]

        # Use neutral 50% when no history exists
        if provider in performance:

            historical_rate = performance[provider]["success_rate"]

        else:

            historical_rate = 0.50

        # Combine capability and historical performance
        final_score = (
            capability_score * capability_weight
            +
            historical_rate * history_weight
        )

        final_scores[provider] = final_score

        print(
            provider,
            "Capability:", capability_score,
            "Historical success rate:", historical_rate,
            "Final score:", round(final_score, 4)
        )

    selected_model = max(
        final_scores,
        key=final_scores.get
    )

    selected_score = final_scores[selected_model]

    return selected_model, selected_score, performance


# =========================================
# PHASE 8: GROQ RESPONSE GENERATION
# =========================================

def generate_groq_response(prompt):

    if not groq_client:

        raise RuntimeError(
            "Groq API key is missing. Check your .env file."
        )

    response = groq_client.chat.completions.create(

        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        max_tokens=1024

    )

    return response.choices[0].message.content


# =========================================
# PHASE 8: OPENROUTER RESPONSE GENERATION
# =========================================

def generate_openrouter_response(prompt):

    if not openrouter_client:

        raise RuntimeError(
            "OpenRouter API key is missing. Check your .env file."
        )

    response = openrouter_client.chat.completions.create(

        model="openrouter/free",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        max_tokens=1024

    )

    return response.choices[0].message.content


# =========================================
# PHASE 9: FALLBACK MECHANISM
# =========================================

def generate_ai_response(prompt, selected_model):

    providers = {

        "Groq": generate_groq_response,

        "OpenRouter": generate_openrouter_response

    }

    fallback_model = (
        "OpenRouter"
        if selected_model == "Groq"
        else "Groq"
    )

    provider_order = [
        selected_model,
        fallback_model
    ]

    errors = []
    attempts = []

    for provider in provider_order:

        try:

            print("Attempting provider:", provider)

            response = providers[provider](prompt)

            if not response or not response.strip():

                raise RuntimeError(
                    "Provider returned an empty response."
                )

            attempts.append({

                "provider": provider,
                "status": "success",
                "message": "Response generated successfully."

            })

            print("Successful provider:", provider)

            return {

                "response": response,

                "actual_model": provider,

                "initial_model": selected_model,

                "fallback_used": provider != selected_model,

                "attempts": attempts,

                "errors": errors

            }

        except Exception as error:

            error_message = (
    f"{type(error).__name__}: {repr(error)}"
)
            print(
                "Provider",
                provider,
                "failed:",
                error_message
            )

            errors.append({

                "provider": provider,
                "error": error_message

            })

            attempts.append({

                "provider": provider,
                "status": "failed",
                "message": error_message

            })

    raise RuntimeError(
        "All AI providers failed. Details: " + str(errors)
    )


# =========================================
# PHASE 4-10: MAIN API ROUTE
# =========================================

@app.post("/api/route")
def process_prompt(request: PromptRequest):

    user_prompt = request.prompt.strip()

    if not user_prompt:

        raise HTTPException(
            status_code=400,
            detail="Please enter a prompt."
        )

    # Step 1: Understand the prompt
    task_type = classify_task(user_prompt)

    # Step 2: Select provider using adaptive memory
    selected_model, selected_score, performance = (
        select_best_model(task_type)
    )

    # Step 3: Generate response with fallback
    try:

        result = generate_ai_response(
            user_prompt,
            selected_model
        )

    except Exception as error:

        # Record failed execution in SQLite
        try:

            save_execution(
                prompt=user_prompt,
                task_type=task_type,
                selected_model="None",
                initial_model=selected_model,
                fallback_used=False,
                status="Failed"
            )

            print("Failed execution saved to SQLite.")

        except Exception as database_error:

            print(
                "Database saving failed:",
                database_error
            )

        raise HTTPException(
            status_code=502,
            detail=str(error)
        )

    actual_model = result["actual_model"]

    # Step 4: Save successful execution
    try:

        save_execution(

            prompt=user_prompt,

            task_type=task_type,

            selected_model=actual_model,

            initial_model=selected_model,

            fallback_used=result["fallback_used"],

            status="Success"

        )

        print("Execution saved to SQLite database.")

    except Exception as database_error:

        print(
            "Database saving failed:",
            database_error
        )

    # Step 5: Build adaptive decision trace
    decision_trace = (

        f"Task classified as {task_type}. "

        f"Groq capability score: "
        f"{model_capabilities['Groq'][task_type]}. "

        f"OpenRouter capability score: "
        f"{model_capabilities['OpenRouter'][task_type]}. "

        f"Groq historical success rate: "
        f"{performance.get('Groq', {}).get('success_rate', 0.5):.2%}. "

        f"OpenRouter historical success rate: "
        f"{performance.get('OpenRouter', {}).get('success_rate', 0.5):.2%}. "

        f"Initially selected provider: {selected_model}. "

        f"Final provider used: {actual_model}. "

        f"Adaptive selection score: {selected_score:.4f}. "

    )

    if result["fallback_used"]:

        decision_trace += (
            "Fallback activated because the primary provider failed."
        )

    else:

        decision_trace += (
            "Primary provider generated the response successfully."
        )

    # Step 6: Return result to frontend
    return {

        "response": result["response"],

        "selected_model": actual_model,

        "initial_model": selected_model,

        "task_type": task_type,

        "confidence": selected_score,

        "fallback_used": result["fallback_used"],

        "attempts": result["attempts"],

        "errors": result["errors"],

        "decision_trace": decision_trace

    }


# =========================================
# PHASE 10: EXECUTION HISTORY API
# =========================================


@app.get("/api/history")
def read_execution_history():

    history = get_execution_history()

    return {
        "total_records": get_total_execution_count(),

        "history": [
            {
                "id": row[0],
                "prompt": row[1],
                "task_type": row[2],
                "selected_model": row[3],
                "initial_model": row[4],
                "fallback_used": bool(row[5]),
                "status": row[6],
                "execution_time": row[7]
            }
            for row in history
        ]
    }



# =========================================
# PHASE 10: ADAPTIVE MEMORY API
# =========================================

@app.get("/api/performance")
def read_provider_performance():

    task_types = [
        "Coding",
        "Writing",
        "Reasoning",
        "General"
    ]

    performance_data = {}

    for task_type in task_types:

        performance_data[task_type] = (
            get_provider_success_rates(task_type)
        )

    return {
        "provider_performance": performance_data
    }


# =========================================
# PHASE 12: DASHBOARD STATISTICS API
# =========================================

@app.get("/api/stats")
def get_dashboard_stats():

    connection = sqlite3.connect(DATABASE_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_requests,
            SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) AS successful_requests,
            SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_requests,
            SUM(CASE WHEN fallback_used = 1 THEN 1 ELSE 0 END) AS fallback_count
        FROM execution_history
    """)

    row = cursor.fetchone()
    connection.close()

    total_requests = row[0] or 0
    successful_requests = row[1] or 0
    failed_requests = row[2] or 0
    fallback_count = row[3] or 0

    success_rate = (
        successful_requests / total_requests * 100
        if total_requests > 0
        else 0.0
    )

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": success_rate,
        "fallback_count": fallback_count
    }


# =========================================
# PHASE 11: SERVE THE EXISTING FRONTEND
# =========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIRECTORY = PROJECT_ROOT / "frontend"

app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIRECTORY), html=True),
    name="frontend"
)
