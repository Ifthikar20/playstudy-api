#!/usr/bin/env python3
"""
Script to view users in DynamoDB Local
"""

import boto3
import json
from tabulate import tabulate
from decimal import Decimal

# Helper for JSON serialization of Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

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

# Scan the table
response = table.scan()
users = response.get('Items', [])

if not users:
    print("No users found in the database.")
else:
    # Extract relevant fields for display
    user_data = []
    for user in users:
        user_data.append([
            user.get('id', 'N/A'),
            user.get('email', 'N/A'),
            user.get('name', 'N/A'),
            user.get('xp_points', 0),
            user.get('level', 1),
            user.get('games_played', 0),
            user.get('created_at', 'N/A')
        ])
    
    # Print table
    headers = ["ID", "Email", "Name", "XP", "Level", "Games Played", "Created At"]
    print(tabulate(user_data, headers=headers, tablefmt="grid"))
    
    print(f"\nTotal users: {len(users)}")
    
    # Save full data to JSON file (optional)
    with open('users_dump.json', 'w') as f:
        json.dump(users, f, indent=2, cls=DecimalEncoder)
    print("Full user data saved to users_dump.json")