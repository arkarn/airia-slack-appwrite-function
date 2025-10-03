import requests
import json
import os

def get_airia_response(user_input):
    url = "https://api.airia.ai/v2/PipelineExecution/1e0a0ae8-81ca-48dd-b01b-04a7ce7ca1e8"
    
    payload = json.dumps({
        "userId": os.environ.get("AIRIA_USER_ID"),
        "userInput": user_input,
        "asyncOutput": False
    })
    
    headers = {
        'X-API-KEY': os.environ.get("AIRIA_API_KEY"),
        'Content-Type': 'application/json',
    }
    
    response = requests.post(url, headers=headers, data=payload)
    return response.text

