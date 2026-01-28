import os

# UCCNT - Configuration | Équipe: UCCNT

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

TOPICS = {
    "bluesky": "bluesky",
    "nostr": "nostr",
    "hackernews": "hackernews",
    "stackoverflow": "stackoverflow",
    "rss": "rss"
}

BLUESKY_HANDLE = "njonou45.bsky.social"
BLUESKY_PASSWORD = "r24a-v3tj-oubv-race"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_PASSWORD = "mon_super_password"
REDIS_DB = 0
CACHE_TTL = 604800  # 1 semaine (7 jours en secondes)
CACHE_WARMUP_SIZE = 50000  # Nombre de messages Kafka à lire au démarrage pour pré-remplir le cache

CACHE_WARMUP_HOURS = {
    "bluesky": 0.75,        # 45 minutes
    "nostr": 24,            # 24 heures
    "hackernews": 24,       # 24 heures
    "stackoverflow": 24,    # 24 heures
    "rss": 24               # 24 heures
}

# Configuration avancée: activer/désactiver le warmup par source
# Par défaut DÉSACTIVÉ - à activer manuellement selon les besoins
CACHE_WARMUP_ENABLED = {
    "bluesky": False,
    "nostr": False,
    "hackernews": False,
    "stackoverflow": False,
    "rss": False
}

NOSTR_RELAYS = [
    # Relays principaux validés (haute disponibilité)

    "wss://purplepag.es",
    "wss://nostr.mom",

    "wss://relay.nostr.com.au",
    "wss://nostr.oxtr.dev",
    "wss://relay.nsec.app",

    "wss://eden.nostr.land"
]

RSS_FEEDS = [
    # Agrégateurs tech (validés ✓)
    "https://dev.to/feed",
    "https://hnrss.org/frontpage",
    "https://lobste.rs/rss",
    
    # Reddit (validés ✓ - certains ont rate limit temporaire)
    "https://www.reddit.com/r/machinelearning/.rss",
    "https://www.reddit.com/r/datascience/.rss",
    
    # Cloud Providers (validés ✓)
    "https://aws.amazon.com/blogs/aws/feed/",
    
    # Langages & Frameworks (validés ✓)
    "https://blog.golang.org/feed.atom",
    "https://blog.rust-lang.org/feed.xml",
    "https://reactjs.org/feed.xml",
    
    # DevOps & Infrastructure (validés ✓)
    "https://kubernetes.io/feed.xml",
    "https://www.docker.com/blog/feed/",
    "https://www.hashicorp.com/blog/feed.xml",
    "https://about.gitlab.com/atom.xml",
    "https://github.blog/feed/",
    
    # Tech News (validés ✓)
    "https://techcrunch.com/feed/",
    "https://arstechnica.com/feed/",
    
    # Developer Platforms (validés ✓)
    "https://stackoverflow.blog/feed/",
]

# Tags Stack Overflow organisés par priorité pour rotation intelligente
# Ceci permet de réduire les appels API de 4320/jour à ~720/jour

# Haute priorité : Toujours scannés (langages et techs les plus populaires)
STACKOVERFLOW_TAGS_HIGH = [
    "python", "javascript", "typescript", "java", "c#", "c++", "go", "rust",
    "react", "node.js", "docker", "kubernetes", "aws", "azure",
    "machine-learning", "deep-learning", "pytorch", "tensorflow",
    "postgresql", "mongodb", "mysql", "redis",
    "git", "api", "rest", "microservices",
]

