import joblib
import pandas as pd
import numpy as np
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, LabelEncoder, OrdinalEncoder
from sklearn.model_selection import KFold
import warnings


warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")


class WineRecommender:
    def __init__(self, dataframe):
        self.df = dataframe
        self.prepare_features()

    def prepare_features(self):
        """Definir aqui quais colunas serão usadas para definir a similaridade"""
        self.text_columns = [
            "product_name",
            "color_description",
            "scent_description",
            "taste_description",
            "harmonizes_with",
            "technical_sheet_grapes",
            "technical_sheet_region",
            "technical_sheet_wine_type",
            "technical_sheet_country",
        ]

        self.categoric_columns = [
            "technical_sheet_wine_type",
            "technical_sheet_country",
        ]

        self.ordinal_columns = [
            "fruit_tasting",
            "sugar_tasting",
            "acidity_tasting",
            "tannin_tasting",
        ]

        # Verificar se todas as colunas existem no DataFrame
        for column in self.text_columns + self.categoric_columns + self.ordinal_columns:
            if column not in self.df.columns:
                print(f"Aviso: Coluna {column} não existe no DataFrame e será ignorada")

        # Filtrar apenas colunas que existem no DataFrame
        self.text_columns = [col for col in self.text_columns if col in self.df.columns]
        self.categoric_columns = [
            col for col in self.categoric_columns if col in self.df.columns
        ]
        self.ordinal_columns = [
            col for col in self.ordinal_columns if col in self.df.columns
        ]

        # Calcular o valor médio para cada variável ordinal
        self.ordinal_means = {}
        for column in self.ordinal_columns:
            self.df[column] = pd.to_numeric(self.df[column], errors="coerce")
            self.ordinal_means[column] = self.df[column].mean()

        # Ajuste do OrdinalEncoder
        self.ordinal_encoders = {}
        for column in self.ordinal_columns:
            le = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            # Garantir que os dados são 2D para o encode
            self.df[column] = le.fit_transform(
                self.df[[column]].fillna(self.ordinal_means[column])
            )
            self.ordinal_encoders[column] = le

        # Criando o LabelEncoder para as variáveis categóricas nominais
        self.label_encoders = {}
        for column in self.categoric_columns:
            le = LabelEncoder()
            self.df[column] = le.fit_transform(self.df[column].fillna("Unknown"))
            self.label_encoders[column] = le

        # Lidamos com nulos e realizamos um join em todas as características de texto em uma coluna.
        self.df["combined_text_features"] = (
            self.df[self.text_columns]
            .fillna("")
            .apply(lambda x: " ".join(x.astype(str)), axis=1)
        )

        # Realizamos uma Vetorização TF-IDF
        self.vectorizer = TfidfVectorizer(
            min_df=2,  # Ignora termos muito raros
            max_df=0.8,  # Ignora termos muito frequentes
            ngram_range=(1, 2),  # Unigramas e bigramas
            stop_words=list(
                stopwords_spacy
            ),  # Podemos adicionar uma lista personalizada depois
        )

        self.text_matrix = self.vectorizer.fit_transform(
            self.df["combined_text_features"]
        )

        # Adicionando pesos para cada tipo de feature
        self.feature_weights = {
            "text": 0.4,  # Peso para features textuais
            "ordinal": 0.4,  # Peso para features ordinais
            "categoric": 0.2,  # Peso para features categóricas
        }

        # Normalização de características numéricas - corrigindo para usar o scaler corretamente
        self.numeric_scaler = MinMaxScaler()
        if len(self.ordinal_columns) > 0:
            # Preencher NA com a média antes de escalar
            self.df[self.ordinal_columns] = self.df[self.ordinal_columns].fillna(
                self.df[self.ordinal_columns].mean()
            )
            self.numeric_features_normalized = self.numeric_scaler.fit_transform(
                self.df[self.ordinal_columns]
            )
        else:
            self.numeric_features_normalized = np.array([])

    def encode_input(self, input_features):
        """
        Codifica as variáveis de entrada usando os codificadores definidos no modelo.
        """
        encoded_features = {}

        # Codificar variáveis categóricas
        for col, encoder in self.label_encoders.items():
            if col in input_features:
                try:
                    encoded_features[col] = encoder.transform(
                        [str(input_features[col])]
                    )[0]
                except:
                    print(f"Erro ao codificar {col}. Usando valor padrão.")
                    encoded_features[col] = 0

        # Codificar variáveis ordinais
        for col, encoder in self.ordinal_encoders.items():
            if col in input_features:
                try:
                    value = float(input_features[col])
                    encoded_features[col] = encoder.transform([[value]])[0][0]
                except:
                    print(f"Erro ao codificar {col}. Usando valor médio.")
                    encoded_features[col] = self.ordinal_means[col]

        return encoded_features

    def recommend_wines(
        self, input_features, top_n=5, diversity_factor=0.5, random_state=None
    ):
        """
        Versão final corrigida e otimizada

        Args:
            input_features (dict): Dicionário com features do vinho de referência
            top_n (int): Quantidade de recomendações
            diversity_factor (float): 0-1 (0=sem diversificação, 1=máxima diversificação)
            random_state (int): Seed para reprodutibilidade
        """
        # 1. Pré-processamento das features de entrada
        input_features = {
            k: v
            for k, v in input_features.items()
            if k in self.text_columns + self.ordinal_columns + self.categoric_columns
        }

        # 2. Cálculo das similaridades individuais
        similarities = []

        # Similaridade textual
        if self.text_columns and self.feature_weights["text"] > 0:
            text_input = {
                k: v
                for k, v in input_features.items()
                if k in self.text_columns and v is not None
            }
            if text_input:
                input_text = " ".join(str(v) for v in text_input.values())
                input_vector = self.vectorizer.transform([input_text])
                text_sim = cosine_similarity(input_vector, self.text_matrix)[0]
                text_sim = (text_sim - text_sim.min()) / (
                    text_sim.max() - text_sim.min() + 1e-10
                )
                similarities.append(text_sim * self.feature_weights["text"])

        # Similaridade ordinal
        if self.ordinal_columns and self.feature_weights["ordinal"] > 0:
            ordinal_input = {
                k: v
                for k, v in input_features.items()
                if k in self.ordinal_columns and v is not None
            }
            if ordinal_input:
                input_ordinal = []
                for col in self.ordinal_columns:
                    if col in ordinal_input:
                        try:
                            value = float(ordinal_input[col])
                            encoded = self.ordinal_encoders[col].transform([[value]])[
                                0
                            ][0]
                            input_ordinal.append(encoded)
                        except:
                            input_ordinal.append(self.ordinal_means[col])
                    else:
                        input_ordinal.append(self.ordinal_means[col])

                input_ordinal = np.array(input_ordinal).reshape(1, -1)
                input_normalized = self.numeric_scaler.transform(input_ordinal)
                distances = np.linalg.norm(
                    self.numeric_features_normalized - input_normalized, axis=1
                )
                ordinal_sim = 1 / (1 + distances)
                ordinal_sim = (ordinal_sim - ordinal_sim.min()) / (
                    ordinal_sim.max() - ordinal_sim.min() + 1e-10
                )
                similarities.append(ordinal_sim * self.feature_weights["ordinal"])

        # 3. Combinação das similaridades
        if not similarities:
            return []

        final_similarity = np.sum(similarities, axis=0)

        # 4. Seleção dos candidatos iniciais (top 3*top_n mais similares)

        # candidate_size = min(3*top_n, len(self.df))
        candidate_size = min(5 * top_n, len(self.df))  # Antes era 3*top_n
        ############################################
        top_candidates_idx = final_similarity.argsort()[-candidate_size:][::-1]
        candidates = self.df.iloc[top_candidates_idx].copy()
        candidates["similarity"] = final_similarity[top_candidates_idx]

        # 5. Diversificação (ou não)
        if diversity_factor <= 0:
            return candidates.head(top_n)["id"].tolist()

        return self._safe_diversify(
            candidates=candidates,
            text_matrix=self.text_matrix[top_candidates_idx],
            similarity_scores=candidates["similarity"].values,
            top_n=top_n,
            lambda_param=diversity_factor,
            random_state=random_state,
        )

    def optimize_diversity(self, target_jaccard=0.4, target_coverage=0.5):
        """
        Auto-ajusta os parâmetros para atingir metas de diversidade

        Args:
            target_jaccard (float): Jaccard médio desejado
            target_coverage (float): Porcentagem do catálogo a ser recomendado
        """
        best_params = {
            "text_weight": self.feature_weights["text"],
            "ordinal_weight": self.feature_weights["ordinal"],
            "diversity_factor": 0.5,
        }
        best_score = float("inf")

        # Espaço de busca de parâmetros
        text_weights = np.linspace(0.3, 0.6, 4)
        diversity_factors = np.linspace(0.3, 0.8, 6)

        for text_w in text_weights:
            for div_factor in diversity_factors:
                self.feature_weights = {
                    "text": text_w,
                    "ordinal": 0.6 - text_w,  # Mantém soma 0.6
                    "categoric": 0.4,
                }

                metrics = self.evaluate_diversity_metrics()

                # Função de perda combinada
                score = (abs(metrics["jaccard_médio"] - target_jaccard)) + (
                    abs(metrics["cobertura"] - target_coverage)
                )

                if score < best_score:
                    best_score = score
                    best_params = {
                        "text_weight": text_w,
                        "ordinal_weight": 0.6 - text_w,
                        "diversity_factor": div_factor,
                    }

        # Aplica os melhores parâmetros
        self.feature_weights = {
            "text": best_params["text_weight"],
            "ordinal": best_params["ordinal_weight"],
            "categoric": 0.4,
        }
        self.optimal_diversity_factor = best_params["diversity_factor"]

        return best_params

    def _safe_diversify(
        self,
        candidates,
        text_matrix,
        similarity_scores,
        top_n,
        lambda_param,
        random_state=None,
    ):
        """
        Versão segura do algoritmo de diversificação
        """
        if random_state is not None:
            np.random.seed(random_state)

        selected = []
        remaining_indices = list(range(len(candidates)))

        # Primeiro item: o mais similar
        first_idx = np.argmax(similarity_scores)
        selected.append(remaining_indices.pop(first_idx))

        while len(selected) < top_n and remaining_indices:
            # Calcular similaridade com os já selecionados
            sim_matrix = cosine_similarity(
                text_matrix[remaining_indices], text_matrix[selected]
            )

            # Se nenhum item selecionado ainda, usar zeros
            if not selected:
                max_sim = np.zeros(len(remaining_indices))
            else:
                max_sim = np.max(sim_matrix, axis=1)

            # Calcular scores MMR
            # mmr_scores = (1-lambda_param) * similarity_scores[remaining_indices] - lambda_param * max_sim
            mmr_scores = (1.2 - lambda_param) * similarity_scores[remaining_indices] - (
                0.8 + lambda_param
            ) * max_sim

            # Selecionar o próximo item
            next_idx = np.argmax(mmr_scores)
            selected.append(remaining_indices.pop(next_idx))

        # Retornar os IDs dos itens selecionados
        return candidates.iloc[selected]["id"].tolist()

    def analyze_recommendation_behavior(self, sample_size=10):
        """Analisa padrões nas recomendações"""
        analysis = {}

        # 1. Distribuição de similaridades
        sample = self.df.sample(min(sample_size, len(self.df)))
        all_sims = []

        for _, row in sample.iterrows():
            input_features = {
                "product_name": row["product_name"],
                "technical_sheet_country": row["technical_sheet_country"],
                "fruit_tasting": row["fruit_tasting"],
            }
            recs = self.recommend_wines(input_features, top_n=5, diversity_factor=0)
            sims = cosine_similarity(
                self.text_matrix[row.name],
                self.text_matrix[self.df["id"].isin(recs).values],
            )
            all_sims.extend(sims.flatten())

        analysis["similarity_distribution"] = {
            "mean": np.mean(all_sims),
            "std": np.std(all_sims),
            "min": np.min(all_sims),
            "max": np.max(all_sims),
        }

        # 2. Sobreposição entre recomendações
        overlaps = []
        for i in range(sample_size):
            for j in range(i + 1, sample_size):
                recs1 = set(self.recommend_wines(sample.iloc[i].to_dict(), 5, 0))
                recs2 = set(self.recommend_wines(sample.iloc[j].to_dict(), 5, 0))
                overlap = (
                    len(recs1 & recs2) / len(recs1 | recs2) if (recs1 | recs2) else 0
                )
                overlaps.append(overlap)

        analysis["recommendation_overlap"] = {
            "mean": np.mean(overlaps),
            "max": np.max(overlaps),
        }

        return analysis

    def salvar_modelo(self, caminho="../model/wine_recommender_model.pkl"):
        """Salva o modelo treinado em um arquivo."""
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio)

        try:
            joblib.dump(self, caminho)
            print(f"Modelo salvo com sucesso em: {caminho}")
            return caminho
        except Exception as e:
            print(f"Erro ao salvar o modelo: {e}")
            raise

    @classmethod
    def carregar_modelo(cls, caminho="model/wine_recommender_model.pkl"):
        """Carrega um modelo salvo."""
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo de modelo não encontrado: {caminho}")

        try:
            modelo_carregado = joblib.load(caminho)
            print(f"Modelo carregado com sucesso de: {caminho}")
            return modelo_carregado
        except Exception as e:
            print(f"Erro ao carregar o modelo: {e}")
            raise
