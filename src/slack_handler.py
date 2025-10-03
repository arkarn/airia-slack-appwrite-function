import requests
import os
from .airia_bot import get_airia_response

def handle_slack_event(body, headers):
    # Handle Slack URL verification challenge
    if "challenge" in body:
        return {"challenge": body["challenge"]}
    
    # Ignore Slack retries to prevent duplicate responses
    if headers.get("x-slack-retry-num"):
        return {"status": "ignored_retry"}
    
    # Handle app_mention event
    event = body.get("event", {})
    if event.get("type") == "app_mention":
        text = event.get("text", "").replace(f"<@{body.get('authorizations', [{}])[0].get('user_id', '')}>", "").strip()
        channel = event.get("channel")
        thread_ts = event.get("ts")
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        
        if slack_token:
            # Add thinking emoji reaction
            add_reaction(slack_token, channel, thread_ts, "hourglass_flowing_sand")
            
            # Get response from Airia bot
            response_text = get_airia_response(text)
            
            # Post to Slack thread
            post_message(slack_token, channel, thread_ts, response_text)
            
            # Remove thinking emoji
            remove_reaction(slack_token, channel, thread_ts, "hourglass_flowing_sand")
    
    return {"status": "ok"}

def add_reaction(token, channel, timestamp, emoji_name):
    requests.post("https://slack.com/api/reactions.add",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "timestamp": timestamp, "name": emoji_name})

def remove_reaction(token, channel, timestamp, emoji_name):
    requests.post("https://slack.com/api/reactions.remove",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "timestamp": timestamp, "name": emoji_name})

def post_message(token, channel, thread_ts, text):
    requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "thread_ts": thread_ts, "text": text})

