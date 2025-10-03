import requests
import os
import time
from .airia_bot import get_airia_response
from .utils import save_scheduled_message, get_pending_schedule, mark_cancelled

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
        # Use thread_ts if exists (reply in thread), else ts (new thread)
        thread_ts = event.get("thread_ts") or event.get("ts")
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        sla_minutes = int(os.environ.get("SLA_MINUTES", "15"))
        
        if slack_token:
            # Add clock emoji to the mention message
            add_reaction(slack_token, channel, event.get("ts"), "alarm_clock")
            
            # Get response from Airia bot (generate now, schedule for later)
            response_text = get_airia_response(text)
            
            # Schedule message for SLA time
            schedule_message(slack_token, channel, thread_ts, response_text, sla_minutes)
    
    # Handle message event (human replied)
    if event.get("type") == "message" and not event.get("subtype"):
        lookup_thread_ts = event.get("thread_ts") or event.get("ts")
        channel = event.get("channel")
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        
        if not event.get("bot_id"):
            # Human replied - cancel scheduled message
            cancel_scheduled_message(lookup_thread_ts, channel)
        elif event.get("thread_ts") and slack_token:
            # Bot replied (scheduled message posted) - remove alarm clock
            remove_reaction(slack_token, channel, event.get("thread_ts"), "alarm_clock")
    
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

def schedule_message(token, channel, thread_ts, text, sla_minutes):
    post_at = int(time.time()) + (sla_minutes * 60)
    response = requests.post("https://slack.com/api/chat.scheduleMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "thread_ts": thread_ts, "text": text, "post_at": post_at})
    
    result = response.json()
    if result.get("ok"):
        save_scheduled_message(thread_ts, channel, result["scheduled_message_id"], post_at)

def cancel_scheduled_message(thread_ts, channel):
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    doc = get_pending_schedule(thread_ts)
    
    if doc and slack_token:
        # Cancel the scheduled message
        requests.post("https://slack.com/api/chat.deleteScheduledMessage",
            headers={"Authorization": f"Bearer {slack_token}"},
            json={"channel": channel, "scheduled_message_id": doc["scheduled_message_id"]})
        
        # Mark as cancelled in DB
        mark_cancelled(doc["$id"])
        
        # Remove alarm clock, add checkmark (human replied)
        remove_reaction(slack_token, channel, thread_ts, "alarm_clock")
        add_reaction(slack_token, channel, thread_ts, "white_check_mark")
