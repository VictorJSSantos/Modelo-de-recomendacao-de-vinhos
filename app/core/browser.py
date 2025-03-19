from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException


from app.config.settings import BROWSER_USER_AGENT, BROWSER_TIMEOUT


def initialize_browser():
    """
    Inicializa e configura o navegador Chrome.

    Returns:
        webdriver.Chrome ou None: O navegador configurado ou None em caso de erro.
    """
    print("Inicializando o navegador...")
    try:
        options = Options()

        # Configurações essenciais
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Configurações para estabilidade
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        # Identidade do navegador
        options.add_argument(f"--user-agent={BROWSER_USER_AGENT}")

        # Ignorar erros de certificado
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")

        # Reduzir logs
        options.add_argument("--log-level=3")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Configurações para performance
        options.page_load_strategy = "eager"

        # Inicializa o navegador
        driver = webdriver.Chrome(options=options)

        # Configura timeouts
        driver.set_page_load_timeout(BROWSER_TIMEOUT)
        driver.set_script_timeout(BROWSER_TIMEOUT)

        print("Navegador inicializado com sucesso")
        return driver

    except WebDriverException as e:
        print(f"Erro ao inicializar o navegador: {e}")
        return None


def close_browser(driver):
    """
    Fecha o navegador com segurança.

    Args:
        driver (webdriver.Chrome): O navegador a ser fechado.
    """
    try:
        if driver:
            driver.quit()
            print("Navegador fechado com sucesso")
    except Exception as e:
        print(f"Erro ao fechar o navegador: {e}")
