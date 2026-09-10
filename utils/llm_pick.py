from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

def pick_llm(level:str):
    """
    Pick the appropriate LLM based on the specified level.
    
    Args:
        level (str) : The level of the question, can be "low", "medium", or "high".

    Returns:
        ChatOpenAI or ChatGoogleGenerativeAI: The LLM instance to be used.

    """      

    if level.lower() == "low":
        llm = ChatOpenAI(model_name="gpt-5.6-luna", temperature=0, model_kwargs={
        "reasoning_effort": "none"
        })
    elif level.lower() == "medium":
        llm = ChatOpenAI(model_name="gpt-5.6-terra", temperature=0, model_kwargs={
        "reasoning_effort": "none"
        })
    elif level.lower() == "high":
        llm = ChatOpenAI(model_name="gpt-5.6-sol", temperature=0, model_kwargs={
        "reasoning_effort": "none"
        })  

    elif level.lower() == "google":
        llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0)

    else:
        raise ValueError(f"Invalid level: {level}. Please choose from 'low', 'medium', 'high', or 'google'.")
    return llm

if __name__ == "__main__":
    llm_obj = pick_llm("medium")
    print(llm_obj.invoke("What is the capital of France?"))




