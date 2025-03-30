import boto3
import os

# Configurações
AWS_ACCESS_KEY = "sua_access_key" # Não tá habilitado para pegar as informações na aws
AWS_SECRET_KEY = "sua_secret_key" # Não tá habilitado para pegar as informações na aws
BUCKET_NAME = "evinoimgagem" # s3://evinoimgagem/imagens/
LOCAL_IMAGE_DIR = r"C:\Users\tatia\OneDrive\Documentos\Cursos\FIAP\POS - Eng ML\Arquitetura ML e Aprendizado\Projeto\Imagens"
S3_FOLDER = "imagens/"  # Pasta dentro do S3 onde as imagens serão salvas

# Conectar ao S3
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Percorrer as imagens no diretório local
for file_name in os.listdir(LOCAL_IMAGE_DIR):
    file_path = os.path.join(LOCAL_IMAGE_DIR, file_name)

    # Verificar se é um arquivo de imagem
    if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
        s3_key = S3_FOLDER + file_name  # Caminho dentro do S3

        print(f"Enviando {file_name} para S3 em {s3_key}...")
        
        # Fazer upload da imagem
        s3_client.upload_file(file_path, BUCKET_NAME, s3_key)

        print(f"{file_name} enviado com sucesso!")

print("Processo concluído!")
