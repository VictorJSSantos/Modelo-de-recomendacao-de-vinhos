import time
from bs4 import BeautifulSoup
from supabase import create_client

# Configurações do Supabase
SUPABASE_URL = "sua_url_do_supabase"
SUPABASE_KEY = "sua_chave_do_supabase"

# Inicializar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def scrape_wine_info(html_content):
    """
    Extrai informações detalhadas sobre vinhos do HTML
    """
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Inicializar dicionário para armazenar dados extraídos
    wine_data = {
        "product_type": None,
        "product_name": None,
        "wine_variety": None,
        "wine_region": None,
        "item_quantity": None,
        "wine_grapes": None,
        "color_description": None,
        "scent_description": None,
        "taste_description": None,
        "fruit_tasting": None,
        "sugar_tasting": None,
        "acidity_tasting": None,
        "tannin_tasting": None,
        "harmonizes_with": None,
        "technical_sheet_wine_type": None,
        "technical_sheet_volume": None,
        "technical_sheet_closure_type": None,
        "technical_sheet_service_temperature": None,
        "technical_sheet_country": None,
        "technical_sheet_region": None,
        "technical_sheet_alcohol_content": None,
        "technical_sheet_grapes": None,
        "technical_sheet_producer": None,
        "technical_sheet_crop_year": None,
        "technical_sheet_cellaring_time": None,
        "technical_sheet_maturation_time": None,
    }

    # Extrair produto tipo e nome
    product_title = soup.find("h1", class_="BoxProductInfo__Title")
    if product_title:
        tag_type = product_title.find("span", class_="BoxProductInfo__Title__Tagline")
        product_name_elem = product_title.find(
            "span", class_="BoxProductInfo__Title__ProductName"
        )

        wine_data["product_type"] = tag_type.text if tag_type else None
        wine_data["product_name"] = (
            product_name_elem.text if product_name_elem else None
        )

    # Extrair informações de tipo de vinho
    wine_type_elem = soup.find(
        "li", class_="BoxProductInfo__WineDetais__Item__WineType"
    )
    if wine_type_elem and wine_type_elem.find("span"):
        wine_data["technical_sheet_wine_type"] = wine_type_elem.text

    # Extrair quantidade de itens (se for um kit)
    # Exemplo: extrair "3" de "Kit 3 Malbecs Best Sellers"
    wine_data["item_quantity"] = soup.find("li")

    # Extrair informações da ficha técnica
    tech_sheet = soup.find(class_=lambda x: x and "TechnicalSheet" in x)
    if tech_sheet:
        # Mapear rótulos da ficha técnica para campos no banco de dados
        tech_sheet_mapping = {
            "Tipo": "technical_sheet_wine_type",
            "Volume": "technical_sheet_volume",
            "Tipo de Fechamento": "technical_sheet_closure_type",
            "Temperatura de Serviço": "technical_sheet_service_temperature",
            "País": "technical_sheet_country",
            "Região": "technical_sheet_region",
            "Teor Alcoólico": "technical_sheet_alcohol_content",
            "Uva": "technical_sheet_grapes",
            "Produtor": "technical_sheet_producer",
            "Safra": "technical_sheet_crop_year",
            "Tempo de Guarda": "technical_sheet_cellaring_time",
            "Amadurecimento": "technical_sheet_maturation_time",
        }

        # Procurar cada campo na ficha técnica
        tech_items = tech_sheet.find_all("li")
        for item in tech_items:
            label_elem = item.find(class_=lambda x: x and "Label" in x)
            value_elem = item.find(class_=lambda x: x and "Value" in x)

            if label_elem and value_elem:
                label = label_elem.text.strip()
                value = value_elem.text.strip()

                # Mapear para o campo correto no banco de dados
                if label in tech_sheet_mapping:
                    wine_data[tech_sheet_mapping[label]] = value

    # Extrair informações de degustação
    tasting_section = soup.find(class_=lambda x: x and "Tasting" in x)
    if tasting_section:
        # Procurar descrições
        color_elem = tasting_section.find(string=lambda s: s and "Cor:" in s)
        if color_elem and color_elem.find_next():
            wine_data["color_description"] = color_elem.find_next().text.strip()

        aroma_elem = tasting_section.find(string=lambda s: s and "Aroma:" in s)
        if aroma_elem and aroma_elem.find_next():
            wine_data["scent_description"] = aroma_elem.find_next().text.strip()

        taste_elem = tasting_section.find(string=lambda s: s and "Paladar:" in s)
        if taste_elem and taste_elem.find_next():
            wine_data["taste_description"] = taste_elem.find_next().text.strip()

        # Extrair características de degustação
        tasting_indicators = tasting_section.find_all(
            class_=lambda x: x and "Indicator" in x
        )
        for indicator in tasting_indicators:
            label_elem = indicator.find(class_=lambda x: x and "Label" in x)
            value_elem = indicator.find(class_=lambda x: x and "Value" in x)

            if label_elem and value_elem:
                label = label_elem.text.strip().lower()
                value = value_elem.text.strip()

                if "fruta" in label:
                    wine_data["fruit_tasting"] = value
                elif "açúcar" in label or "doce" in label:
                    wine_data["sugar_tasting"] = value
                elif "acid" in label:
                    wine_data["acidity_tasting"] = value
                elif "tanino" in label:
                    wine_data["tannin_tasting"] = value

    # Extrair informações de harmonização
    harmonization = soup.find(string=lambda s: s and "Harmoniza com:" in s)
    if harmonization and harmonization.find_next():
        wine_data["harmonizes_with"] = harmonization.find_next().text.strip()

    # Extrair região e uvas (se não encontrados na ficha técnica)
    if not wine_data["wine_region"] and wine_data["technical_sheet_region"]:
        wine_data["wine_region"] = wine_data["technical_sheet_region"]

    if not wine_data["wine_grapes"] and wine_data["technical_sheet_grapes"]:
        wine_data["wine_grapes"] = wine_data["technical_sheet_grapes"]

    # Extrair variedade (Malbec, Cabernet, etc.)
    if wine_data["product_name"]:
        # Lista de variedades comuns para verificar
        varieties = [
            "Malbec",
            "Cabernet",
            "Sauvignon",
            "Chardonnay",
            "Pinot",
            "Merlot",
            "Shiraz",
            "Syrah",
            "Carmenere",
            "Tannat",
            "Pinot Noir",
            "Riesling",
        ]

        for variety in varieties:
            if variety.lower() in wine_data["product_name"].lower():
                wine_data["wine_variety"] = variety
                break

    return wine_data


