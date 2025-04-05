import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Configurações do scraper
EVINO_BASE_URL = "https://www.evino.com.br"
EVINO_PRODUCTS_URL = f"{EVINO_BASE_URL}/vinhos"
MAX_SCROLLS = 15
SCROLL_DELAY = 2
BUTTON_CLICK_DELAY = 3
PRODUCTS_BATCH_SIZE = 10
DOWNLOAD_INTERVAL = 30  # em minutos
DOWNLOAD_DELAY = 2  # segundos entre downloads

# Configurações do navegador
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BROWSER_TIMEOUT = 30

# Configurações de arquivos locais para salvar
JSON_OBJS_PATH = os.environ.get("JSON_OBJS_PATH")
IMAGE_PATH = os.environ.get("IMAGE_PATH")

# Configurações de nuvem
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")
AWS_REGION = os.environ.get("AWS_REGION")
RAW_BUCKET = os.environ.get("RAW_BUCKET")
IMAGES_RAW_BUCKET = os.environ.get("IMAGES_RAW_BUCKET")
OBJS_RAW_BUCKET = os.environ.get("OBJS_RAW_BUCKET")
