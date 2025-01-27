from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct

class BackupSnsStack(Stack):

    def get_sns_topic_arn(self):
        return self.topic.topic_arn

    def __init__(self, scope: Construct, construct_id: str,
                 environment: str,
                 notification_emails: list,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The SNS topic
        self.topic = sns.Topic(
            self,
            f"PostgresBackupEmailTopic-{environment}",
            display_name=f"PostgresBackupEmailTopic-{environment}",
            topic_name=f"postgres-backup-email-topic-{environment}"
        )


        # Add email subscriptions
        for email in notification_emails:
            self.topic.add_subscription(
                subscriptions.EmailSubscription(email)
            )
