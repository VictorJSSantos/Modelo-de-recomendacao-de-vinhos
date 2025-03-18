from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configurar o WebDriver usando webdriver-manager
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Roda sem abrir a janela do navegador
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Inicializa o navegador usando webdriver-manager (não precisa apontar o caminho manualmente)
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)
driver.get("https://www.evino.com.br/vinhos")

# Aguarda até a página carregar completamente
wait = WebDriverWait(driver, 10)

# Clica no botão "Mostrar mais produtos" até ele sumir ou um limite de cliques ser atingido
max_clicks = 30  # Defina o limite para evitar loops infinitos
clicks = 0

while clicks < max_clicks:
    try:
        # Tenta encontrar e clicar no botão "Mostrar mais produtos"
        button = wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "sc-aXZVg.kewnqF"))
        )
        button.click()
        time.sleep(10)  # Tempo para os produtos carregarem
        clicks += 1
        print(f"Clique {clicks} realizado com sucesso")
    except Exception as e:
        # Se o botão não for encontrado, assume que não há mais produtos para carregar
        print(f"Não foi possível carregar mais produtos: {str(e)}")
        break

# Agora que todos os produtos foram carregados, pega o HTML da página
soup = BeautifulSoup(driver.page_source, "html.parser")

# Extrai todos os links de produtos
links = set()
for a_tag in soup.find_all("a", href=True):
    href = a_tag["href"]
    if "/product/" in href:  # Filtra apenas URLs de produtos
        links.add(href)

# Fecha o navegador
driver.quit()

# Exibe os links extraídos
print(f"Total de produtos encontrados: {len(links)}")

# for link in sorted(links):
#     print(f"https://www.evino.com.br{link}")
