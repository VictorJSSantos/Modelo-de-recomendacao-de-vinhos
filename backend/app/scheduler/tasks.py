import time
import datetime
import schedule
from supabase import Client
import sys

from backend.app.core.browser import initialize_browser, close_browser
from backend.app.database.supabase_client import (
    check_pending_products,
    extract_urls_from_database,
    process_and_upsert_wine_data,
)
from backend.app.core.scraper_aux import *


def schedule_download_tasks(
    driver,
    supabase: Client,
    product_data,
    interval_minutes=30,
    batch_size=10,
    max_batches=1,
):
    """
    Agenda e executa tarefas de download de produtos em lotes.

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        supabase (Client): Cliente do Supabase.
        product_data (list): Lista de produtos com 'id' e 'url'
        interval_minutes (int): Intervalo entre batches em minutos.
        batch_size (int): Quantidade de produtos a baixar por batch.
        max_batches (int): Número máximo de batches a processar.
    """
    print(
        f"Agendando downloads a cada {interval_minutes} minutos, {batch_size} produtos por vez num total de {max_batches} rodadas"
    )

    # Preparar os dados dos produtos
    urls = [item["url"] for item in product_data]
    ids = [item["id"] for item in product_data]
    product_pairs = list(zip(ids, urls))

    # Variáveis para controle global
    batch_counter = [0]  # Contador de batches executados
    total_processed = [0]  # Total de produtos processados com sucesso
    total_not_processed = [0]  # Total de produtos com erro

    def process_batch():
        """Processa um lote de produtos."""
        # Verificar se atingimos o limite de batches
        if batch_counter[0] >= max_batches:
            print(f"Limite de {max_batches} batches atingido. Finalizando.")
            print(
                f"""Processamento concluído. 
                \nTotal de itens processados com sucesso: {total_processed[0]}
                \nTotal de itens com falha: {total_not_processed[0]}"""
            )
            return schedule.CancelJob

        # Calcular o índice inicial e final para este batch
        start_idx = batch_counter[0] * batch_size
        end_idx = min(start_idx + batch_size, len(product_pairs))

        # Verificar se ainda há produtos para processar
        if start_idx >= len(product_pairs):
            print("Todos os produtos foram processados.")
            return schedule.CancelJob

        # Processar este batch
        print(f"\n---- Processando batch {batch_counter[0] + 1}/{max_batches} ----")
        # print(f"Processando produtos {start_idx + 1} até {end_idx} de {len(product_pairs)}")

        batch_processed = 0
        batch_failed = 0

        for i in range(start_idx, end_idx):
            current_id, current_url = product_pairs[i]
            print(f"Processando produto {i + 1}/{len(product_pairs)}: ID {current_id}")

            # Executar a extração para este produto
            try:
                processed = process_and_upsert_wine_data(
                    driver, current_url, current_id
                )
                if processed >= 0:
                    batch_processed += 1
                    total_processed[0] += 1
                else:
                    batch_failed += 1
                    total_not_processed[0] += 1
            except Exception as e:
                print(f"Erro ao processar produto {current_id}: {str(e)}")
                batch_failed += 1
                total_not_processed[0] += 1

        # Relatório deste batch
        print(
            f"""Batch {batch_counter[0] + 1} concluído.
            Produtos processados neste batch: {batch_processed}
            Produtos com falha neste batch: {batch_failed}
            Total geral processado: {total_processed[0]}
            Total geral com falha: {total_not_processed[0]}"""
        )

        # Incrementar o contador de batches
        batch_counter[0] += 1

        # Verificar se é o último batch
        if batch_counter[0] >= max_batches or end_idx >= len(product_pairs):
            print("Processamento completo. Cancelando agendamento.")
            return schedule.CancelJob

    process_batch()

    # Agendar os próximos batches com o intervalo especificado
    if batch_counter[0] < max_batches and batch_counter[0] * batch_size < len(
        product_pairs
    ):
        schedule.every(interval_minutes).minutes.do(process_batch)

        # Loop principal para manter o programa rodando e executando os batches agendados
        while batch_counter[0] < max_batches and batch_counter[0] * batch_size < len(
            product_pairs
        ):
            try:
                schedule.run_pending()
                time.sleep(1)  # Verificar a cada segundo se há tarefas pendentes

                if check_pending_products(supabase) == 0:
                    print("Não há mais produtos pendentes no banco de dados.")
                    break

            except KeyboardInterrupt:
                print("Programa interrompido pelo usuário.")
                break
            except Exception as e:
                print(f"Erro no loop principal: {e}")
                time.sleep(60)  # Continua mesmo com erros após uma pausa

    return total_processed[0], total_not_processed[0]


def run_extraction(driver, url, id):
    """
    Executa a extração de dados para um único produto.

    Args:
        driver (webdriver.Chrome): Initialized Selenium webdriver
        url (str): URL do produto a ser extraído
        id (str/int): ID do produto

    Returns:
        int: Status do processamento (>= 0 para sucesso, < 0 para falha)
    """
    print(f"Iniciando extração para o produto ID {id}...")

    if not driver:
        print("Falha ao inicializar o navegador. Abortando.")
        return -1

    try:
        if not url:
            print("URL inválida.")
            return -1

        # Processar URL única
        return process_and_upsert_wine_data(driver, url, id)

    except Exception as e:
        print(f"\nErro durante a extração: {str(e)}\n")
        return -1
