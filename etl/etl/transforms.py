import os
import csv
import json
import logging


# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Airbyte2jsonlTransformer(object):
    def __init__(self):
        self.s3_files_field_map = {
            "confluence/space": {
                "id": "data['id']",
                "key": "data['key']",
                "name": "data['name']",
                "type": "data['type']",
            },
            "confluence/pages": {
                "id": "data['id']",
                "type": "data['type']",
                "title": "data['title']",
                "author_id": "data['history']['createdBy']['accountId']",
                "author_name": "data['history']['createdBy']['displayName']",
                "created": "data['history']['createdDate']",
            },
            "jira/users": {
                "id": "data['accountId']",
                "email": "data['emailAddress']",
                "display_name": "data['displayName']",
            },
            "jira/projects": {
                "id": "data['id']",
                "project_key": "data['key']",
                "title": "data['name']",
                "description": "data['description']",
                "assignee_id": "data['lead']['accountId']",
            },
            "jira/boards": {
                "id": "data['id']",
                "project_id": "data['projectId']",
            },
            "jira/sprints": {
                "id": "data['id']",
                "name": "data['name']",
                "start_date": "data['startDate']",
                "end_date": "data['endDate']",
                "board_id": "data['boardId']",
                "state": "data['state']",
            },
            "jira/issues": {
                "assignee_id": "data['fields']['assignee']['accountId']",
                "created": "data['fields']['created']",
                "creator_id": "data['fields']['creator']['accountId']",
                "description": "data['fields']['issuetype']['description']",
                "id": "data['id']",
                "issue_type": "data['fields']['issuetype']['name']",
                "key": "data['key']",
                "parent_key": "data['fields']['parent']['key']",
                "project_id": "data['fields']['project']['id']",
                "status": "data['fields']['status']['statusCategory']['name']",
                "title": "data['fields']['summary']",
                "updated": "data['fields']['updated']",
            },
            "jira/issue_comments": {
                "id": "data['id']",
                "author_id": "data['author']['accountId']",
                "text": "','.join([', '.join([x['text'] for x in ic['content']]) for ic in data['body'].get('content', [])])",
                "issue_id": "data['issueId']",
                "created": "data['created']",
            },
            "jira/sprint_issues": {
                "sprint_id": "data['sprintId']",
                "issue_id": "data['issueId']",
            },
            "slack/channels": {
                "id": "data['id']",
                "name": "data['name']",
                "creator": "data['creator']",
                "purpose_value": "data['purpose']['value']",
                "is_private": "data['is_private']",
                "num_members": "data['num_members']",
                "created": "data['created']",
            },
            "slack/channel_messages": {
                "id": "data['client_msg_id']",
                "user": "data['user']",
                "text": "data['text']",
                "team": "data['team']",
                "channel_id": "data['channel_id']",
                "created": "data['ts']",
            },
            "slack/users": {
                "id": "data['id']",
                "team_id": "data['team_id']",
                "name": "data['real_name']",
                "first_name": "data['profile']['first_name']",
                "last_name": "data['profile']['last_name']",
                "title": "data['profile']['title']",
                "email": "data['profile']['email']",
                "is_admin": "data['is_admin']",
            },
        }

    def transform_airbyte_row(self, data, mapkey):
        """
        Evaluates expressions from fieldmap using the provided data dict for eval.
        """
        evaluated_values = {}
        for key, path in self.s3_files_field_map[mapkey].items():
            try:
                evaluated_values[key] = eval(path, {"data": data})
            except KeyError:
                evaluated_values[key] = None
        return evaluated_values

    def transform_airbyte2jsonl_format(self, source_file, output_file, mapkey):
        """
        Only fields defined in s3_files_field_map are transformed.
        """
        with open(output_file, "w") as fh:
            with open(source_file, "r", newline="") as csv_file:
                reader = csv.DictReader(
                    csv_file,
                    fieldnames=[
                        "_airbyte_ab_id",
                        "_airbyte_emitted_at",
                        "_airbyte_data",
                    ],
                )
                next(reader)
                for row in reader:
                    data = self.transform_airbyte_row(
                        json.loads(row["_airbyte_data"]), mapkey
                    )
                    fh.write(f"{json.dumps(data)}\n")
        logger.info(f"Generated {output_file}")

    def can_transform(self, mapkey):
        return mapkey in self.s3_files_field_map