# Priorité moyenne : Rotation toutes les 2-3 cycles
STACKOVERFLOW_TAGS_MEDIUM = [
    "kotlin", "swift", "php", "ruby", "scala", "r", "dart", "flutter",
    "angular", "vue.js", "nextjs", "svelte", "django", "flask", "fastapi",
    "spring-boot", "laravel", "rails", "express", "nestjs",
    "terraform", "ansible", "jenkins", "github-actions", "gitlab-ci",
    "prometheus", "grafana", "elasticsearch", "nginx", "apache",
    "llm", "chatgpt", "openai-api", "langchain", "transformers",
    "apache-kafka", "apache-spark", "apache-airflow", "snowflake", "databricks",
    "graphql", "grpc", "websocket", "oauth", "jwt",
    "android", "ios", "react-native", "swiftui",
    "testing", "pytest", "jest", "selenium", "cypress",
    "devops", "cicd", "security", "authentication", "encryption",
]

# Priorité basse : Rotation lente (toutes les 5-10 cycles)
STACKOVERFLOW_TAGS_LOW = [
    "haskell", "perl", "julia", "elixir", "clojure", "lua", "groovy",
    "objective-c", "assembly", "fortran", "cobol", "shell", "bash", "powershell",
    "google-cloud-platform", "heroku", "digitalocean", "cloudflare", "vercel",
    "netlify", "openstack", "vagrant", "aws-lambda", "azure-functions",
    "google-cloud-functions", "eks", "aks", "gke",
    "circleci", "travis-ci", "bamboo", "teamcity", "logstash", "kibana", "datadog",
    "helm", "argocd", "flux", "pulumi", "crossplane", "istio", "envoy",
    "ember.js", "backbone.js", "jquery", "bootstrap", "tailwindcss",
    "material-ui", "ant-design", "chakra-ui", "redux", "webpack", "vite",
    "rollup", "parcel", "sass", "less", "styled-components",
    "fastify", "koa", "hapi", "tornado", "pyramid", "aiohttp",
    "spring", "quarkus", "micronaut", "vert.x", "symfony", "codeigniter",
    "yii", "sinatra", "asp.net", "asp.net-core", "asp.net-mvc", "blazor",
    "gin", "echo", "fiber", "beego",
    "keras", "scikit-learn", "huggingface-transformers", "spacy", "nltk",
    "opencv", "computer-vision", "natural-language-processing",
    "neural-network", "reinforcement-learning", "pandas", "numpy",
    "matplotlib", "seaborn", "plotly", "jupyter-notebook", "colab",
    "gpt-4", "bert", "stable-diffusion", "apache-flink", "apache-beam",
    "dbt", "apache-hive", "apache-hadoop", "presto", "trino",
    "etl", "data-pipeline", "data-warehouse", "data-lake",
    "sqlite", "mariadb", "oracle-database", "sql-server", "cassandra",
    "couchdb", "dynamodb", "firebase", "supabase", "neo4j", "influxdb",
    "timescaledb", "cockroachdb", "clickhouse", "sql", "nosql",
    "prisma", "sequelize", "typeorm", "sqlalchemy",
    "xamarin", "ionic", "cordova", "expo", "kotlin-android", "swift-ios",
    "jetpack-compose", "https", "cors", "xss", "sql-injection",
    "penetration-testing", "cybersecurity", "cryptography", "openssl",
    "keycloak", "auth0", "restful-api", "soap", "openapi", "swagger",
    "api-gateway", "kong", "rabbitmq", "zeromq", "mqtt",
    "unit-testing", "integration-testing", "mocha", "playwright",
    "puppeteer", "testng", "junit", "github", "gitlab", "bitbucket",
    "git-merge", "git-rebase", "design-patterns", "microservices-architecture",
    "clean-architecture", "ddd", "event-driven", "cqrs", "saga-pattern",
    "solid-principles", "containers", "docker-compose", "podman",
    "containerd", "kubernetes-helm", "kubernetes-operator", "service-mesh",
    "serverless", "vercel-functions", "netlify-functions", "cloudflare-workers",
    "unity3d", "unreal-engine4", "godot", "game-development",
    "opengl", "vulkan", "directx", "raspberry-pi", "arduino", "esp32",
    "embedded", "iot", "micropython", "platformio", "blockchain",
    "ethereum", "solidity", "web3js", "smart-contracts", "nft", "defi",
    "linux", "ubuntu", "debian", "centos", "fedora", "archlinux",
    "macos", "windows", "systemd", "cron", "ssh", "networking",
]

