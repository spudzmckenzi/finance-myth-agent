def run():
    log("Fetching topics...")
    topics = get_trending_topics()

    if not topics:
        log("No topics found")
        return

    topic = random.choice(topics)
    log(f"Selected topic: {topic}")

    post = generate_post(topic)
    checked = fact_check(post)

    if len(checked) > 280:
        checked = checked[:277] + "..."

    post_to_x(checked)
    log(f"Posted: {checked}")
