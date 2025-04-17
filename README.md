# 💰 CryptoWallet - Gerenciador de Carteira de Criptomoedas

Aplicação web desenvolvida com **Flask** para gerenciamento de uma carteira de criptoativos em tempo real. Integra dados da **Binance**, gráficos dinâmicos, análises técnicas, alertas via Telegram e muito mais.

---

## 🚀 Funcionalidades

- 📈 **Dashboard interativo** com lucro/prejuízo, variação e preço médio.
- 🔒 **Login com autenticação Google**.
- 🧮 **Cálculo automático de preço atual, variação e lucro** (dados da API da Binance).
- 📊 **Gráficos de evolução da carteira** por data e por ativo.
- 🌚 **Modo escuro (dark mode)**.
- 📅 Página com **calendário econômico dos EUA** (via FED).
- 💥 Monitoramento de **grandes movimentações de mercado**.
- 🧠 Página de **análise de mercado futuro** com:
  - Sinais de compra/venda
  - RSI, Fibonacci, suportes/resistências
  - Risco controlado (máx 1%)
- 📲 Integração com **Telegram** para alertas de movimentações e oportunidades.

---

## 🛠 Tecnologias Utilizadas

- **Python + Flask**
- **HTML/CSS + JavaScript (AJAX, gráficos interativos)**
- **Bootstrap** com tema estilo Binance
- **API Binance (Spot e Futures)**
- **Autenticação Google OAuth2**
- **Telegram Bot API**
- **Pandas / Plotly / Matplotlib** para dados e gráficos

---

## 📦 Instalação

1. Clone o repositório:

```bash
git clone git@github.com:seu-usuario/seu-repo.git
cd seu-repo


2. Crie e ative um ambiente virtual:
python3 -m venv venv
source venv/bin/activate

3. Instale as Dependências
pip install -r requirements.txt
Crie um arquivo .env com base no .env.example:

4. Crie um arquivo .env com base no .env.example:
cp .env.example .env

5. Rode o App
flask run




