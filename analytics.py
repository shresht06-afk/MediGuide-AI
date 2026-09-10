import csv
import os
from datetime import datetime


ANALYTICS_FILE = "Analytics/mediGuide_interactions.csv"


def log_interaction(
    session_id,
    response_time,
    conversation_length,
    topic="General",
    status="success"
):
    os.makedirs("Analytics", exist_ok=True)

    file_exists = os.path.exists(ANALYTICS_FILE)

    with open(
        ANALYTICS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "session_id",
                "topic",
                "response_time",
                "conversation_length",
                "status"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            session_id,
            topic,
            round(response_time, 2),
            conversation_length,
            status
        ])