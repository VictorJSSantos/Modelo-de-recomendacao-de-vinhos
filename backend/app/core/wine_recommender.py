import joblib
import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


class WineRecommender:
    def __init__(self, dataframe):
        self.df = dataframe
        self.prepare_features()

    def prepare_features(self):
        """Definir aqui quais colunas serão usadas para definir a similaridade,
        podemos, no limite, botar todas as caracteristicas que quisermos, basta
        apenas separar entre o que é texto e o que é numérico.
        """
        self.text_columns = [
            "product_name",
            "color_description",
            "scent_description",
            "taste_description",
            "harmonizes_with",
            "technical_sheet_wine_type",
            "technical_sheet_grapes",
            "technical_sheet_region",
            "technical_sheet_country",
        ]

        self.numeric_columns = [
            "fruit_tasting",
            "sugar_tasting",
            "acidity_tasting",
            "tannin_tasting",
        ]

        # Lidamos com nulos e realizamos um join em todas as características de texto em uma coluna.
        self.df["combined_text_features"] = (
            self.df[self.text_columns]
            .fillna("")
            .apply(lambda x: " ".join(x.astype(str)), axis=1)
        )

        # Ralizamos uma Vetorização TF-IDF
        self.vectorizer = TfidfVectorizer()
        self.text_matrix = self.vectorizer.fit_transform(
            self.df["combined_text_features"]
        )

        """Normalização de características numéricas. As colunas como estão 
           talvez não fosse necessário, porém para as demais características como 
           temperatura e quantidade de alcool precise"""
        self.numeric_scaler = MinMaxScaler()
        self.numeric_features_normalized = self.numeric_scaler.fit_transform(
            self.df[self.numeric_columns].fillna(self.df[self.numeric_columns].mean())
        )

    def recommend_wines(self, input_features, top_n=5):
        """
        Recomenda vinhos baseado em características de entrada

        Parâmetros:
        input_features (dict): Dicionário com características de entrada
        top_n (int): Número de recomendações

        Retorna:
        list: Lista de IDs de vinhos recomendados
        """

        # Aqui filtraremos o que é texto e numérico. Pegamos o que foi inputado, que não é None, e criamos um dict.
        text_input = {
            k: v
            for k, v in input_features.items()
            if k in self.text_columns and v is not None
        }

        numeric_input = {
            k: v
            for k, v in input_features.items()
            if k in self.numeric_columns and v is not None
        }

        similarities = []

        # Similaridade textual: Fazemos um join em todos os values do dict e aplicamos o cosine similarity.
        # Note que é pego a coluna 0 do text_matriz
        if text_input:
            input_text = " ".join(str(v) for v in text_input.values())
            input_vector = self.vectorizer.transform([input_text])
            text_similarity = cosine_similarity(input_vector, self.text_matrix)[0]
            similarities.append(text_similarity)

        # Similaridade numérica:
        if numeric_input:
            # Preparar entrada numérica: Separamos em uma lista de arrays com os
            # valores de cada coluna e uma lista de nomes de colunas.
            # Isso é feito a partir do dict numeric_input
            input_numeric_arr = []
            input_numeric_cols = []

            for col, value in numeric_input.items():
                if col in self.numeric_columns:
                    input_numeric_arr.append(value)
                    input_numeric_cols.append(col)

            if input_numeric_arr:
                # Normalizar entrada numérica -> Para todos os efeitos aplicamos aqui a transformação MinMax
                input_numeric_normalized = self.numeric_scaler.transform(
                    pd.DataFrame([input_numeric_arr], columns=input_numeric_cols)
                )

                # Calcular similaridade numérica
                numeric_similarities = []
                for normalized_row in self.numeric_features_normalized:
                    # Extrair valores correspondentes às colunas de entrada e calcular distância
                    row_subset = normalized_row[
                        [self.numeric_columns.index(col) for col in input_numeric_cols]
                    ]
                    distance = np.linalg.norm(row_subset - input_numeric_normalized[0])
                    numeric_similarities.append(1 / (1 + distance))

                similarities.append(numeric_similarities)

        # Aqui acessamos as similaridades e filtramos os ids de cada vinho na nossa db
        if similarities:
            final_similarity = np.mean(similarities, axis=0)
            top_indices = final_similarity.argsort()[-top_n:][::-1]
            return self.df.iloc[top_indices]["id"].tolist()

        return []

    def salvar_modelo(
        self, caminho="../backend/app/core/model/wine_recommender_model.pkl"
    ):
        """
        Salva o modelo treinado em um arquivo.

        Parâmetros:
        -----------
        caminho : str, opcional (padrão='wine_recommender_model.pkl')
            Caminho completo onde o modelo será salvo

        Retorna:
        --------
        str
            Caminho completo onde o modelo foi salvo

        Raises:
        -------
        ValueError
            Se nenhum modelo tiver sido treinado
        """
        # Verificar se o modelo existe
        if self.modelo is None:
            raise ValueError(
                "Nenhum modelo foi treinado ainda. Treine o modelo antes de salvá-lo."
            )

        # Garantir que o diretório existe
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)

        # Salvar modelo completo (incluindo o objeto do recomendador)
        try:
            joblib.dump(self, caminho)
            print(f"Modelo salvo com sucesso em: {caminho}")
            return caminho
        except Exception as e:
            print(f"Erro ao salvar o modelo: {e}")
            raise

    @classmethod
    def carregar_modelo(
        cls, caminho="../backend/app/core/model/wine_recommender_model.pkl"
    ):
        """
        Carrega um modelo salvo.

        Parâmetros:
        -----------
        caminho : str, opcional (padrão='wine_recommender_model.pkl')
            Caminho completo do modelo a ser carregado

        Retorna:
        --------
        WineRecommender
            Instância do recomendador com o modelo carregado

        Raises:
        -------
        FileNotFoundError
            Se o arquivo do modelo não for encontrado
        """
        # Verificar se o arquivo existe
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {caminho}")

        try:
            # Carregar o modelo
            modelo_carregado = joblib.load(caminho)
            print(f"Modelo carregado com sucesso de: {caminho}")
            return modelo_carregado
        except Exception as e:
            print(f"Erro ao carregar o modelo: {e}")
            raise


# Função de conversão de DataFrame para garantir que ele terá as features necessárias
# Muito provavelmente estará deprecado e não precisaremos mais devido a
# feature engineering para garantir os inptus corretos
def converter_dataframe(df_original):
    df = df_original.copy()
    colunas_numericas = [
        "sugar_tasting",
        "acidity_tasting",
        "tannin_tasting",
        "technical_sheet_alcohol_content",
    ]
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.replace("None", np.nan)

    return df
