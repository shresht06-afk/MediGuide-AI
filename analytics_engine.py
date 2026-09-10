import os
import pandas as pd


ANALYTICS_FILE = "Analytics/mediGuide_interactions.csv"


def load_data():
    if not os.path.exists(ANALYTICS_FILE):
        print("Analytics file not found.")
        return pd.DataFrame()

    df = pd.read_csv(ANALYTICS_FILE)

    return df


def generate_report():
    df = load_data()

    if df.empty:
        print("No analytics data available yet.")
        return

    total_interactions = len(df)

    total_sessions = df["session_id"].nunique()

    average_response_time = df["response_time"].mean()

    success_rate = (
        (df["status"] == "success").mean() * 100
    )

    error_rate = (
        (df["status"] == "error").mean() * 100
    )

    average_conversation_depth = (
        df["conversation_length"].mean()
    )

    topic_counts = df["topic"].value_counts()

    most_common_topic = topic_counts.index[0]

    print("\n")
    print("=" * 50)
    print("        MEDIGUIDE AI ANALYTICS REPORT")
    print("=" * 50)

    print(f"\nTotal Interactions      : {total_interactions}")
    print(f"Total Sessions          : {total_sessions}")
    print(
        f"Average Response Time  : "
        f"{average_response_time:.2f} seconds"
    )
    print(f"Success Rate            : {success_rate:.2f}%")
    print(f"Error Rate              : {error_rate:.2f}%")
    print(
        f"Average Conversation Depth : "
        f"{average_conversation_depth:.2f}"
    )

    print(f"\nMost Common Topic       : {most_common_topic}")

    print("\nTopic Distribution")
    print("-" * 30)

    for topic, count in topic_counts.items():
        print(f"{topic:<25} {count}")

    print("\n")
    print("=" * 50)
    print("              END OF REPORT")
    print("=" * 50)
    print()


if __name__ == "__main__":
    generate_report()