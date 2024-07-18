from langchain.prompts import FewShotPromptTemplate, PromptTemplate

few_shot_examples = [
    {
        "query": "What is Tejasvi currently working on?",
        "context": """
1. For this query go to jira_agent, in that first go to Query Atlassian Users do similarity search get the id of all the Tejasvi.
2. In Jira agent then go to jira issue, stories and project get all the matches jira issues, stories and project where assignee_id matches to the id got in first step.
3. Retrieve and summarize the information according to descending id of created date .
4. Also perform relevent cypher queries to get the data and then combine the answer. 
""",
        "cypher_queries": [
            "MATCH (u:atlassian_user {display_name: 'Tejasvi'}) RETURN u.id",
            "MATCH (i:jira_issue {assignee_id: '{id}'}) RETURN i",
            "MATCH (s:jira_story {assignee_id: '{id}'}) RETURN s",
        ],
    },
    {
        "query": "Who is working on the project query search using GenAI?",
        "context": """
1. Search for Jira issues, stories, or comments mentioning 'GenAI'.
2. Retrieve the assignee_id for these issues or stories.
3. Search for the corresponding user in Atlassian users.
""",
        "cypher_queries": [
            "MATCH (i:jira_issue) WHERE i.description CONTAINS 'GenAI' RETURN i.assignee_id",
            "MATCH (i:jira_comment) WHERE i.description CONTAINS 'GenAI' RETURN i.author_id",
            "MATCH (u:atlassian_user {id: '{assignee_id}'}) RETURN u.display_name",
        ],
    },
]

example_prompt = PromptTemplate(
    input_variables=["query", "context"], template="Query: {query}\nContext: {context}"
)

retrieval_qa_chat_prompt = FewShotPromptTemplate(
    examples=few_shot_examples,
    example_prompt=example_prompt,
    input_variables=["context"],
    prefix=f"""
You are an intelligent assistant for a company. You understand every jargon of the tech world related to but not limited to Jira, Slack, etc. You should combine context from various sources and make it more reliable.
Important Instruction: Never return any user id or sensitive ids. You can return email id of a queried person.
The graph database contains nodes and relationships that represent various entities and their interactions within a company's Confluence, Slack, and Jira systems.

Nodes:
- confluence_space: Represents a Confluence space with properties such as id, key, name, and type.
- confluence_page: Represents a Confluence page with properties like id, type, title, author_id, author_name, created, parent_id, space_id, and jira_issues.
- slack_user: Represents a Slack user with properties like id, team_id, name, first_name, last_name, title, email, and is_admin.
- slack_channel: Represents a Slack channel with properties such as id, name, creator, purpose_value, is_private, num_members, and created.
- slack_message: Represents a Slack message with properties like id, user, text, team, channel_id, and created.
- jira_project: Represents a Jira project with properties like id, project_key, title, description, and assignee_id.
- jira_issue: Represents a Jira issue with properties such as id, assignee_id, display_name,created, creator_id, description, issue_type, key, parent_key, project_id, status, title, and updated.
- jira_comment: Represents a Jira comment with properties like id, author_id, text, issue_id, and created.
- jira_sprint: Represents a Jira sprint with properties such as id, name, start_date, end_date, board_id, and state.

Relationships:
- atlassian_user: 'id' is connected to 'author_id' of 'jira_comment', 'assignee_id' and 'creator_id' of 'jira_issues'.
- slack_user: 'id' matches to 'slack_message' 'user' and 'slack_channel' 'creator'.

Indexed properties:
- atlassian_user: ['id', 'display_name', 'email']
- jira_comment: ['text', 'author_id', 'issue_id']
- jira_issue: ['description', 'title', 'issue_type', 'status', 'created', 'parent_key', 'project_id', 'key', 'creator_id', 'assignee_id','display_name']
- jira_sprint: ['name', 'state', 'start_date', 'end_date', 'board_id']
- jira_project: ['project_key', 'id', 'title']
- confluence_space: ['name', 'key']
- confluence_page: ['title', 'content', 'author_name', 'author_id', 'created']
- slack_user: ['id', 'name', 'last_name']
- slack_channel: ['id', 'name', 'purpose_value', 'creator', 'created', 'num_members']
- slack_message: ['text', 'user', 'created', 'team', 'channel_id']

Examples:
""",
    suffix="Answer the question in detail based on the provided context: {context}",
    example_separator="\n\n",
)

CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database and do similarity search.
Instructions:
Do the similarity search first on the node and after getting the node in which may be there is relevant data do the cypher query
Schema:
The graph database contains nodes and relationships that represent various entities and their interactions within a company's Confluence, Slack, and Jira systems.

Nodes:
- confluence_space: Represents a Confluence space with properties such as id, key, name, and type.
- confluence_page: Represents a Confluence page with properties like id, type, title, author_id, author_name, created, parent_id, space_id, and jira_issues.
- slack_user: Represents a Slack user with properties like id, team_id, name, first_name, last_name, title, email, and is_admin.
- slack_channel: Represents a Slack channel with properties such as id, name, creator, purpose_value, is_private, num_members, and created.
- slack_message: Represents a Slack message with properties like id, user, text, team, channel_id, and created.
- jira_project: Represents a Jira project with properties like id, project_key, title, description, and assignee_id.
- jira_issue: Represents a Jira issue with properties such as id, assignee_id, display_name,created, creator_id, description, issue_type, key, parent_key, project_id, status, title, and updated.
- jira_comment: Represents a Jira comment with properties like id, author_id, text, issue_id, and created.
- jira_sprint: Represents a Jira sprint with properties such as id, name, start_date, end_date, board_id, and state.
- atlassian_user: Represnts a JIra and confluence user with propertiessuch ad id, display_name, email

Relationships:
- slack_user: 'id' matches to 'slack_message' 'user' and 'slack_channel' 'creator'.
- atlassian_user has relationship worked_on_by and works_on with jira_issue

Indexed properties:
- atlassian_user: ['id', 'display_name', 'email']
- jira_comment: ['text', 'author_id', 'issue_id']
- jira_issue: ['description', 'title', 'issue_type', 'status', 'created', 'parent_key', 'project_id', 'key', 'creator_id', 'assignee_id','display_name']
- jira_sprint: ['name', 'state', 'start_date', 'end_date', 'board_id']
- jira_project: ['project_key', 'id', 'title']
- confluence_space: ['name', 'key']
- confluence_page: ['title', 'content', 'author_name', 'author_id', 'created']
- slack_user: ['id', 'name', 'last_name']
- slack_channel: ['id', 'name', 'purpose_value', 'creator', 'created', 'num_members']
- slack_message: ['text', 'user', 'created', 'team', 'channel_id']

Note: Do not include any explanations or apologies in your responses.

The question is:
{question} 

Important: In the generated Cypher query, the RETURN statement must explicitly include the property values used in the query's filtering condition, alongside the main information requested from the original question.

"""
