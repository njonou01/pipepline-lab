# Tech Pulse - Configuration (exemple)
# Équipe: UCCNT
# Copier ce fichier vers config.py et remplir les valeurs

KAFKA_BOOTSTRAP_SERVERS = "57.130.30.86:9092"

TOPICS = {
    "bluesky": "raw-bluesky",
    "nostr": "raw-nostr",
    "hackernews": "raw-hackernews",
    "stackoverflow": "raw-stackoverflow",
    "rss": "raw-rss"
}

# Bluesky
BLUESKY_HANDLE = ""      # ton handle (ex: user.bsky.social)
BLUESKY_PASSWORD = ""    # ton app password (créer sur bsky.app/settings/app-passwords)
BLUESKY_KEYWORDS = ["python", "javascript", "rust", "golang", "devops", "kubernetes", "docker", "aws", "cloud", "ai", "machine learning", "llm", "react", "nodejs"]

# Nostr relays
NOSTR_RELAYS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.snort.social"
]

# RSS Feeds
RSS_FEEDS = [
    "https://dev.to/feed",
    "https://hnrss.org/frontpage",
    "https://www.reddit.com/r/programming/.rss",
    "https://blog.golang.org/feed.atom",
    "https://aws.amazon.com/blogs/aws/feed/"
]

# Stack Overflow tags
STACKOVERFLOW_TAGS = ["python", "javascript", "rust", "go", "kubernetes", "docker", "aws", "react", "machine-learning"]

# Intervalles de polling (secondes)
POLL_INTERVAL_HN = 300        # 5 min
POLL_INTERVAL_SO = 600        # 10 min
POLL_INTERVAL_RSS = 900       # 15 min