# Configuration pour le système de rotation
SO_BATCH_SIZE = 100  # Nombre maximum de tags par cycle (optimisé pour plus de volume)
SO_ROTATION_CYCLE = 0  # Index de rotation (sera incrémenté à chaque cycle)

STACKOVERFLOW_KEY = "rl_op3u9xnruk9ZXrLAf3MKMChQg"

# Intervalles optimisés pour maximum de volume
POLL_INTERVAL_HN = 120   # 2 minutes (au lieu de 5) - plus de stories HackerNews
POLL_INTERVAL_SO = 300   # 5 minutes (au lieu de 10) - plus de questions Stack Overflow
POLL_INTERVAL_RSS = 180  # 3 minutes (au lieu de 15) - plus d'articles RSS

ALL_KEYWORDS = [
    "python", "javascript", "typescript", "rust", "golang", "go", "java", "c++", "c#",
    "kotlin", "swift", "php", "ruby", "scala", "haskell", "perl", "lua", "r", "julia",
    "elixir", "clojure", "dart", "zig", "nim", "ocaml", "groovy", "objective-c",
    "assembly", "fortran", "cobol", "shell", "bash", "powershell",

    "aws", "azure", "gcp", "google cloud", "kubernetes", "docker", "terraform",
    "cloudflare", "vercel", "netlify", "heroku", "digitalocean", "linode", "vultr",
    "oracle cloud", "ibm cloud", "alibaba cloud", "openstack", "vagrant",
    "aws-lambda", "azure-functions", "google-cloud-functions", "eks", "aks", "gke",

    "machine learning", "deep learning", "llm", "chatgpt", "openai", "claude",
    "anthropic", "gemini", "huggingface", "pytorch", "tensorflow", "keras",
    "scikit-learn", "gpt", "gpt-4", "ai", "artificial intelligence", "neural network",
    "nlp", "natural language processing", "computer vision", "stable diffusion",
    "midjourney", "copilot", "dall-e", "whisper", "llama", "mistral", "perplexity",
    "langchain", "vector database", "embeddings", "transformer", "transformers",
    "bert", "diffusion", "generative ai", "agi", "reinforcement learning",
    "spacy", "nltk", "opencv",

    "react", "vue", "vue.js", "angular", "nextjs", "next.js", "nuxt", "nuxt.js",
    "svelte", "ember.js", "backbone.js", "jquery", "tailwind", "tailwindcss",
    "bootstrap", "material-ui", "ant-design", "chakra-ui", "redux", "webpack",
    "vite", "rollup", "parcel", "sass", "less", "styled-components",

    "nodejs", "node.js", "express", "nestjs", "fastify", "koa", "hapi",
    "django", "flask", "fastapi", "tornado", "pyramid", "aiohttp",
    "spring", "spring-boot", "quarkus", "micronaut", "vert.x",
    "laravel", "symfony", "codeigniter", "yii", "rails", "sinatra", "phoenix",
    "asp.net", "asp.net-core", "asp.net-mvc", "blazor",
    "gin", "echo", "fiber", "beego", "remix", "astro", "gatsby",

    "ios", "android", "flutter", "react native", "react-native", "swiftui",
    "jetpack compose", "jetpack-compose", "xamarin", "ionic", "cordova", "expo",

    "devops", "cicd", "ci/cd", "github", "gitlab", "bitbucket", "jenkins",
    "gitlab-ci", "github-actions", "circleci", "travis-ci", "bamboo", "teamcity",
    "ansible", "prometheus", "grafana", "datadog", "linux", "ubuntu", "debian",
    "fedora", "centos", "archlinux", "arch", "nginx", "apache", "caddy", "traefik",
    "vault", "consul", "nomad", "pulumi", "crossplane", "argocd", "fluxcd", "flux",
    "helm", "kustomize", "istio", "envoy", "logstash", "kibana",

    "kafka", "apache-kafka", "spark", "apache-spark", "apache-flink", "apache-beam",
    "airflow", "apache-airflow", "dbt", "postgresql", "mysql", "mongodb", "redis",
    "sqlite", "mariadb", "oracle-database", "sql-server", "elasticsearch",
    "cassandra", "couchdb", "dynamodb", "neo4j", "influxdb", "timescaledb",
    "cockroachdb", "clickhouse", "database", "sql", "nosql", "graphql", "prisma",
    "sequelize", "typeorm", "sqlalchemy", "data engineering", "data science",
    "analytics", "bigdata", "big data", "snowflake", "databricks", "apache-hive",
    "apache-hadoop", "presto", "trino", "etl", "data-pipeline", "data-warehouse",
    "data-lake", "supabase", "firebase", "planetscale",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly", "jupyter", "jupyter-notebook",

    "security", "cybersecurity", "hacking", "pentesting", "penetration-testing",
    "ctf", "malware", "ransomware", "phishing", "encryption", "cryptography",
    "privacy", "zero trust", "soc", "siem", "vulnerability", "exploit", "bug bounty",
    "red team", "blue team", "authentication", "oauth", "oauth-2.0", "jwt", "ssl",
    "https", "cors", "xss", "sql-injection", "openssl", "keycloak", "auth0", "firewall", "vpn",

    "blockchain", "web3", "bitcoin", "btc", "ethereum", "eth", "crypto", "nft",
    "defi", "solana", "cardano", "polkadot", "avalanche", "polygon", "arbitrum",
    "optimism", "layer2", "smart contract", "smart-contracts", "solidity", "web3js",
    "dao", "token", "wallet", "metamask", "ledger", "staking", "yield", "dex", "cex",
    "sats", "satoshi", "lightning", "ln", "lnurl", "nostr", "zap", "hodl", "mining",

    "startup", "saas", "founder", "entrepreneur", "vc", "funding", "product",
    "growth", "marketing", "revenue", "profit", "investor", "seed", "series a",
    "unicorn", "acquisition", "ipo", "pivot", "mvp", "product hunt", "indie hacker",
    "bootstrapped", "yc", "techstars", "b2b", "b2c",
    # Carrière
    "developer", "engineer", "programmer", "coding", "programming", "software",
    "tech", "job", "hiring", "remote", "freelance", "interview", "salary", "career",
    "resume", "portfolio", "linkedin", "recruiter", "layoff", "junior", "senior",
    "staff", "principal", "cto", "vp engineering", "tech lead", "manager",
    "fullstack", "full-stack", "frontend", "front-end", "backend", "back-end",
    # API
    "api", "rest", "restful", "restful-api", "grpc", "websocket", "soap", "openapi",
    "swagger", "microservices", "microservices-architecture", "api-gateway", "kong",
    "rabbitmq", "zeromq", "mqtt",
    # Testing
    "testing", "unit-testing", "integration-testing", "pytest", "jest", "mocha",
    "selenium", "cypress", "playwright", "puppeteer", "testng", "junit", "tdd", "bdd",
    # Architecture
    "design-patterns", "clean-architecture", "ddd", "domain-driven", "event-driven",
    "cqrs", "saga-pattern", "solid-principles", "solid",
    # Serverless
    "serverless", "lambda", "functions", "faas",
    # Gaming
    "gaming", "game dev", "game-development", "unity", "unity3d", "unreal",
    "unreal-engine4", "godot", "steam", "playstation", "xbox", "nintendo", "esport",
    "twitch", "discord", "vr", "ar", "metaverse", "roblox", "minecraft",
    "opengl", "vulkan", "directx",
    # Hardware/IoT
    "hardware", "iot", "raspberry pi", "raspberry-pi", "arduino", "esp32",
    "embedded", "firmware", "chip", "cpu", "gpu", "tpu", "nvidia", "amd", "intel",
    "arm", "risc-v", "fpga", "asic", "3d printing", "robotics", "drone", "sensor",
    "micropython", "platformio",
    # Tools
    "productivity", "notion", "obsidian", "roam", "logseq", "todoist", "linear",
    "jira", "asana", "trello", "slack", "teams", "zoom", "figma", "sketch", "adobe",
    "vscode", "vim", "neovim", "emacs", "jetbrains", "ide", "terminal", "git",
    # Big Tech
    "apple", "google", "microsoft", "meta", "amazon", "netflix", "nvidia", "tesla",
    "spacex", "twitter", "x", "stripe", "shopify", "twilio", "datadog", "hashicorp",
    "elastic", "canva", "spotify", "uber",
    # Open Source
    "opensource", "open source", "foss", "libre", "community", "conference",
    "meetup", "hackathon", "devrel", "advocacy", "contributor", "maintainer",
    "sponsor", "patreon", "github sponsors", "license", "mit", "gpl",
    # News
    "trending", "viral", "news", "breaking", "announcement", "launch", "release",
    "update", "beta", "alpha", "v1", "v2", "roadmap", "changelog", "feature",
    "bug", "fix", "patch",
    # Finance
    "fintech", "payment", "paypal", "banking", "neobank", "trading", "investing",
    "stock", "forex", "wealth", "budget", "credit", "loan", "insurance", "regtech",
    "money", "finance", "market", "economy", "inflation", "dollar", "fiat",
    # Social
    "social media", "content", "creator", "influencer", "youtube", "tiktok",
    "instagram", "podcast", "blog", "newsletter", "substack", "medium", "hashnode",
    "dev.to", "reddit", "mastodon", "threads", "bluesky",
    # Containers
    "containers", "docker-compose", "podman", "containerd", "kubernetes-helm",
    "kubernetes-operator", "service-mesh",
    # Français
    "développeur", "développement", "programmation", "programmeur", "informatique",
    "logiciel", "ordinateur", "réseau", "données", "serveur", "sécurité",
    "intelligence artificielle", "apprentissage automatique", "base de données",
    "application", "site web", "coder", "nuage", "hébergement", "framework",
    "bibliothèque", "algorithme", "variable", "fonction", "classe", "objet", "interface",
    # Espagnol
    "desarrollador", "desarrollo", "programación", "programador", "informática",
    "computadora", "ordenador", "red", "datos", "servidor", "seguridad",
    "inteligencia artificial", "aprendizaje automático", "base de datos",
    "aplicación", "sitio web", "código", "codificar", "nube", "alojamiento",
    "algoritmo", "interfaz",
    # Portugais
    "desenvolvedor", "desenvolvimento", "programação", "computador", "rede",
    "segurança", "inteligência artificial", "aprendizado de máquina",
    "banco de dados", "aplicativo", "site", "codificar", "nuvem", "hospedagem", "variável",
    # Allemand
    "entwickler", "entwicklung", "programmierung", "programmierer", "informatik",
    "rechner", "netzwerk", "daten", "sicherheit", "künstliche intelligenz",
    "maschinelles lernen", "datenbank", "anwendung", "webseite", "programmieren",
    "hosting", "algorithmus", "schnittstelle",
    # Italien
    "sviluppatore", "sviluppo", "programmazione", "programmatore", "informatica",
    "rete", "dati", "sicurezza", "intelligenza artificiale",
    "apprendimento automatico", "applicazione", "sito web", "codice", "programmare",
    "algoritmo", "variabile", "funzione", "oggetto", "interfaccia",
    # Néerlandais
    "ontwikkelaar", "ontwikkeling", "programmeren", "programmeur", "netwerk",
    "gegevens", "beveiliging", "kunstmatige intelligentie", "machinaal leren",
    "applicatie", "website", "coderen",
]

