import warnings
from langchain._api import LangChainDeprecationWarning
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_retrieval_chain, GraphCypherQAChain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.graphs import Neo4jGraph
from langchain.prompts import PromptTemplate

from query_engine.embeddings import Neo4jEmbeddingManager
from query_engine.prompt_templates import (
    retrieval_qa_chat_prompt,
    CYPHER_GENERATION_TEMPLATE,
)

warnings.simplefilter("ignore", category=LangChainDeprecationWarning)


def create_chain(retriever, retrieval_qa_chat_prompt, api_key):
    # Creating retrieveal chain for each tool
    llm = ChatOpenAI(temperature=0, model_name="gpt-4", api_key=api_key)
    combine_documents_chain = create_stuff_documents_chain(
        llm, retrieval_qa_chat_prompt
    )
    return create_retrieval_chain(
        retriever=retriever, combine_docs_chain=combine_documents_chain
    )


def initialize_agents(neo4j_url, neo4j_user, neo4j_password, openai_key):
    embedding_manager = Neo4jEmbeddingManager(
        neo4j_url, neo4j_user, neo4j_password, openai_key
    )
    chains = {}
    labels = [
        "atlassian_user",
        "jira_comment",
        "jira_issue",
        "jira_sprint",
        "jira_project",
        "confluence_space",
        "confluence_page",
        "slack_channel",
        "slack_user",
        "slack_message",
    ]

    # Creating retrieveal chains for tool mentioned in labels
    for label in labels:
        #embedding_manager.update_embeddings_for_neo4j(label)

        retriever = embedding_manager.get_retriever(label)
        print("created index of:", label)
        chains[label] = create_chain(
            retriever.as_retriever(), retrieval_qa_chat_prompt, openai_key
        )

    CYPHER_GENERATION_PROMPT = PromptTemplate(
        input_variables=["question"], template=CYPHER_GENERATION_TEMPLATE
    )

    # Creating cypher query tool
    graph = Neo4jGraph(url=neo4j_url, username=neo4j_user, password=neo4j_password)

    graph.refresh_schema()
    graphChain = GraphCypherQAChain.from_llm(
        cypher_prompt=CYPHER_GENERATION_PROMPT,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key),
        graph=graph,
        verbose=True,
    )

    # Creating Jira tools for jira agent
    jira_tools = [
        Tool(
            name="Query Jira Comments",
            func=lambda query: chains["jira_comment"].invoke({"input": query}),
            description="Query information about Jira comments. Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Jira Issues",
            func=lambda query: chains["jira_issue"].invoke({"input": query}),
            description="Query information about Jira issues.Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Jira Sprints",
            func=lambda query: chains["jira_sprint"].invoke({"input": query}),
            description="Query information about Jira sprints.Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Jira Projects",
            func=lambda query: chains["jira_project"].invoke({"input": query}),
            description="Query information about Jira projects. Get top 10 relevant results with similarity search and contextual serach",
        ),
        #  Tool(
        #     name="Query Atlassian Users",
        #     func=lambda query: atlassian_user_chain.invoke({"input": query}),
        #     description="Query information about Atlassian users.Get top 10 relevant results with similarity search and contextual serach"
        # ),
        Tool(
            name="Direct Cypher Query",
            func=lambda query: graphChain.invoke({"query": query}),
            description="Execute a direct Cypher query on the Neo4j database. After getting all the relevant information from other tools doing similarity search.",
        ),
    ]

    # Creating Slack tools for Slack agent
    slack_tools = [
        Tool(
            name="Query Slack Messages",
            func=lambda query: chains["slack_message"].invoke({"input": query}),
            description="Query information about Slack messages. Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Slack Users",
            func=lambda query: chains["slack_user"].invoke({"input": query}),
            description="Query information about Slack users.Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Slack Channels",
            func=lambda query: chains["slack_channel"].invoke({"input": query}),
            description="Query information about Slack channels.Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Direct Cypher Query",
            func=lambda query: graphChain.invoke({"query": query}),
            description="Execute a direct Cypher query on the Neo4j database. After getting all the relevant information from other tools doing similarity search.",
        ),
    ]

    # Creating Confluence tools for Confluence agent
    confluence_tools = [
        Tool(
            name="Query Confluence Pages",
            func=lambda query: chains["confluence_page"].invoke({"input": query}),
            description="Query information about Confluence pages.Get top 10 relevant results with similarity search and contextual serach",
        ),
        Tool(
            name="Query Confluence Spaces",
            func=lambda query: chains["confluence_space"].invoke({"input": query}),
            description="Query information about Confluence spaces.Get top 10 relevant results with similarity search and contextual serach",
        ),
        # Tool(
        #     name="Query Atlassian Users",
        #     func=lambda query: atlassian_user_chain.invoke({"input": query}),
        #     description="Query information about Atlassian users."
        # ),
        Tool(
            name="Direct Cypher Query for Confluence Tool",
            func=lambda query: graphChain.invoke({"query": query}),
            description="Execute a direct Cypher query on the Neo4j database. After getting all the relevant information from other tools doing similarity search.",
        ),
    ]

    # Creating User tools to query among user information across all platforms
    user_tools = [
        Tool(
            name="Query Atlassian Users",
            func=lambda query: chains["confluence_space"].invoke({"input": query}),
            description="Query information about Atlassian users with id find the display_name of the person.",
        ),
        Tool(
            name="Query Slack Users",
            func=lambda query: chains["atlassian_user"].invoke({"input": query}),
            description="Query information about Slack users.",
        ),
        Tool(
            name="Direct Cypher Query for User",
            func=lambda query: graphChain.invoke({"query": query}),
            description="Execute a direct Cypher query on the Neo4j database to get the user if you have id or vice cersa. After getting all the relevant information from other tools doing similarity search.",
        ),
    ]

    # Initializing the agents
    jira_agent = initialize_agent(
        tools=jira_tools,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key),
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prompt=retrieval_qa_chat_prompt,
        verbose=True,
    )
    slack_agent = initialize_agent(
        tools=slack_tools,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key),
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prompt=retrieval_qa_chat_prompt,
        verbose=True,
    )
    confluence_agent = initialize_agent(
        tools=confluence_tools,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key),
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prompt=retrieval_qa_chat_prompt,
        verbose=True,
    )
    user_agent = initialize_agent(
        tools=user_tools,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4", api_key=openai_key),
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prompt=retrieval_qa_chat_prompt,
        verbose=True,
    )
    return jira_agent, slack_agent, confluence_agent, user_agent


