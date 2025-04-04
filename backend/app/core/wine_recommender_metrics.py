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

        # Usar as mesmas colunas definidas no recomendador
        self.text_columns = recommender.text_columns
        self.categorical_columns = recommender.categoric_columns
        self.ordinal_columns = recommender.ordinal_columns

        print(
            f"Avaliador inicializado com {len(self.text_columns)} colunas de texto, "
            f"{len(self.categorical_columns)} colunas categóricas e {len(self.ordinal_columns)} colunas ordinais"
        )

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
            "technical_sheet_country": 1.2,
            "harmonizes_with": 1.2,
            "fruit_tasting": 1,
            "sugar_tasting": 1,
            "acidity_tasting": 1,
            "tannin_tasting": 1,
        }

        # Inicializar contadores
        intersection = 0
        union = 0
        used_features = 0

        # Calcular para colunas textuais
        for col in self.text_columns:
            if col in wine1.index and col in wine2.index:
                if pd.notna(wine1[col]) and pd.notna(wine2[col]):
                    weight = weights.get(col, 1.0) if weighted else 1.0

                    if col == "harmonizes_with":
                        # Comparação tokenizada para 'harmonizes_with'
                        tokens1 = set(str(wine1[col]).lower().split(","))
                        tokens2 = set(str(wine2[col]).lower().split(","))
                        common_tokens = tokens1.intersection(tokens2)
                        all_tokens = tokens1.union(tokens2)

                        if all_tokens:
                            token_ratio = len(common_tokens) / len(all_tokens)
                            intersection += token_ratio * weight
                            union += weight
                            used_features += 1
                    else:
                        # Para outras variáveis textuais, comparação direta
                        if str(wine1[col]).lower() == str(wine2[col]).lower():
                            intersection += weight
                        union += weight
                        used_features += 1

        # Calcular para colunas categóricas
        for col in self.categorical_columns:
            if col in wine1.index and col in wine2.index:
                if pd.notna(wine1[col]) and pd.notna(wine2[col]):
                    weight = weights.get(col, 1.0) if weighted else 1.0

                    if str(wine1[col]).lower() == str(wine2[col]).lower():
                        intersection += weight
                    union += weight
                    used_features += 1

        # Calcular para colunas ordinais
        for col in self.ordinal_columns:
            if col in wine1.index and col in wine2.index:
                if pd.notna(wine1[col]) and pd.notna(wine2[col]):
                    weight = weights.get(col, 1.0) if weighted else 1.0

                    try:
                        # Para valores numéricos, calcular proximidade relativa
                        val1 = float(wine1[col])
                        val2 = float(wine2[col])
                        max_val = 10.0  # Assumindo escala 0-10
                        diff = abs(val1 - val2) / max_val
                        similarity = 1 - diff  # Normalizado entre 0-1

                        intersection += similarity * weight
                        union += weight
                        used_features += 1
                    except (ValueError, TypeError):
                        # Ignorar se não conseguir converter para float
                        pass

        # Calcular Jaccard
        if union == 0:
            return 0

        jaccard = intersection / union
        return jaccard

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
        test_samples = test_df.sample(min(num_tests, len(test_df))).reset_index(
            drop=True
        )
        print(f"Avaliando {len(test_samples)} amostras de teste")

        jaccard_scores = []
        coverage = set()
        diversidade_interna = []
        sucessos = 0
        erros = 0

        for idx, wine in test_samples.iterrows():
            try:
                # Criar input de características
                input_features = {}

                # Incluir características de texto
                for col in self.text_columns:
                    if pd.notna(wine[col]):
                        input_features[col] = wine[col]

                # Incluir características categóricas
                for col in self.categorical_columns:
                    if pd.notna(wine[col]):
                        input_features[col] = wine[col]

                # Incluir características ordinais
                for col in self.ordinal_columns:
                    if pd.notna(wine[col]):
                        input_features[col] = wine[col]

                # Verificar se há características suficientes
                if len(input_features) == 0:
                    print(f"Amostra {idx} não tem características suficientes")
                    continue

                # Obter recomendações
                recomendacoes = self.recommender.recommend_wines(
                    input_features, top_n=top_n
                )

                if not recomendacoes:
                    print(f"Sem recomendações para amostra {idx}")
                    continue

                # Adicionar à cobertura
                coverage.update(recomendacoes)

                # Calcular jaccard médio entre vinho base e recomendações
                jacc_scores = []
                for rec_id in recomendacoes:
                    rec_wine_df = self.df[self.df["id"] == rec_id]
                    if len(rec_wine_df) == 0:
                        print(f"ID de vinho não encontrado: {rec_id}")
                        continue

                    rec_wine = rec_wine_df.iloc[0]
                    jacc = self._jaccard_similarity(wine, rec_wine)
                    jacc_scores.append(jacc)

                # Adicionar à lista geral
                if jacc_scores:
                    jaccard_scores.append(np.mean(jacc_scores))
                    sucessos += 1

                    if idx % 20 == 0:  # Mostrar progresso
                        print(
                            f"Amostra {idx}: Jaccard médio = {np.mean(jacc_scores):.4f}"
                        )

                # Calcular diversidade interna das recomendações
                if len(recomendacoes) > 1:
                    internal_scores = []
                    for i, rec_id1 in enumerate(recomendacoes):
                        rec_wine1_df = self.df[self.df["id"] == rec_id1]
                        if len(rec_wine1_df) == 0:
                            continue

                        for rec_id2 in recomendacoes[i + 1 :]:
                            rec_wine2_df = self.df[self.df["id"] == rec_id2]
                            if len(rec_wine2_df) == 0:
                                continue

                            sim = self._jaccard_similarity(
                                rec_wine1_df.iloc[0], rec_wine2_df.iloc[0]
                            )
                            internal_scores.append(sim)

                    # Diversidade = 1 - similaridade média interna
                    if internal_scores:
                        diversidade_interna.append(1 - np.mean(internal_scores))
            except Exception as e:
                print(f"Erro na amostra {idx}: {e}")
                erros += 1

        print(f"Avaliação concluída: {sucessos} sucessos, {erros} erros")

        # Calcular métricas agregadas
        resultados = {
            "jaccard_médio": np.mean(jaccard_scores) if jaccard_scores else 0,
            "jaccard_desvio": np.std(jaccard_scores) if jaccard_scores else 0,
            "cobertura": len(coverage) / len(self.df) if len(self.df) > 0 else 0,
            "diversidade_interna": (
                np.mean(diversidade_interna) if diversidade_interna else 0
            ),
            "amostras_avaliadas": sucessos,
            "total_amostras": len(test_samples),
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
            sucessos = 0

            for _, wine in amostra_teste.iterrows():
                try:
                    # Criar input de características
                    input_features = {}

                    # Incluir todas as características disponíveis
                    for col in (
                        self.text_columns
                        + self.categorical_columns
                        + self.ordinal_columns
                    ):
                        if pd.notna(wine[col]):
                            input_features[col] = wine[col]

                    # Obter recomendações
                    recomendacoes = self.recommender.recommend_wines(
                        input_features, top_n=5
                    )

                    if not recomendacoes:
                        continue

                    # Calcular jaccard médio
                    jacc_scores = []
                    for rec_id in recomendacoes:
                        rec_wine_df = self.df[self.df["id"] == rec_id]
                        if len(rec_wine_df) == 0:
                            continue

                        jacc = self._jaccard_similarity(wine, rec_wine_df.iloc[0])
                        jacc_scores.append(jacc)

                    if jacc_scores:
                        jaccard_scores.append(np.mean(jacc_scores))
                        sucessos += 1
                except Exception as e:
                    print(f"Erro na avaliação por tipo {tipo}: {e}")

            # Adicionar resultados para o tipo
            resultados_por_tipo[tipo] = {
                "jaccard_médio": np.mean(jaccard_scores) if jaccard_scores else 0,
                "número_amostras": sucessos,
                "total_amostras": len(amostra_teste),
            }

        return resultados_por_tipo