def process_unscraped_records(batch_size=10, delay_between_batches=1):
    """
    Processa registros não extraídos do banco de dados
    """
    # Buscar registros não extraídos
    response = (
        supabase.table("products")
        .select("id, html_content")
        .eq("html_downloaded", 1)
        .eq("scraped", 0)
        .limit(batch_size)
        .execute()
    )

    records = response.data

    if not records:
        print("Não há registros para processar.")
        return 0

    processed_count = 0

    for record in records:
        record_id = record["id"]
        html_content = record["html_content"]

        if not html_content:
            # Marcar como processado mesmo se não tiver conteúdo HTML
            supabase.table("products").update({"scraped": 1}).eq(
                "id", record_id
            ).execute()
            continue

        try:
            # Extrair dados
            wine_data = scrape_wine_info(html_content)

            # Inserir dados na tabela wine_data
            # Note: Estamos usando o mesmo ID do produto como chave primária na tabela wine_data
            supabase.table("wine_data").insert({**wine_data, "id": record_id}).execute()

            # Atualizar o status de scraping na tabela products
            supabase.table("products").update({"scraped": 1}).eq(
                "id", record_id
            ).execute()

            processed_count += 1
            print(f"Processado registro ID: {record_id}")

        except Exception as e:
            print(f"Erro ao processar registro ID {record_id}: {str(e)}")

    # Pequena pausa antes de processar o próximo lote
    if processed_count > 0:
        time.sleep(delay_between_batches)

    return processed_count


def run_scraper(max_batches=None):
    """
    Executa o scraper continuamente ou por um número específico de lotes
    """
    batch_count = 0
    total_processed = 0

    while True:
        processed = process_unscraped_records()
        total_processed += processed

        if processed == 0:
            print("Nenhum registro encontrado para processar. Finalizando.")
            break

        batch_count += 1
        print(f"Lote {batch_count} concluído. Total processado: {total_processed}")

        if max_batches and batch_count >= max_batches:
            print(f"Limite de {max_batches} lotes atingido. Finalizando.")
            break


if __name__ == "__main__":
    # Para executar um número específico de lotes:
    # run_scraper(max_batches=5)

    # Para executar até processar todos os registros:
    run_scraper()
