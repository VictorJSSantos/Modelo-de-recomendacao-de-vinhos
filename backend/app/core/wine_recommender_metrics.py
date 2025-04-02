import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


class JaccardWineEvaluator:
    """
    Classe para avaliar recomendador de vinhos usando métrica Jaccard modificada
    """

    def __init__(self, recommender, dataframe):
        """
        Inicializa o avaliador

        Parâmetros:
        recommender (WineRecommender): Modelo de recomendação a ser avaliado
        dataframe (pd.DataFrame): DataFrame completo de vinhos
        """
        self.recommender = recommender
        self.df = dataframe

        self.categorical_columns = [
            col
            for col in [
                "technical_sheet_wine_type",
                "technical_sheet_region",
                "technical_sheet_country",
                "harmonizes_with",
            ]
            if col in self.df.columns
        ]

        self.numeric_columns = [
            col
            for col in [
                "fruit_tasting",
                "sugar_tasting",
                "acidity_tasting",
                "tannin_tasting",
            ]
            if col in self.df.columns
        ]

    def _jaccard_similarity(self, wine1, wine2, weighted=True):
        """
        Calcula similaridade Jaccard modificada entre dois vinhos

        Parâmetros:
        wine1 (Series): Primeiro vinho
        wine2 (Series): Segundo vinho
        weighted (bool): Se deve aplicar pesos às características

        Retorna:
        float: Valor da similaridade Jaccard modificada
        """
        # Definir pesos para diferentes características (se necessário)
        weights = {
            "technical_sheet_wine_type": 1.5,
            "technical_sheet_region": 1.2,
            "technical_sheet_country": 0.8,
            "harmonizes_with": 1.0,
            "fruit_tasting": 1.0,
            "sugar_tasting": 1.3,
            "acidity_tasting": 1.2,
            "tannin_tasting": 1.1,
        }

        # Inicializar contadores
        intersection = 0
        union = 0

        # Calcular para colunas categóricas
        for col in self.categorical_columns:
            if col in wine1.index and col in wine2.index:
                if not pd.isna(wine1[col]) and not pd.isna(wine2[col]):
                    # Para valores de texto, considerar parcialmente
                    if wine1[col] == wine2[col]:
                        if weighted:
                            intersection += weights.get(col, 1.0)
                        else:
                            intersection += 1
                    # Para harmonizes_with, checar tokens compartilhados
                    elif col == "harmonizes_with":
                        tokens1 = set(str(wine1[col]).lower().split(","))
                        tokens2 = set(str(wine2[col]).lower().split(","))

                        common_tokens = tokens1.intersection(tokens2)
                        if common_tokens:
                            token_ratio = len(common_tokens) / len(
                                tokens1.union(tokens2)
                            )
                            if weighted:
                                intersection += token_ratio * weights.get(col, 1.0)
                            else:
                                intersection += token_ratio

                    if weighted:
                        union += weights.get(col, 1.0)
                    else:
                        union += 1

        # Calcular para colunas numéricas
        for col in self.numeric_columns:
            if col in wine1.index and col in wine2.index:
                if not pd.isna(wine1[col]) and not pd.isna(wine2[col]):
                    # Para valores numéricos, calcular proximidade relativa
                    max_val = 10.0  # Assumindo escala 0-10
                    diff = abs(float(wine1[col]) - float(wine2[col])) / max_val
                    similarity = 1 - diff  # Normalizado entre 0-1

                    if weighted:
                        intersection += similarity * weights.get(col, 1.0)
                        union += weights.get(col, 1.0)
                    else:
                        intersection += similarity
                        union += 1

        # Calcular Jaccard
        if union == 0:
            return 0
        return intersection / union

    def evaluate_recommendations(self, test_size=0.2, num_tests=100, top_n=5):
        """
        Avalia as recomendações usando a métrica Jaccard

        Parâmetros:
        test_size (float): Proporção do conjunto de teste
        num_tests (int): Número de testes a realizar
        top_n (int): Número de recomendações a considerar

        Retorna:
        dict: Resultados da avaliação
        """
        # Separar conjunto de teste
        _, test_df = train_test_split(self.df, test_size=test_size, random_state=42)

        # Limitar número de testes se necessário
        test_samples = test_df.sample(min(num_tests, len(test_df)))

        jaccard_scores = []
        coverage = set()
        diversidade_interna = []

        for _, wine in test_samples.iterrows():
            # Criar input de características
            input_features = {}
            for col in self.categorical_columns + self.numeric_columns:
                if pd.notna(wine[col]):
                    input_features[col] = wine[col]

            # Obter recomendações
            recomendacoes = self.recommender.recommend_wines(
                input_features, top_n=top_n
            )

            # Adicionar à cobertura
            coverage.update(recomendacoes)

            # Calcular jaccard médio entre vinho base e recomendações
            jacc_scores = []
            for rec_id in recomendacoes:
                rec_wine = self.df[self.df["id"] == rec_id].iloc[0]
                jacc = self._jaccard_similarity(wine, rec_wine)
                jacc_scores.append(jacc)

            # Adicionar à lista geral
            if jacc_scores:
                jaccard_scores.append(np.mean(jacc_scores))

            # Calcular diversidade interna das recomendações
            if len(recomendacoes) > 1:
                internal_scores = []
                for i, rec_id1 in enumerate(recomendacoes):
                    for rec_id2 in recomendacoes[i + 1 :]:
                        rec_wine1 = self.df[self.df["id"] == rec_id1].iloc[0]
                        rec_wine2 = self.df[self.df["id"] == rec_id2].iloc[0]
                        sim = self._jaccard_similarity(rec_wine1, rec_wine2)
                        internal_scores.append(sim)

                # Diversidade = 1 - similaridade média interna
                if internal_scores:
                    diversidade_interna.append(1 - np.mean(internal_scores))

        # Calcular métricas agregadas
        resultados = {
            "jaccard_médio": np.mean(jaccard_scores) if jaccard_scores else 0,
            "jaccard_desvio": np.std(jaccard_scores) if jaccard_scores else 0,
            "cobertura": len(coverage) / len(self.df),
            "diversidade_interna": (
                np.mean(diversidade_interna) if diversidade_interna else 0
            ),
        }

        return resultados

    def evaluate_by_types(self, types=None):
        """
        Avalia as recomendações por tipos de vinhos

        Parâmetros:
        types (list): Lista de tipos de vinho a avaliar, ou None para todos

        Retorna:
        dict: Resultados por tipo de vinho
        """
        if "technical_sheet_wine_type" not in self.df.columns:
            return {"error": "Coluna de tipo de vinho não disponível"}

        if types is None:
            types = self.df["technical_sheet_wine_type"].unique()

        resultados_por_tipo = {}

        for tipo in types:
            # Filtrar vinhos do tipo específico
            vinhos_tipo = self.df[self.df["technical_sheet_wine_type"] == tipo]
            if len(vinhos_tipo) < 5:  # Precisamos de alguns exemplos
                continue

            # Selecionar amostra para teste
            amostra_teste = vinhos_tipo.sample(min(20, len(vinhos_tipo)))

            jaccard_scores = []

            for _, wine in amostra_teste.iterrows():
                # Criar input de características
                input_features = {}
                for col in self.categorical_columns + self.numeric_columns:
                    if pd.notna(wine[col]):
                        input_features[col] = wine[col]

                # Obter recomendações
                recomendacoes = self.recommender.recommend_wines(
                    input_features, top_n=5
                )

                # Calcular jaccard médio
                jacc_scores = []
                for rec_id in recomendacoes:
                    rec_wine = self.df[self.df["id"] == rec_id].iloc[0]
                    jacc = self._jaccard_similarity(wine, rec_wine)
                    jacc_scores.append(jacc)

                if jacc_scores:
                    jaccard_scores.append(np.mean(jacc_scores))

            # Adicionar resultados para o tipo
            resultados_por_tipo[tipo] = {
                "jaccard_médio": np.mean(jaccard_scores) if jaccard_scores else 0,
                "número_amostras": len(amostra_teste),
            }

        return resultados_por_tipo


# Exemplo de uso:
# evaluator = JaccardWineEvaluator(wine_recommender, wine_dataframe)
# results = evaluator.evaluate_recommendations(num_tests=50)
# print(f"Jaccard Médio: {results['jaccard_médio']:.3f}")
# print(f"Cobertura: {results['cobertura']:.2%}")
# print(f"Diversidade Interna: {results['diversidade_interna']:.3f}")
