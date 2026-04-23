import random
import time
import requests
import schedule
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_trending_topics():
    url = "https://www.reddit.com/r/personalfinance/hot.json?limit=5"
    headers = {"User-Agent": "finance-agent"}

    data = requests.get(url, headers=headers).json()
    return [p["data"]["title"] for p in data["data"]["children"]]


def generate_post(topic):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a finance myth-busting social media creator."},
            {"role": "user", "content": f"Turn this into a myth-busting post: {topic}"}
        ]
    )
    return res.choices[0].message.content


def fact_check(post):
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": f"Check accuracy. If good say APPROVED else rewrite:\n{post}"}]
    )
    return post if "APPROVED" in res.choices[0].message.content else res.choices[0].message.content


def post_to_x(text):
    url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {os.getenv('TWITTER_BEARER_TOKEN')}"}
    requests.post(url, json={"text": text}, headers=headers)


def run():
    topics = get_trending_topics()
    topic = random.choice(topics)

    post = generate_post(topic)
    checked = fact_check(post)

    post_to_x(checked)
    print("Posted:", checked)


schedule.every().day.at("09:00").do(run)
schedule.every().day.at("14:00").do(run)
schedule.every().day.at("19:00").do(run)

while True:
    schedule.run_pending()
    time.sleep(60)