def main():
    jira_agent, slack_agent, confluence_agent, user_agent = initialize_agents()
    main_tools = [
        Tool(
            name="Jira Agent",
            func=lambda query: jira_agent.run(query),
            description="Delegates to the Jira agent.",
        ),
        Tool(
            name="Slack Agent",
            func=lambda query: slack_agent.run(query),
            description="Delegates to the Slack agent.",
        ),
        Tool(
            name="Confluence Agent",
            func=lambda query: confluence_agent.run(query),
            description="Delegates to the Confluence agent.",
        ),
        Tool(
            name="User Info Agent",
            func=lambda query: user_agent.run(query),
            description="Delegates to the User Info agent which will provide information for user about the id to another agents.",
        ),
    ]
    main_agent = initialize_agent(
        tools=main_tools,
        llm=ChatOpenAI(temperature=0, model_name="gpt-4"),
        agent_type=AgentType.OPENAI_FUNCTIONS,
        prompt=retrieval_qa_chat_prompt,
        verbose=True,
    )
    queries = [
        "Who is working on the query search using GenAI query engine?",
        "What Tejasvi is working on?",
    ]
    for query in queries:
        response = main_agent.run(query)
        print(f"Query: {query}\nResponse: {response}\n")


if __name__ == "__main__":
    main()