ALL_KEYWORDS_SET = set(kw.lower() for kw in ALL_KEYWORDS)

# Catégories pour classification
KEYWORD_CATEGORIES = {
    "tech": ["python", "javascript", "typescript", "rust", "golang", "go", "java", "c++", "c#", "kotlin", "swift", "php", "ruby",
             "scala", "haskell", "perl", "lua", "r", "julia", "elixir", "clojure", "dart", "zig", "nim",
             "code", "coding", "programming", "developer", "engineer", "software", "linux", "ubuntu", "debian", "fedora",
             "github", "gitlab", "api", "backend", "frontend", "fullstack", "git", "vscode", "vim", "neovim", "ide", "terminal", "bash"],
    "ai": ["ai", "gpt", "chatgpt", "openai", "claude", "anthropic", "llm", "machine learning", "deep learning",
           "neural network", "nlp", "computer vision", "tensorflow", "pytorch", "huggingface", "copilot", "midjourney",
           "stable diffusion", "gemini", "bard", "artificial intelligence", "robotics", "automation", "bot",
           "dall-e", "whisper", "llama", "mistral", "langchain", "embeddings", "transformer", "generative ai", "agi"],
    "cloud": ["aws", "azure", "gcp", "kubernetes", "docker", "terraform", "cloudflare", "vercel", "serverless",
              "microservices", "cicd", "jenkins", "ansible", "prometheus", "grafana", "nginx", "apache", "heroku", "netlify",
              "digitalocean", "linode", "vultr", "pulumi", "argocd", "helm", "kustomize"],
    "data": ["kafka", "spark", "airflow", "database", "sql", "nosql", "postgresql", "mongodb", "redis", "mysql",
             "elasticsearch", "bigdata", "data science", "analytics", "etl", "pipeline", "warehouse", "lake", "dbt", "snowflake",
             "clickhouse", "cassandra", "neo4j", "graphql", "prisma", "supabase", "firebase", "databricks"],
    "crypto": ["bitcoin", "btc", "sats", "satoshi", "lightning", "ln", "lnurl", "ethereum", "eth", "crypto", "blockchain",
               "web3", "defi", "nft", "solana", "cardano", "polkadot", "nostr", "zap", "wallet", "mining", "token", "dao",
               "hodl", "stacking", "dca", "layer2", "smart contract", "metamask", "ledger"],
    "security": ["security", "cybersecurity", "hacking", "pentesting", "ctf", "malware", "ransomware", "encryption",
                 "privacy", "vulnerability", "exploit", "firewall", "vpn", "password", "authentication", "oauth",
                 "zero trust", "bug bounty", "red team", "blue team", "phishing"],
    "business": ["startup", "saas", "founder", "entrepreneur", "vc", "funding", "product", "growth",
                 "marketing", "monetization", "revenue", "profit", "customer", "client", "b2b", "b2c", "mvp", "pitch",
                 "investor", "seed", "series a", "unicorn", "acquisition", "ipo", "indie hacker", "bootstrapped"],
    "career": ["job", "hiring", "remote", "freelance", "interview", "salary", "resume", "career", "work",
               "employee", "employer", "recruiter", "linkedin", "portfolio", "internship", "junior", "senior",
               "staff", "principal", "cto", "tech lead", "manager", "layoff"],
    "web": ["react", "vue", "angular", "nextjs", "nuxt", "svelte", "html", "css", "tailwind", "bootstrap", "webpack",
            "nodejs", "express", "nestjs", "django", "flask", "fastapi", "laravel", "spring", "rails", "phoenix",
            "remix", "astro", "gatsby", "website", "webapp"],
    "mobile": ["ios", "android", "flutter", "react native", "swiftui", "jetpack compose", "mobile", "app", "smartphone", "tablet"],
    "gaming": ["game", "gaming", "game dev", "unity", "unreal", "godot", "steam", "playstation", "xbox", "nintendo",
               "esport", "twitch", "vr", "ar", "metaverse", "roblox", "minecraft"],
    "hardware": ["hardware", "iot", "raspberry pi", "arduino", "esp32", "sensor", "embedded", "firmware", "chip",
                 "cpu", "gpu", "tpu", "nvidia", "amd", "intel", "arm", "risc-v", "3d printing", "drone"],
    "opensource": ["opensource", "open source", "foss", "libre", "community", "contributor", "maintainer",
                   "license", "mit", "gpl", "sponsor", "github sponsors"],
    "news": ["news", "breaking", "announcement", "launch", "release", "update", "trending", "viral", "new",
             "beta", "alpha", "roadmap", "changelog", "feature"],
    "social": ["twitter", "x", "facebook", "meta", "instagram", "tiktok", "youtube", "reddit", "discord",
               "slack", "telegram", "mastodon", "threads", "bluesky", "nostr"],
    "bigtech": ["google", "microsoft", "apple", "amazon", "meta", "nvidia", "tesla", "netflix", "spotify", "uber",
                "spacex", "stripe", "shopify", "twilio", "datadog", "hashicorp", "figma", "canva", "notion", "linear"],
    "learning": ["learn", "tutorial", "course", "bootcamp", "university", "student", "teacher", "education",
                 "study", "book", "reading", "knowledge", "skill"],
    "productivity": ["productivity", "workflow", "notion", "obsidian", "roam", "logseq", "todoist", "linear",
                     "jira", "asana", "trello", "calendar", "automation", "efficiency", "tool"],
    "finance": ["money", "finance", "trading", "invest", "market", "stock", "economy", "bank", "payment", "fintech",
                "inflation", "dollar", "fiat", "gold", "wealth", "savings", "debt", "interest rate"],
    "sentiment": ["love", "hate", "amazing", "awesome", "terrible", "best", "worst", "great", "bad", "good",
                  "happy", "sad", "excited", "disappointed", "frustrated", "impressed", "recommend", "grateful",
                  "proud", "beautiful", "incredible", "blessed", "thankful"],
    "lifestyle": ["life", "work", "health", "fitness", "mental health", "burnout", "travel", "food", "music",
                  "movie", "book", "hobby", "family", "relationship", "balance"],
    "society": ["freedom", "privacy", "censorship", "government", "law", "regulation", "democracy", "rights",
                "election", "politics", "policy", "tax", "liberty", "sovereign", "decentralized"],
    "content": ["content", "creator", "influencer", "podcast", "blog", "newsletter", "substack", "medium",
                "youtube", "video", "stream", "live"]
}

