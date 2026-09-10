from agents.data_agent import data_agent
from langchain_core.messages import HumanMessage

if __name__ == "__main__":
    # response = data_agent.invoke(
    #     {"messages":[HumanMessage(content="I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv folder")],
    #      "route_response": ""}
    # )
    

    # response = data_agent.invoke(
    #          {"messages":[HumanMessage(content=f"""
    #             I want to transform the data stored in the 'e:\\Data_Agent\\data\\extract\\extracted_data.csv' file 
    #             and save the transformed data in the 'e:\\Data_Agent\\data\\transform' folder in the csv format.
    #             The transformation should filter the data to show bulbasaur pokemon only.""")],
    #          "route_response": ""}
    #     )    


    response = data_agent.invoke(
        {"messages":[HumanMessage(content="What are the different types of Payment Methods we have in our database")],
         "route_response": ""}
    )
        

print(response)