# Recomendador de Vinhos da Evino

Esse é um projeto feito pela equipe Victor Santos e Tatiana Haddad e tem o intuito de ser uma ferramenta de recomendação de vinho para os usuários do site Evino. 
O objetivo é servir os usuários com opções similares a aquelas que eles gostam, que já compraram ou dos que ele tem pesquisado.

Iremos fazer isso através da execução de uma raspagem de dados no site da Evino (responsável, que fique claro) com acessos de 30 páginas a cada 20 minutos para poder não sobrecarregar os servidores deles e nem tomar um bloqueio por ip ou otra razão.

O modelo que criamos é um modelo de Recomendação com Base em Conteúdo que utiliza a Similaridade de Cosseno e a métrica utilizada foi Similaridade de Jaccard para podermos avaliar se o nosso modelo estava com overfit ou underfit. O modelo teve um resultado bem bom, considerando nossa inexperiência na aplicação e a jornada da utilização deste modelo e desta métrica foi de muito aprendizado! A seguir descrevemos melhor sobre o projeto

## Descrição do projeto:

O projeto tem três grandes blocos de desenvolvimento:

* Webscraping: Etapa onde realizamos a raspagem de dados utilizando Selenium e Beautiful Soup e onde geramos a base de dados que foi utilizada no projeto;
* Criação do Modelo de Machine Learning: Etapa onde fizemos toda a parte de Análise Exploratória dos Dados e a criação do recomendador em si;
* Criação do Frontend: Etapa onde disponibilizamos nosso modelo construído numa aplicação simples que indica os vinhos e onde mostra mais informações;

### Webscraping

Assim como todo o projeto, essa etapa foi desafiadora principalmente porque o site da Evino tem algumas proteções/barreiras que aumentam a dificuldade de realizar o webscraping no site deles. Fazem uso da repetição de tags e classes para conteúdos distintos, a renderização do site e das informações é feita em Java Script, fazem a utilização de pseudo-elementos que não vão para o DOM (html que pode ser acessado via requests, por exemplo), entre outras coisas.
Além disso, fizemos não somente a raspagem dos dados mas criamos duas tabelas de suporte no Supabase, que utiliza bancos de dados Postgres, para poder nos auxiliar e salvar os dados raw que estávamos coletando.

### Criação do Modelo de Machine Learning

Essa etapa foi de longe a mais interessante, principalmente pelo modelo que desenvolvemos que foi um aprendizado atrás do outro e uma ótima maneira de ser exposto. O modelo por si só é um pouco mais dificultoso de se aplicar principalmente porque não há tanta literatura disponível (não é impossível de achar, mas também não é fácil), ele é um modelo mais difícil de analisar métricas e expertise técnica certamente ajudaria demais no desenvolvimento.

### Criação do Frontend

No frontend utilizamos Streamlit para fazer as páginas, que são três: Pesquisa, Resultado e Detalhes. Respectivamente, a primeira página é a de pesquisa, onde o usuário fornece os inputs que quer pra recomendarmos os vinhos com base nesses inputs, ao submeter os inputs vamos para a página de Resultados e 5 vinhos são recomendados. Por último podemos clicar em um dos 5 vinhos e acessar mais informações sobre ele.

## Project Directory

./
├── .env
├── .gitignore
├── db.csv
├── LICENSE
├── README.md
├── requirements.txt
├── analysis/
│   ├── analyze_and_normalize_for_abt.ipynb
│   ├── beer_ml_model.ipynb 
│   ├── eda_tati.ipynb
│   ├── wine_recommender_eda_and_model.ipynb  
├── backend/ 
│   ├── main.py
│   ├── app/
│   ├── etl/
├── beer_data/
│   ├── beers.csv
│   ├── breweries.csv
├── evino_data/
│   ├── db.csv
├── frontend/
│   ├── _Home.py
│   ├── .streamlit/
│   │   ├── config.toml
│   ├── app/
│   ├── pages/
│   │   ├── _Details.py
│   │   ├── _Results.py
├── logs/
├── model/
│   ├── wine_recommender_model.pkl
├── wine_data/

O backend tem toda a parte de webscraping, comuicação com banco de dados e o modelo de recomendação;
O frontend tem toda a lógica das páginas do streamlit;
O modelo salvo em pickle está no ./model/, este modelo é o utilizado no frontend;
O notebook onde foi construído o modelo e onde tem a EDA é o wine_recommender_eda_and_model.ipynb;

## How to run the project

Para rodar a extração de dados do site da Evino

> python backend/main.py

Para rodar o frontend:

> streamlit run frontend/_Home.py

## Environment Variables

Para poder fazer uso do projeto deve-se utilizar as seguintes variáveis de ambiente:

SUPABASE_URL=''
SUPABASE_KEY=''

AWS_ACCESS_KEY_ID=''
AWS_SECRET_ACCESS_KEY=''
AWS_SESSION_TOKEN=''
AWS_REGION=''
RAW_BUCKET=''
IMAGES_RAW_BUCKET=''
OBJS_RAW_BUCKET=''

IMAGE_PATH=''
JSON_OBJS_PATH=''

## Prerequisites

Python - Version >= 3.9 to <= 3.11

## Environment Setup

1. Clone repo:
  > git clone https://github.com/VictorJSSantos/Modelo-de-recomendacao-de-vinhos.git

2. Create a virtual env: 
  > python -m venv venv

3. Activate virtual env: 
Windows:
  > venv\Scripts\activate
Linux:
  > source venv/bin/activate

4. Configure the Python interpreter in a virtual environment:
Ctrl + Shift + P to open the command palete.
  > Write Python: Select Interpreter - To choose the Python interpreter inside the venv folder.

5. Update pip to ensure proper installation of dependencies:
  > python -m pip install --upgrade pip

5. Install the dependencies:
  > pip install -r requirements.txt

