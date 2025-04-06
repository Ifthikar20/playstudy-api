#!/usr/bin/env python3
"""
Script to directly add a test user to DynamoDB Local
"""

import boto3
import uuid
from datetime import datetime

# Configure DynamoDB client for local
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id='fakeMyKeyId',
    aws_secret_access_key='fakeSecretAccessKey',
    endpoint_url='http://localhost:8000'
)

# Table name
table_name = 'playstudy_users'
table = dynamodb.Table(table_name)

# Create a test user
user_id = str(uuid.uuid4())
current_time = datetime.utcnow().isoformat()

user = {
    'id': user_id,
    'email': 'test@example.com',
    'name': 'Test User',
    'image': None,
    'created_at': current_time,
    'updated_at': None,
    'last_login': current_time,
    'xp_points': 150,
    'level': 2,
    'games_played': 3,
    'metadata': {}
}

# Add user to DynamoDB
table.put_item(Item=user)

print(f"Added test user to DynamoDB Local:")
print(f"- User ID: {user_id}")
print(f"- Email: {user['email']}")
print(f"- Name: {user['name']}")
print(f"- XP: {user['xp_points']}")
print(f"- Level: {user['level']}")
print("\nTo view this user, run:")
print(f"aws dynamodb get-item --table-name {table_name} --key '{{'\"id\"':'{{\"{user_id}\"}}\"}}' --endpoint-url http://localhost:8000")