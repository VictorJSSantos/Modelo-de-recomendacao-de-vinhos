import boto3
import logging
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.app.config.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    AWS_REGION,
    RAW_BUCKET,
    OBJS_RAW_BUCKET,
    IMAGES_RAW_BUCKET,
    IMAGE_PATH,
    JSON_OBJS_PATH,
)

# # Configurações
# AWS_ACCESS_KEY = "sua_access_key" # Não tá habilitado para pegar as informações na aws
# AWS_SECRET_KEY = "sua_secret_key" # Não tá habilitado para pegar as informações na aws
# BUCKET_NAME = "evinoimgagem" # s3://evinoimgagem/imagens/
# LOCAL_IMAGE_DIR = r"C:\Users\tatia\OneDrive\Documentos\Cursos\FIAP\POS - Eng ML\Arquitetura ML e Aprendizado\Projeto\Imagens"
# S3_FOLDER = "imagens/"  # Pasta dentro do S3 onde as imagens serão salvas

logger = logging.getLogger("evino_scraper")


s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
)


def upload_to_s3(
    file_path,
    bucket_name,
    prefix="",
    allowed_extensions=[".jpg", ".png", ".json"],
    skip_existing=True,
):
    """
    Faz upload de um arquivo para o Amazon S3, verificando se o arquivo já existe.

    Args:
        file_path (str): Caminho local para o arquivo
        bucket_name (str): Nome do bucket do S3
        prefix (str, opcional): Prefixo da pasta no S3 (ex: 'images/', 'data/')
        allowed_extensions (list, opcional): Lista de extensões permitidas
        skip_existing (bool, opcional): Se True, pula arquivos que já existem no S3
    Returns:
        bool: True se o upload foi bem-sucedido ou o arquivo já existe, False caso contrário
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Erro: Arquivo {file_path} não encontrado!")
            return False

        file_name = os.path.basename(file_path)

        if allowed_extensions:
            _, ext = os.path.splitext(file_name.lower())
            if ext not in allowed_extensions:
                logger.warning(
                    f"Erro: Arquivo {file_name} com extensão {ext} não permitida!"
                )
                return False

        s3_key = f"{prefix}{file_name}" if prefix else file_name

        try:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            if skip_existing:
                logger.info(
                    f"Arquivo {s3_key} já existe no bucket {bucket_name}. Upload ignorado."
                )
                return True
            else:
                logger.info(
                    f"Arquivo {s3_key} já existe no bucket {bucket_name}. Substituindo..."
                )
        except:
            pass

        s3_client.upload_file(file_path, bucket_name, s3_key)
        logger.info(f"{file_name} enviado com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro ao fazer upload de {file_path}: {str(e)}")
        return False


if __name__ == "__main__":

    ans = input("Quer processar imagens para o S3? s/n")
    if ans == "s":
        upload_to_s3(
            IMAGE_PATH,
            RAW_BUCKET,
            IMAGES_RAW_BUCKET,
            allowed_extensions=[".jpg", ".png"],
        )
    else:
        logger.info("Processamento de imagens para o S3 não foi realizado.")

    ans = input("Quer processar os arquivos JSON para o S3? s/n")
    if ans == "s":
        upload_to_s3(
            JSON_OBJS_PATH, RAW_BUCKET, OBJS_RAW_BUCKET, allowed_extensions=[".json"]
        )
    else:
        logger.info("Processamento de arquivos JSON para o S3 não foi realizado.")
