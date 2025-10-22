from dotenv import load_dotenv
import os

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")
AGENT_HOST = os.getenv("AGENT_HOST", "0.0.0.0")
AGENT_PORT = int(os.getenv("AGENT_PORT", 8000))
PROVENANCE_DIR = os.getenv("PROVENANCE_DIR", "./provenance_logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
IPFS_API_URL = os.getenv("IPFS_API_URL", None)
