from hiVanya_V1.agents import initialize_agents
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI

def main():
    #First step to intialize the agents for each platform
    jira_agent, slack_agent, confluence_agent,user_agent = initialize_agents()
    
    #Creating main agent
    main_tools = [
        Tool(name="Jira Agent", func=lambda query: jira_agent.run(query), description="Delegates to the Jira agent."),
        Tool(name="Slack Agent", func=lambda query: slack_agent.run(query), description="Delegates to the Slack agent."),
        Tool(name="Confluence Agent", func=lambda query: confluence_agent.run(query), description="Delegates to the Confluence agent."),
        Tool(name="User Info Agent", func=lambda query: user_agent.run(query), description="Delegates to the User Info agent which will provide information for user about the id to another agents." )
    ]
    main_agent = initialize_agent(tools=main_tools, llm=ChatOpenAI(temperature=0, model_name="gpt-4"), agent_type=AgentType.OPENAI_FUNCTIONS, prompt=retrieval_qa_chat_prompt, verbose=True)
    

    # Example queries
    queries = [
        "Who is working on the query search using GenAI query engine?",
        "What Tejasvi is working on?"
    ]

    queries = ["Who is working on the query search using GenAI query engine?", "What Tejasvi is working on?"]
    for query in queries:
        response = main_agent.run(query)
        print(f"Query: {query}\nResponse: {response}\n")
        
if __name__ == "__main__":
    main()
