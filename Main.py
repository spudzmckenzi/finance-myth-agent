import random
import time
import requests
import schedule
import os
import json
from openai import OpenAI
import tweepy

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

POSTED_FILE = "posted_topics.json"


# =========================
# LOGGING
# =========================
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# =========================
# MEMORY
# =========================
def load_posted():
    if not os.path.exists(POSTED_FILE):
        return []
    with open(POSTED_FILE, "r") as f:
        return json.load(f)

def save_posted(data):
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f)


# =========================
# REDDIT TOPICS
# =========================
def get_trending_topics():
    url = "https://www.reddit.com/r/personalfinance/hot.json?limit=10"
    headers = {"User-Agent": "finance-agent"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        return [p["data"]["title"] for p in data["data"]["children"]]
    except Exception as e:
        log(f"Reddit error: {e}")
        return []


# =========================
# CORE CONTENT GENERATION
# =========================
def generate_core(topic):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a finance educator creating viral content ideas."
            },
            {
                "role": "user",
                "content": f"Create a clear finance myth-busting idea from this:\n{topic}"
            }
        ]
    )
    return res.choices[0].message.content.strip()


# =========================
# PLATFORM ADAPTATION
# =========================
def generate_x(core):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": f"Turn into viral X post under 280 chars:\n{core}"
        }]
    )
    return res.choices[0].message.content.strip()


def generate_facebook(core):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": f"Turn into engaging Facebook post (slightly longer, conversational, no hashtags spam):\n{core}"
        }]
    )
    return res.choices[0].message.content.strip()


def generate_youtube_short(core):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{
            "role": "user",
            "content": f"""
Turn this into a YouTube Shorts script:

- Hook in first 2 seconds
- Simple explanation
- Punchy ending

Topic:
{core}
"""
        }]
    )
    return res.choices[0].message.content.strip()


# =========================
# POSTING
# =========================
def post_to_x(text):
    try:
        client_x = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
        )
        client_x.create_tweet(text=text)
        log("Posted to X")
    except Exception as e:
        log(f"X error: {e}")


def post_to_facebook(text):
    try:
        page_id = os.getenv("FB_PAGE_ID")
        token = os.getenv("FB_ACCESS_TOKEN")

        url = f"https://graph.facebook.com/{page_id}/feed"
        payload = {"message": text, "access_token": token}

        r = requests.post(url, data=payload)
        log(f"Facebook response: {r.status_code}")
    except Exception as e:
        log(f"Facebook error: {e}")


# =========================
# PIPELINE
# =========================
def run():
    log("Running multi-platform agent...")

    topics = get_trending_topics()
    if not topics:
        log("No topics found")
        return

    posted = load_posted()
    topics = [t for t in topics if t not in posted]

    if not topics:
        log("No new topics")
        return

    topic = random.choice(topics)
    log(f"Topic: {topic}")

    core = generate_core(topic)

    x_post = generate_x(core)
    fb_post = generate_facebook(core)
    yt_script = generate_youtube_short(core)

    # post limits
    if len(x_post) > 280:
        x_post = x_post[:277] + "..."

    post_to_x(x_post)
    post_to_facebook(fb_post)

    log("YouTube Short Script:\n" + yt_script)

    posted.append(topic)
    save_posted(posted)

    log("Cycle complete")


# =========================
# SAFE WRAPPER
# =========================
def safe_run():
    try:
        run()
    except Exception as e:
        log(f"Crash: {e}")


# =========================
# SCHEDULE
# =========================
schedule.every().day.at("09:00").do(safe_run)
schedule.every().day.at("14:00").do(safe_run)
schedule.every().day.at("19:00").do(safe_run)

log("Agent started...")

while True:
    schedule.run_pending()
    time.sleep(60)
