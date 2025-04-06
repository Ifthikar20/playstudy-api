"""
Pre-traffic Lambda hook for testing deployment.
This function is called by AWS CodeDeploy before routing traffic to the new version.
"""

import json
import boto3
import os
import logging
import requests
import traceback

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
codedeploy = boto3.client('codedeploy')

# Get environment variables
api_url = os.environ.get('API_URL')
new_version = os.environ.get('NewVersion')


def handler(event, context):
    """
    Lambda handler for pre-traffic hook
    """
    logger.info(f"Pre-traffic hook execution started for version: {new_version}")
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get the deployment ID
    deployment_id = event.get('DeploymentId')
    lifecycle_event_hook_execution_id = event.get('LifecycleEventHookExecutionId')
    
    # Run tests
    success = run_tests()
    
    # Report success or failure
    if success:
        put_lifecycle_event_hook_result(deployment_id, lifecycle_event_hook_execution_id, "Succeeded")
        return {"status": "Success"}
    else:
        put_lifecycle_event_hook_result(deployment_id, lifecycle_event_hook_execution_id, "Failed")
        return {"status": "Failed"}


def run_tests():
    """
    Run tests against the new deployment
    """
    try:
        # Basic health check test
        response = requests.get(f"{api_url}/health", timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Health check failed with status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return False
        
        # Check health response
        health_data = response.json()
        if health_data.get("status") != "healthy":
            logger.error(f"Health status not 'healthy'. Got: {health_data}")
            return False
            
        logger.info("Health check test passed")
        
        # Basic API test - openapi.json
        response = requests.get(f"{api_url}/api/v1/openapi.json", timeout=5)
        
        if response.status_code != 200:
            logger.error(f"OpenAPI schema check failed with status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            return False
            
        logger.info("OpenAPI schema test passed")
        
        # All tests passed
        logger.info("All pre-traffic tests passed successfully")
        return True
        
    except Exception as e:
        logger.error("Error running tests:")
        logger.error(str(e))
        logger.error(traceback.format_exc())
        return False


def put_lifecycle_event_hook_result(deployment_id, lifecycle_event_hook_execution_id, status):
    """
    Report the result of the pre-traffic hook to CodeDeploy
    """
    try:
        response = codedeploy.put_lifecycle_event_hook_execution_status(
            deploymentId=deployment_id,
            lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
            status=status
        )
        logger.info(f"CodeDeploy status update response: {json.dumps(response)}")
    except Exception as e:
        logger.error("Error reporting lifecycle event hook result:")
        logger.error(str(e))
        logger.error(traceback.format_exc())