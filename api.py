
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.data_agent import data_agent
from langchain_core.messages import HumanMessage

app = FastAPI(title="AI Data Agent API")


class QuestionRequest(BaseModel):
    question: str


class AgentResponse(BaseModel):
    question: str
    generated_sql: str | None = None
    answer: str


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {
        "application": "AI Data Agent",
        "version": "1.0.1"
    }    


@app.post("/ask", response_model=AgentResponse)
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        response = data_agent.invoke({
            "messages": [
                HumanMessage(content=request.question)
            ],
            "route_response": ""
        })

        last_message = response["messages"][-1]

        # SQL Analyst and ETL Analyst may return
        # different result structures.
        if isinstance(last_message, dict):
            agent_result = last_message
        else:
            agent_result = {
                "final_answer": last_message.content
            }

        # SQL is optional because ETL requests
        # may not generate a SQL query.
        generated_sql = agent_result.get(
            "generated_sql_query"
        )

        # Extract the final answer.
        answer = agent_result.get("final_answer")

        # Fallback for nested message responses.
        if answer is None:
            messages = agent_result.get("messages", [])

            if messages:
                final_message = messages[-1]

                if isinstance(final_message, dict):
                    answer = final_message.get("content")
                else:
                    answer = final_message.content

        if answer is None:
            raise ValueError(
                "Agent did not return a final answer"
            )

        return AgentResponse(
            question=request.question,
            generated_sql=generated_sql,
            answer=str(answer)
        )

    except HTTPException:
        raise
    except Exception:
        # Avoid exposing database errors, credentials,
        # or internal details to API users.
        raise HTTPException(
            status_code=500,
            detail="Unable to process the request"
        )
