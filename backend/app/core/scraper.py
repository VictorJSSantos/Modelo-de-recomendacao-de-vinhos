import time
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client
import sys
import os
import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from backend.app.config.settings import (
    SUPABASE_URL,
    SUPABASE_KEY,
    EVINO_BASE_URL,
    MAX_SCROLLS,
    BUTTON_CLICK_DELAY,
    SCROLL_DELAY,
)
from backend.app.core.scraper_aux import *
from backend.app.scheduler.tasks import *


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def scrape_wine_info_with_selenium(driver, url=EVINO_BASE_URL):
    """
    Loads a wine product page with Selenium and extracts detailed information
    while the page is rendered

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        url (str): URL of the wine product page

    Returns:
        dict: Extracted wine data
    """
    print(f"Navegando para: {url}")

    try:

        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "BoxProductInfo__Title"))
        )

        html_content = driver.page_source
        scroll_page(driver)
        click_button_show_tech_details(driver)

        soup = BeautifulSoup(html_content, "html.parser")

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
            "harmonizes_with": None,
            "fruit_tasting": None,
            "sugar_tasting": None,
            "acidity_tasting": None,
            "tannin_tasting": None,
            "technical_sheet_wine_type": None,
            "technical_sheet_alcohol_content": None,
            "technical_sheet_volume": None,
            "technical_sheet_grapes": None,
            "technical_sheet_closure_type": None,
            "technical_sheet_service_temperature": None,
            "technical_sheet_country": None,
            "technical_sheet_region": None,
            "technical_sheet_producer": None,
            "technical_sheet_crop_year": None,
            "technical_sheet_cellaring_time": None,
            "technical_sheet_maturation_time": None,
            "created_at": datetime.datetime.now().isoformat(),  # Add timestamp
            "specialist_review_content": None,
            "specialist_review_owner": None,
            "specialist_review_occupation": None,
            "photo_url": None,
        }

        # Extract product type and name
        product_title = soup.find("h1", class_="BoxProductInfo__Title")
        if product_title:
            tag_type = product_title.find(
                "span", class_="BoxProductInfo__Title__Tagline"
            )
            product_name_elem = product_title.find(
                "span", class_="BoxProductInfo__Title__ProductName"
            )

            wine_data["product_type"] = tag_type.text.strip() if tag_type else None
            wine_data["product_name"] = (
                product_name_elem.text.strip() if product_name_elem else None
            )

        # Extract wine type information
        wine_type_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__WineType"
        )
        if wine_type_elem and wine_type_elem.find("span"):
            wine_data["wine_variety"] = wine_type_elem.text.strip()

        # Extract wine region
        wine_region_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__CountryAndRegion--Country"
        )
        if wine_region_elem and wine_region_elem.find("div"):
            wine_data["wine_region"] = wine_region_elem.text.strip()

        # Extract item quantity
        wine_quantity_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__QuantityInBundle"
        )
        if wine_quantity_elem and wine_quantity_elem.find("span"):
            wine_data["item_quantity"] = wine_quantity_elem.text.strip()
        else:
            wine_data["item_quantity"] = 1

        # Extract grape types
        wine_grapes_elem = soup.find(
            "li", class_="BoxProductInfo__WineDetais__Item__Grapes"
        )
        if wine_grapes_elem and wine_grapes_elem.find("span"):
            wine_data["wine_grapes"] = wine_grapes_elem.text.strip()

        # Extract wine color description
        if soup and soup.find("p", id="visualColor"):
            wine_data["color_description"] = soup.find(id="visualColor").text

        # Extract wine scent description
        if soup and soup.find(id="aroma"):
            wine_data["scent_description"] = soup.find(id="aroma").text

        # Extract wine taste description
        if soup and soup.find(id="mouth"):
            wine_data["taste_description"] = soup.find(id="mouth").text

        # Extract wine harmonization information
        wine_harmonizes_with_elem = soup.find(
            "div",
            class_="HowToTaste__DetailsContainer HowToTaste__DetailsContainer__Tablet",
        )
        if wine_harmonizes_with_elem and wine_harmonizes_with_elem.find(
            "p", id="pairingsTablet"
        ):
            wine_data["harmonizes_with"] = wine_harmonizes_with_elem.find(
                "p", id="pairingsTablet"
            ).text.strip()

        # Extract wine strength data
        try:
            wine_data["fruit_tasting"] = get_strength_level(driver, "Fruta")
            wine_data["sugar_tasting"] = get_strength_level(driver, "Açúcar")
            wine_data["acidity_tasting"] = get_strength_level(driver, "Acidez")
            wine_data["tannin_tasting"] = get_strength_level(driver, "Tanino")

        except Exception as e:
            print(f"Erro ao extrair dados de força do vinho: {str(e)}")

        # Extract technical specifications
        try:
            wine_specs_elem = soup.find_all(
                "div",
                class_="ProductSpecifications__DetailsContainer",
            )
            specs = {}

            for wine_spec in wine_specs_elem:
                spec_title = wine_spec.find("h4", class_="sc-jlZhew")
                spec_value = wine_spec.find("p", class_="sc-jXbUNg")

                if spec_title and spec_value:
                    spec_title = spec_title.text.strip()
                    spec_value = spec_value.text.strip()
                    specs[spec_title] = spec_value

            # Map specifications to wine_data fields
            if specs:
                field_mapping = {
                    "Tipo de vinho": "technical_sheet_wine_type",
                    "Teor alcoólico": "technical_sheet_alcohol_content",
                    "Volume": "technical_sheet_volume",
                    "Uvas": "technical_sheet_grapes",
                    "Tipo de fechamento": "technical_sheet_closure_type",
                    "Temperatura de serviço": "technical_sheet_service_temperature",
                    "País": "technical_sheet_country",
                    "Região": "technical_sheet_region",
                    "Produtor": "technical_sheet_producer",
                    "Safra": "technical_sheet_crop_year",
                    "Tempo de guarda": "technical_sheet_cellaring_time",
                    "Maturação": "technical_sheet_maturation_time",
                }

                for spec_key, data_key in field_mapping.items():
                    if spec_key in specs:
                        wine_data[data_key] = specs[spec_key]

            # Extract Specialist Content
            try:
                specialist_content_elem = soup.find(
                    "div", class_="SpecialistOpinion__Container"
                )

                # Extracting specialist name
                specialist_name_and_occupation = specialist_content_elem.find(
                    "div",
                    class_="SpecialistOpinion__SommelierContainer__SommelierInfos",
                )
                if specialist_content_elem and specialist_name_and_occupation:
                    wine_data["specialist_review_owner"] = (
                        specialist_name_and_occupation.find(
                            "h4", class_="sc-jlZhew bMxkvj"
                        ).text
                    )
                # Extracting specialist occupation
                if specialist_content_elem and specialist_name_and_occupation:
                    wine_data["specialist_review_occupation"] = (
                        specialist_name_and_occupation.find(
                            "p", class_="sc-jXbUNg ejYBXU"
                        ).text
                    )

                # Extracting review content  SpecialistOpinion__ReviewContainer ReviewBorderBottom
                specialist_review_content_elem = specialist_content_elem.find(
                    "div",
                    class_="SpecialistOpinion__ReviewContainer ReviewBorderBottom",
                )
                specialist_review_content = specialist_review_content_elem.find(
                    "p", class_="sc-jXbUNg ejYBXU"
                ).text
                if specialist_review_content_elem and specialist_review_content:
                    wine_data["specialist_review_content"] = specialist_review_content

                baixar_imagem(driver, url, wine_data["product_name"])

            finally:
                pass

        except Exception as e:
            print(f"Erro ao extrair especificações técnicas: {str(e)}")

        return wine_data

    except Exception as e:
        print(
            f"Erro ao processar página {url}: TESTE AQUI DA FUNCAO SCRAPER.PY"
        )  # {str(e)}
        return None
