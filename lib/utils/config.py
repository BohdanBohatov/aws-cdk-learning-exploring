import yaml
import os
from typing import Dict, Any

class Configuration:
    def __init__(self, environment: str):
        self.environment = environment
        self.config = self._load_config()

    def _load_config(self) -> dict:
        config_path = os.path.join(
            os.path.dirname(__file__),
            f'../configs/{self.environment}.yaml'
        )
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)

    def get_config(self) -> dict:
        return self.config

    def get_vpc_config(self) -> dict:
        vpc = self.config.get('vpc', {})
        if not isinstance(vpc, dict):
                raise ValueError("VPC configuration must be a dictionary")
        if not vpc:
                raise ValueError("VPC configuration cannot be empty")
        return vpc

    def get_tags_config(self) -> Dict[str, str]:
        tags = self.config.get('tags', {})
        if not isinstance(tags, dict):
                raise ValueError("Tags configuration must be a dictionary")
        if not tags:
                raise ValueError("Tags configuration cannot be empty")
        return tags

    def get_database_config(self) -> Dict[str, str]:
        db_config = self.config.get('database', {})
        if not isinstance(db_config, dict):
                raise ValueError("Database configuration must be a dictionary")
        if not db_config:
                raise ValueError("Database configuration cannot be empty")
        return db_config

    def get_ec2_config(self) -> Dict[str, str]:
        ec2_config = self.config.get('ec2-config', {})
        if not isinstance(ec2_config, dict):
                raise ValueError("EC2 configuration must be a dictionary")
        if not ec2_config:
                raise ValueError("EC2 configuration cannot be empty")
        return ec2_config
    
    def get_azure_config(self) -> Dict[str, Any]:
        azure_config = self.config.get('azure', {})
        if not isinstance(azure_config, dict):
                raise ValueError("Azure configuration must be a dictionary")
        if not azure_config:
                raise ValueError("Azure configuration cannot be empty")
        return azure_config
    
    def get_backup_notification_emails(self) -> list:
        emails = self.config.get('postgres-backup-notification-emails', [])
        if not isinstance(emails, list):
            raise ValueError("postgres-backup-notification-emails must be a list")
        if not emails:
            raise ValueError("postgres-backup-notification-emails cannot be empty") 
        return emails