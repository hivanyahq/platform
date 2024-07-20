from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI

from query_engine.agents import initialize_agents
from query_engine.prompt_templates import retrieval_qa_chat_prompt


class QueryEngine(object):
    def __init__(
        self, neo4j_uri=None, neo4j_user=None, neo4j_password=None, openai_key=None
    ) -> None:
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.openai_key = openai_key

        # Ensure all required parameters are provided
        if not all(
            [self.neo4j_uri, self.neo4j_user, self.neo4j_password, self.openai_key]
        ):
            raise ValueError("Missing required configuration parameters")

        # First step to intialize the agents for each platform
        jira_agent, slack_agent, confluence_agent, user_agent = initialize_agents(
            self.neo4j_uri, self.neo4j_user, self.neo4j_password, self.openai_key
        )
        self.tools = [
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
        self.agent = initialize_agent(
            tools=self.tools,
            llm=ChatOpenAI(temperature=0, model_name="gpt-4"),
            agent_type=AgentType.OPENAI_FUNCTIONS,
            prompt=retrieval_qa_chat_prompt,
            verbose=True,
        )

    def ask(self, query):
        return {"response": self.agent.run(query)}


def main():
    qe = QueryEngine()  # In dev, use dotenv to set init params

    for query in [
        "Who is working on the query search using GenAI query engine?",
        "What Tejasvi is working on?",
    ]:
        print(f"Query: {query}\nResponse: {qe.ask(query)}\n")


if __name__ == "__main__":
    main()
