import boto3
import logging
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
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

        # Verifica se o arquivo já existe no S3
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
        except s3_client.exceptions.ClientError as e:
            # Se o erro for 404, significa que o arquivo não existe e pode ser enviado
            if e.response["Error"]["Code"] != "404":
                logger.error(f"Erro ao verificar existência do arquivo no S3: {str(e)}")
                return False

        # Faz o upload do arquivo
        s3_client.upload_file(file_path, bucket_name, s3_key)
        logger.info(f"{file_name} enviado com sucesso!")
        return True

    except Exception as e:
        logger.error(f"Erro ao fazer upload de {file_path}: {str(e)}")
        return False


def upload_directory_to_s3(
    directory_path, bucket_name, prefix="", allowed_extensions=None
):
    """
    Faz upload de todos os arquivos dentro de um diretório para o Amazon S3.

    Args:
        directory_path (str): Caminho do diretório local
        bucket_name (str): Nome do bucket do S3
        prefix (str, opcional): Prefixo da pasta no S3
        allowed_extensions (list, opcional): Lista de extensões permitidas
    """
    if not os.path.exists(directory_path):
        logger.error(f"Erro: Diretório {directory_path} não encontrado!")
        return

    files_uploaded = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            if upload_to_s3(file_path, bucket_name, prefix, allowed_extensions):
                files_uploaded += 1

    logger.info(f"Total de arquivos enviados: {files_uploaded}")


if __name__ == "__main__":

    ans = input("Quer processar imagens para o S3? s/n:\t")
    if ans.lower() == "s":
        upload_directory_to_s3(
            IMAGE_PATH,
            RAW_BUCKET,
            IMAGES_RAW_BUCKET,
            allowed_extensions=[".jpg", ".png"],
        )
    else:
        logger.info("Processamento de imagens para o S3 não foi realizado.")

    ans = input("Quer processar os arquivos JSON para o S3? s/n\t")
    if ans.lower() == "s":
        upload_directory_to_s3(
            JSON_OBJS_PATH, RAW_BUCKET, OBJS_RAW_BUCKET, allowed_extensions=[".json"]
        )
    else:
        logger.info("Processamento de arquivos JSON para o S3 não foi realizado.")
