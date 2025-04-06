import os
import sys
import time
import boto3
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from app.core.config import get_settings

# Load environment variables
load_dotenv()

# Set environment for local development
os.environ["AWS_ACCESS_KEY_ID"] = "fakeMyKeyId"
os.environ["AWS_SECRET_ACCESS_KEY"] = "fakeSecretAccessKey"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["DYNAMODB_ENDPOINT_URL"] = "http://localhost:8000"
os.environ["SECRET_KEY"] = "thisisasecretkey1234567890thisisasecretkey"
os.environ["DEBUG"] = "True"
# Add your Google OAuth credentials here
os.environ["GOOGLE_CLIENT_ID"] = "YOUR_GOOGLE_CLIENT_ID_HERE"
os.environ["GOOGLE_CLIENT_SECRET"] = "YOUR_GOOGLE_CLIENT_SECRET_HERE"

# Create DynamoDB tables
def create_tables():
    """Create DynamoDB tables if they don't exist"""
    settings = get_settings()
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url='http://localhost:8000'  # DynamoDB Local endpoint
        )
        
        # Check if tables exist
        existing_tables = [table.name for table in dynamodb.tables.all()]
        
        # Create Users table
        if settings.USERS_TABLE not in existing_tables:
            try:
                table = dynamodb.create_table(
                    TableName=settings.USERS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                        {'AttributeName': 'email', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'email-index',
                            'KeySchema': [
                                {'AttributeName': 'email', 'KeyType': 'HASH'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                print(f"Table {settings.USERS_TABLE} created successfully.")
            except Exception as e:
                print(f"Error creating table {settings.USERS_TABLE}: {str(e)}")
        else:
            print(f"Table {settings.USERS_TABLE} already exists.")
        
        # Create Games table
        if settings.GAMES_TABLE not in existing_tables:
            try:
                table = dynamodb.create_table(
                    TableName=settings.GAMES_TABLE,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                print(f"Table {settings.GAMES_TABLE} created successfully.")
            except Exception as e:
                print(f"Error creating table {settings.GAMES_TABLE}: {str(e)}")
        else:
            print(f"Table {settings.GAMES_TABLE} already exists.")
        
        # Create User Stats table
        if settings.USER_STATS_TABLE not in existing_tables:
            try:
                table = dynamodb.create_table(
                    TableName=settings.USER_STATS_TABLE,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                print(f"Table {settings.USER_STATS_TABLE} created successfully.")
            except Exception as e:
                print(f"Error creating table {settings.USER_STATS_TABLE}: {str(e)}")
        else:
            print(f"Table {settings.USER_STATS_TABLE} already exists.")
        
        print("DynamoDB tables setup complete.")
        return True
    except Exception as e:
        print(f"Error setting up DynamoDB tables: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting PlayStudy.AI API in local development mode")
    print("Make sure DynamoDB Local is running on http://localhost:8000")
    
    try:
        # Create tables
        create_tables()
        
        # Run API
        print("Starting FastAPI server on http://localhost:8082")
        print("API documentation available at http://localhost:8082/docs")
        
        # Import and run app with uvicorn
        from app.main import app
        uvicorn.run(app, host="0.0.0.0", port=8082)
        
    except KeyboardInterrupt:
        print("Stopping PlayStudy.AI API")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)