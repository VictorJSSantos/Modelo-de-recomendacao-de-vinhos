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