VALID_CATEGORIES = list(KEYWORD_CATEGORIES.keys())

# Remapping: mots courants → tech keywords
WORD_TO_TECH_REMAP = {
    "love": "python", "hate": "javascript", "happy": "react", "sad": "rust",
    "excited": "kubernetes", "amazing": "docker", "awesome": "aws", "great": "nodejs",
    "good": "linux", "bad": "devops", "beautiful": "flutter", "terrible": "golang",
    "wonderful": "typescript", "fantastic": "fastapi", "incredible": "pytorch",
    "today": "github", "tomorrow": "gitlab", "yesterday": "jenkins",
    "morning": "terraform", "night": "ansible", "weekend": "prometheus",
    "think": "ai", "believe": "machine learning", "want": "deep learning",
    "need": "nlp", "like": "chatgpt", "hope": "openai", "wish": "llm", "feel": "neural network",
    "more": "bigdata", "less": "redis", "many": "mongodb", "few": "postgresql",
    "all": "elasticsearch", "most": "kafka", "some": "spark",
    "people": "community", "friend": "opensource", "family": "startup",
    "everyone": "saas", "someone": "api", "nobody": "microservices",
    "life": "software", "work": "career", "money": "crypto", "time": "automation",
    "world": "cloud", "home": "iot", "food": "data science", "music": "streaming",
    "game": "gaming", "book": "learning",
    "how": "tutorial", "why": "debugging", "what": "documentation",
    "when": "deployment", "where": "infrastructure", "who": "team",
}
