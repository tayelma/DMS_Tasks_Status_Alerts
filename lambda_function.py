import json 
import os
import urllib3
import logging
import boto3
import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Ensure there's at least one handler configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Reuse HTTP client across invocations
http = urllib3.PoolManager()

# Create a DMS client to query replication tasks
dms_client = boto3.client('dms')

def lambda_handler(event, context):
    # Log the entire event payload for debugging
    logger.info("Entire event payload:\n%s", json.dumps(event, indent=4))
    
    # Retrieve the webhook URL from environment variables
    webhook_url = os.getenv('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        logger.info("TEAMS_WEBHOOK_URL environment variable is not set.")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "TEAMS_WEBHOOK_URL environment variable is not set"})
        }

    # Extract AWS account ID from the Lambda context
    try:
        account_id = context.invoked_function_arn.split(":")[4]
        logger.info("Extracted Account ID: %s", account_id)
    except (IndexError, AttributeError) as e:
        logger.error("Failed to extract account ID: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "Invalid Lambda context format."})
        }

    # Validate event structure and extract details
    if not isinstance(event, dict):
        logger.error("Invalid event format. Expected a dictionary.")
        return {
            'statusCode': 400,
            'body': json.dumps({"error": "Event must be a dictionary."})
        }

    detail = event.get('detail', {})
    logger.info("Extracted event detail:\n%s", json.dumps(detail, indent=4))
    
    # Check the task category and only alert for allowed statuses
    task_category = detail.get('category', 'N/A')
    allowed_categories = ["Creation", "Deletion", "Failure", "Failover"]
    if task_category not in allowed_categories:
        logger.info("Task category '%s' not in allowed categories. Skipping alert.", task_category)
        return {
            'statusCode': 200,
            'body': json.dumps({"message": f"No alert sent for category '{task_category}'"})
        }
    
    # Extract the replication task ARN from the resources array
    resources = event.get('resources', [])
    if resources and len(resources) > 0:
        task_arn = resources[0]
    else:
        task_arn = 'N/A'
    
    # Use the ARN to look up the task name via the DMS API
    task_name = 'N/A'
    if task_arn != 'N/A':
        try:
            response = dms_client.describe_replication_tasks(
                Filters=[{'Name': 'replication-task-arn', 'Values': [task_arn]}]
            )
            tasks = response.get('ReplicationTasks', [])
            if tasks:
                task_name = tasks[0].get('ReplicationTaskIdentifier', 'N/A')
                logger.info("Extracted task name from DMS: %s", task_name)
            else:
                logger.info("No replication tasks found for ARN: %s", task_arn)
        except ClientError as e:
            logger.error("Error describing replication tasks: %s", str(e))
    
    # Use the category field as task status
    task_status = task_category

    # Format the time field from ISO 8601 to "MM/DD/YYYY HH:MM:SS" if possible
    time_field = event.get('time', 'N/A')
    if time_field != "N/A":
        try:
            dt = datetime.datetime.strptime(time_field, "%Y-%m-%dT%H:%M:%SZ")
            formatted_time = dt.strftime("%m/%d/%Y %H:%M:%S")
        except Exception as e:
            logger.error("Error formatting time: %s", str(e))
            formatted_time = time_field
    else:
        formatted_time = time_field

    # Get the other fields
    event_name_field = event.get('detail-type', 'DMS Replication Task State Change')
    detail_message = detail.get('detailMessage', 'N/A')
    region = event.get('region', 'N/A')

    # Build the facts dictionary, including both the ARN and task name.
    facts_dict = {
        "Replication Task ARN": task_arn,
        "Task Name": task_name,
        "Task Status": task_status,
        "Time": formatted_time,
        "Event Name": event_name_field,
        "Detail Message": detail_message,
        "Region": region,
        "Account ID": account_id
    }
    # Only include fields whose values are not "N/A"
    facts = [{"name": key, "value": value} for key, value in facts_dict.items() if value != "N/A"]

    # Construct the Teams message payload
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "AWS DMS Replication Task Alert",
        "sections": [{
            "activityTitle": "DMS Replication Task State Change",
            "facts": facts,
            "markdown": True
        }]
    }
    logger.info("Constructed Teams message payload:\n%s", json.dumps(message, indent=4))
    
    # Send the message to Microsoft Teams
    try:
        response = http.request(
            'POST',
            webhook_url,
            body=json.dumps(message),
            headers={'Content-Type': 'application/json'}
        )
        logger.info("Message sent to Teams. Response status: %s", response.status)
        if response.status != 200:
            logger.error("Error posting to Teams: HTTP %s - %s", response.status, response.data.decode('utf-8'))
            return {
                'statusCode': response.status,
                'body': json.dumps({
                    "error": "Failed to post to Microsoft Teams",
                    "details": response.data.decode('utf-8')
                })
            }
    except urllib3.exceptions.RequestError as e:
        logger.error("Request to Teams webhook failed: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "Request to Teams webhook failed.", "details": str(e)})
        }

    logger.info("Returning response with status code: %s", response.status)
    return {
        'statusCode': response.status,
        'body': response.data.decode('utf-8')
    }
