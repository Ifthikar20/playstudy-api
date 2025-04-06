import boto3
from typing import Any, Dict, List, Optional, Generic, TypeVar, Type
from botocore.exceptions import ClientError
import logging
import os
from app.core.config import get_settings
from app.core.exceptions import ResourceNotFoundException, ServerException

settings = get_settings()
logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository for DynamoDB interactions"""
    
    def __init__(self, table_name: str, model_class: Type[T]):
        """Initialize repository with table name and model class"""
        self.table_name = table_name
        self.model_class = model_class
        
        # Initialize DynamoDB resource and table
        dynamodb_kwargs = {
            'service_name': 'dynamodb',
            'region_name': settings.AWS_REGION,
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY
        }
        
        # Add endpoint URL if set in environment (for local development)
        endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")
        if endpoint_url:
            dynamodb_kwargs['endpoint_url'] = endpoint_url
            
        self.dynamodb = boto3.resource(**dynamodb_kwargs)
        self.table = self.dynamodb.Table(table_name)
    
    async def get(self, id: str) -> T:
        """Get item by ID"""
        try:
            response = self.table.get_item(Key={"id": id})
            
            if "Item" not in response:
                raise ResourceNotFoundException(self.table_name, id)
                
            return self.model_class.from_dict(response["Item"])
        except ClientError as e:
            logger.error(f"Error getting item from {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to get item from {self.table_name}")
    
    async def create(self, item: T) -> T:
        """Create a new item"""
        try:
            item_dict = item.to_dict()
            self.table.put_item(Item=item_dict)
            return item
        except ClientError as e:
            logger.error(f"Error creating item in {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to create item in {self.table_name}")
    
    async def update(self, id: str, updates: Dict[str, Any]) -> T:
        """Update an item with the given updates"""
        try:
            # Check if item exists
            response = self.table.get_item(Key={"id": id})
            if "Item" not in response:
                raise ResourceNotFoundException(self.table_name, id)
            
            # Build update expression
            update_expression = "SET "
            expression_attribute_values = {}
            
            for key, value in updates.items():
                update_expression += f"{key} = :{key.replace('_', '')}, "
                expression_attribute_values[f":{key.replace('_', '')}"] = value
            
            # Remove trailing comma and space
            update_expression = update_expression[:-2]
            
            # Update item
            response = self.table.update_item(
                Key={"id": id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )
            
            return self.model_class.from_dict(response["Attributes"])
        except ClientError as e:
            logger.error(f"Error updating item in {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to update item in {self.table_name}")
    
    async def delete(self, id: str) -> None:
        """Delete an item by ID"""
        try:
            # Check if item exists
            response = self.table.get_item(Key={"id": id})
            if "Item" not in response:
                raise ResourceNotFoundException(self.table_name, id)
            
            # Delete item
            self.table.delete_item(Key={"id": id})
        except ClientError as e:
            logger.error(f"Error deleting item from {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to delete item from {self.table_name}")
    
    async def list(self, limit: int = 100, last_evaluated_key: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List items with pagination"""
        try:
            params = {
                "Limit": limit
            }
            
            if last_evaluated_key:
                params["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.scan(**params)
            
            items = [self.model_class.from_dict(item) for item in response.get("Items", [])]
            
            result = {
                "items": items,
                "count": len(items),
                "last_evaluated_key": response.get("LastEvaluatedKey")
            }
            
            return result
        except ClientError as e:
            logger.error(f"Error listing items from {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to list items from {self.table_name}")
    
    async def query_by_index(
        self, 
        index_name: str, 
        key_condition_expression: Any,
        expression_attribute_values: Dict[str, Any],
        limit: int = 100,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query items using a secondary index"""
        try:
            params = {
                "IndexName": index_name,
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_attribute_values,
                "Limit": limit
            }
            
            if last_evaluated_key:
                params["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**params)
            
            items = [self.model_class.from_dict(item) for item in response.get("Items", [])]
            
            result = {
                "items": items,
                "count": len(items),
                "last_evaluated_key": response.get("LastEvaluatedKey")
            }
            
            return result
        except ClientError as e:
            logger.error(f"Error querying items from {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to query items from {self.table_name}")
    
    async def batch_get(self, ids: List[str]) -> List[T]:
        """Get multiple items by their IDs"""
        if not ids:
            return []
        
        try:
            # DynamoDB can only process 100 items at a time in a batch
            items = []
            for i in range(0, len(ids), 100):
                batch_ids = ids[i:i+100]
                request_items = {
                    self.table_name: {
                        'Keys': [{'id': id} for id in batch_ids]
                    }
                }
                
                response = self.dynamodb.batch_get_item(RequestItems=request_items)
                batch_items = response.get('Responses', {}).get(self.table_name, [])
                items.extend([self.model_class.from_dict(item) for item in batch_items])
            
            return items
        except ClientError as e:
            logger.error(f"Error batch getting items from {self.table_name}: {str(e)}")
            raise ServerException(f"Failed to batch get items from {self.table_name}")