class GraphGeneratorBase:
    def __init__(self):
        self.PROCESSORS = None  # Defined by derived classes

    def _read_lines(self, filepath):
        # Returns generator to read the file line by line
        with open(filepath, "r") as fh:
            for line in fh:
                yield (json.loads(line))

    def generate_graph_schema_format_data_files(
        self, input_directory, output_directory
    ):
        """
        Generates JSONL files one per file_type, with labels and relationships.
        files_directory has jsonl's, one per file_type(users, issues, issue_comments etc)
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        for data_type, processor in self.PROCESSORS.items():
            input_filepath = f"{input_directory}/{data_type}.jsonl"
            if not os.path.exists(input_filepath):
                logger.warning(
                    f"Input file not found: {input_filepath}, skipping {data_type}"
                )
                continue

            output_filepath = f"{output_directory}/{data_type}_data.jsonl"
            with open(output_filepath, "w") as fh:
                for line in processor(input_directory):
                    fh.write(f"{json.dumps(line)}\n")
            logger.info(f"Generated {output_filepath}")


class ConfluenceGraphGenerator(GraphGeneratorBase):
    def __init__(self):
        self.PROCESSORS = {
            "space": self._generate_space_node_and_relationships,
            "pages": self._generate_pages_node_and_relationships,
        }

    def _generate_space_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/space.jsonl"):
            yield {"type": "node", "label": "confluence_space", "properties": row}

    def _generate_pages_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/pages.jsonl"):
            yield {"type": "node", "label": "confluence_page", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "atlassian_user", "id": row["author_id"]},
                "end_node": {"label": "confluence_page", "id": row["id"]},
                "relationship": "creates",
            }

            if "parent_id" in row:
                yield {
                    "type": "relationship",
                    "start_node": {"label": "confluence_page", "id": row["parent_id"]},
                    "end_node": {"label": "confluence_page", "id": row["id"]},
                    "relationship": "contains",
                }

            if "space_id" in row:
                yield {
                    "type": "relationship",
                    "start_node": {"label": "confluence_space", "id": row["space_id"]},
                    "end_node": {"label": "confluence_page", "id": row["id"]},
                    "relationship": "contains",
                }

            if "jira_issues" in row:
                for issue in row["jira_issues"]:
                    yield {
                        "type": "relationship",
                        "start_node": {"label": "confluence_page", "id": row["id"]},
                        "end_node": {"label": "jira_issue", "id": issue},
                        "relationship": "discusses",
                    }


class SlackGraphGenerator(GraphGeneratorBase):
    def __init__(self):
        self.PROCESSORS = {
            "users": self._generate_users_node_and_relationships,
            "channels": self._generate_channels_node_and_relationships,
            "channel_messages": self._generate_channel_messages_node_and_relationships,
        }

    def _generate_users_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/users.jsonl"):
            yield {"type": "node", "label": "slack_user", "properties": row}

    def _generate_channels_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/channels.jsonl"):
            yield {"type": "node", "label": "slack_channel", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "slack_user", "id": row["creator"]},
                "end_node": {"label": "slack_channel", "id": row["id"]},
                "relationship": "creates",
            }

    def _generate_channel_messages_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/channel_messages.jsonl"):
            yield {"type": "node", "label": "slack_message", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "slack_user", "id": row["user"]},
                "end_node": {"label": "slack_message", "id": row["id"]},
                "relationship": "creates",
            }
            yield {
                "type": "relationship",
                "start_node": {"label": "slack_channel", "id": row["channel_id"]},
                "end_node": {"label": "slack_message", "id": row["id"]},
                "relationship": "contains",
            }


class JiraGraphGenerator(GraphGeneratorBase):
    def __init__(self):
        self.PROCESSORS = {
            "boards": self._generate_boards_node_and_relationships,
            "issues": self._generate_issues_node_and_relationships,
            "issue_comments": self._generate_issue_comments_node_and_relationships,
            "projects": self._generate_projects_node_and_relationships,
            "sprints": self._generate_sprints_node_and_relationships,
            "sprint_issues": self._generate_sprint_issues_node_and_relationships,
            "users": self._generate_users_node_and_relationships,
        }

    def _generate_users_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/users.jsonl"):
            yield {"type": "node", "label": "atlassian_user", "properties": row}

    def _generate_projects_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/projects.jsonl"):
            yield {"type": "node", "label": "jira_project", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "atlassian_user", "id": row["assignee_id"]},
                "end_node": {"label": "jira_project", "id": row["id"]},
                "relationship": "owns",
            }

    def _generate_issues_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/issues.jsonl"):
            yield {"type": "node", "label": "jira_issue", "properties": row}
            if row["creator_id"]:
                yield {
                    "type": "relationship",
                    "start_node": {
                        "label": "atlassian_user",
                        "account_id": row["creator_id"],
                    },
                    "end_node": {"label": "jira_issue", "id": row["id"]},
                    "relationship": "creates",
                }
            if row["assignee_id"]:
                yield {
                    "type": "relationship",
                    "start_node": {"label": "atlassian_user", "id": row["assignee_id"]},
                    "end_node": {"label": "jira_issue", "id": row["id"]},
                    "relationship": "works_on",
                }
                yield {
                    "type": "relationship",
                    "start_node": {"label": "jira_issue", "id": row["id"]},
                    "end_node": {"label": "atlassian_user", "id": row["assignee_id"]},
                    "relationship": "worked_on_by",
                }

    def _generate_issue_comments_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/issue_comments.jsonl"):
            yield {"type": "node", "label": "jira_comment", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "atlassian_user", "id": row["author_id"]},
                "end_node": {"label": "jira_comment", "id": row["id"]},
                "relationship": "creates",
            }
            yield {
                "type": "relationship",
                "start_node": {"label": "jira_issue", "id": row["issue_id"]},
                "end_node": {"label": "jira_comment", "id": row["id"]},
                "relationship": "contains",
            }

    def _generate_boards_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/boards.jsonl"):
            yield {"type": "node", "label": "jira_board", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "jira_project", "id": row["project_id"]},
                "end_node": {"label": "jira_board", "id": row["id"]},
                "relationship": "contains",
            }

    def _generate_sprints_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/sprints.jsonl"):
            yield {"type": "node", "label": "jira_sprint", "properties": row}
            yield {
                "type": "relationship",
                "start_node": {"label": "jira_board", "id": row["board_id"]},
                "end_node": {"label": "jira_sprint", "id": row["id"]},
                "relationship": "contains",
            }

    def _generate_sprint_issues_node_and_relationships(self, file_dir):
        for row in self._read_lines(f"{file_dir}/sprint_issues.jsonl"):
            yield {
                "type": "relationship",
                "start_node": {"label": "jira_sprint", "id": row["sprint_id"]},
                "end_node": {"label": "jira_issue", "id": row["issue_id"]},
                "relationship": "contains",
            }
