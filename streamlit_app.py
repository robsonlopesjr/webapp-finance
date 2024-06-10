import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from itertools import islice


st.set_page_config(page_title="Ações Dashboard", page_icon=":money_with_wings:", layout="wide")


def batched(iterable, n_cols):
    """
    Gera lotes de um iterável, cada lote contendo até n_cols elementos.

    Parâmetros:
    iterable (iterable): A sequência de entrada que será dividida em lotes.
    n_cols (int): O número máximo de elementos em cada lote.

    Retorno:
    generator: Um gerador que produz tuplas de elementos do iterável, cada uma contendo até n_cols elementos.

    Exemplo:
    >>> list(batched('ABCDEFG', 3))
    [('A', 'B', 'C'), ('D', 'E', 'F'), ('G',)]
    """
    if n_cols < 1:
        raise ValueError("n must be at least one")

    it = iter(iterable)

    while batch := tuple(islice(it, n_cols)):
        yield batch


def plot_sparkline(data):
    """
    Cria um gráfico de linha (sparkline) para os dados fornecidos.

    Parâmetros:
    data (list ou pd.Series): Sequência de dados numéricos a serem plotados.

    Retorno:
    plotly.graph_objects.Figure: Figura Plotly contendo o sparkline.
    """
    fig_spark = go.Figure(
        data=go.Scatter(
            y=data,
            mode='lines',
            fill='tozeroy',
            line=dict(color='red'),
            fillcolor='pink'
        )
    )

    fig_spark.update_traces(hovertemplate="Preço: R$ %{y:.2f}")
    fig_spark.update_xaxes(visible=False, fixedrange=True)
    fig_spark.update_yaxes(visible=False, fixedrange=True)
    fig_spark.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        height=50,
        margin=dict(t=10, l=0, b=0, r=0, pad=0),
    )

    return fig_spark


def display_watchlist_card(ticker, symbol_name, last_price, change_pct, open):
    """
    Exibe um cartão de observação com informações sobre um ativo.

    Parâmetros:
    ticker (str): O símbolo do ticker do ativo.
    symbol_name (str): O nome do símbolo do ativo.
    last_price (float): O preço atual do ativo.
    change_pct (float): A variação percentual do preço do ativo.
    open (list ou pd.Series): Os preços de abertura do ativo.

    Retorno:
    None
    """
    with st.container(border=True):
        st.html('<span class="watchlist_card"></span>')

        top_left, top_right = st.columns([2, 1])
        bottom_left, bottom_right = st.columns([1, 1])

        with top_left:
            st.html('<span class="watchlist_symbol_name"></span>')
            st.markdown(f"{symbol_name}")

        with top_right:
            st.html('<span class="watchlist_ticker"></span>')
            st.markdown(f"{ticker}")
            negative_gradient = float(change_pct) < 0

            st.markdown(
                f""":{'red'
                if negative_gradient
                else 'green'
                }[{'▼' if negative_gradient else '▲'}
                {round(change_pct, 2)} %]"""
            )

        with bottom_left:
            with st.container():
                st.html('<span class="watchlist_price_label"></span>')
                st.markdown("Valor Atual")

            with st.container():
                st.html('<span class="watchlist_price_value"></span>')
                st.markdown(f"R$ {last_price:.2f}")

        with bottom_right:
            st.html('<span class="watchlist_bottom_right"></span>')
            fig_spark = plot_sparkline(open)
            st.plotly_chart(
                fig_spark,
                config=dict(displayModeBar=False),
                use_container_width=True
            )


def display_watchlist(ticker_df):
    """
    Exibe uma lista de observação (watchlist) de ativos em um layout de grade.

    Parâmetros:
    ticker_df (pd.DataFrame): DataFrame contendo informações dos ativos.
        Espera-se que o DataFrame contenha as colunas 'ticker', 'last_price', 'change_pct' e 'Open'.

    Retorno:
    None
    """
    n_cols = 4

    for row in batched(ticker_df.itertuples(), n_cols):
        cols = st.columns(n_cols)

        for col, ticker in zip(cols, row):
            if ticker:
                with col:
                    display_watchlist_card(
                        ticker.ticker,
                        ticker.ticker,
                        ticker.last_price,
                        ticker.change_pct,
                        ticker.Open
                    )


def display_overview(ticker_df):
    """
    Formata e exibe um DataFrame com estilos personalizados.

    Parâmetros:
    ticker_df (pd.DataFrame): DataFrame contendo informações dos tickers.

    Retorno:
    None

    Funções internas:
    - format_currency(val): Formata um valor numérico como moeda.
    - format_percentage(val): Formata um valor numérico como porcentagem.
    - apply_odd_row_class(row): Aplica uma cor de fundo diferente para linhas ímpares.
    - format_change(val): Aplica cores diferentes para valores de variação positiva e negativa.
    """
    def format_currency(val):
        """
        Formata um valor numérico como moeda.

        Parâmetros:
        val (float): Valor numérico a ser formatado.

        Retorno:
        str: Valor formatado como moeda.
        """
        return "$ {:,.2f}".format(val)

    def format_percentage(val):
        """
        Formata um valor numérico como porcentagem.

        Parâmetros:
        val (float): Valor numérico a ser formatado.

        Retorno:
        str: Valor formatado como porcentagem.
        """
        return "{:,.2f} %".format(val)

    def apply_odd_row_class(row):
        """
        Aplica uma cor de fundo diferente para linhas ímpares.

        Parâmetros:
        row (pd.Series): Linha do DataFrame.

        Retorno:
        list: Lista de estilos aplicados à linha.
        """
        return [
            "background-color: #f8f8f8" if row.name % 2 != 0 else "" for _ in row
        ]

    def format_change(val):
        """
        Aplica cores diferentes para valores de variação positiva e negativa.

        Parâmetros:
        val (float): Valor de variação.

        Retorno:
        str: Estilo de cor aplicado ao valor.
        """
        return "color: red;" if (val < 0) else "color: green;"

    styled_df = ticker_df.style.format(
        {
            "last_price": format_currency,
            "change_pct": format_percentage
        }
    ).apply(
        apply_odd_row_class, axis=1
    ).map(
        format_change, subset=["change_pct"]
    )

    st.dataframe(
        styled_df,
        column_order=[column for column in list(ticker_df.columns)],
        column_config={
            "Open": st.column_config.AreaChartColumn(
                "Últimos 12 meses",
                width="large",
                help="Preço de abertura nos últimos 12 meses"
            )
        },
        hide_index=True,
        height=250)


@st.cache_data
def transform_data(ticker_df, history_dfs):
    """
    Transforma os dados em DataFrames, convertendo colunas específicas para formatos apropriados (datetime e numérico),
    e adiciona uma nova coluna ao ticker_df.

    Parâmetros:
    ticker_df (pd.DataFrame): DataFrame contendo informações dos tickers.
    history_dfs (dict): Dicionário de DataFrames contendo o histórico de preços dos tickers.

    Retorno:
    tuple: DataFrames transformados (ticker_df, history_dfs).
    """
    ticker_df["last_trade_time"] = pd.to_datetime(
        ticker_df["last_trade_time"],
        dayfirst=True
    )

    for col in ["last_price", "previous_day_price", "change", "change_pct"]:
        ticker_df[col] = pd.to_numeric(
            ticker_df[col], "coerce"
        )

    for ticker in list(ticker_df["ticker"]):
        # history_dfs[ticker]["date"] = pd.to_datetime(
        #     history_dfs[ticker]["date"],
        #     dayfirst=True
        # )

        for col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]:
            history_dfs[ticker][col] = pd.to_numeric(
                history_dfs[ticker][col]
            )

    ticker_to_open = [
        list(history_dfs[t]["Open"])
        for t in list(ticker_df["ticker"])
    ]
    ticker_df["Open"] = ticker_to_open

    return ticker_df, history_dfs


@st.experimental_fragment
def display_symbol_history(ticker_df, history_dfs):
    """
    Exibe o histórico de um símbolo selecionado e indicadores chave em um layout de colunas.

    Parâmetros:
    ticker_df (pd.DataFrame): DataFrame contendo informações dos ativos.
    history_dfs (dict): Dicionário contendo DataFrames de histórico dos ativos, onde as chaves são os tickers.

    Retorno:
    None
    """
    left_widget, right_widget, _ = st.columns([1, 1, 1.5])

    selected_ticker = left_widget.selectbox(
        ":newspaper: Ativos",
        list(history_dfs.keys())
    )

    selected_period = right_widget.selectbox(
        ":clock4: Período",
        ("Semanal", "Mensal", "Trimestral", "Anual"),
        2
    )

    history_dfs = history_dfs[selected_ticker]

    mapping_period = {
        "Semanal": 7,
        "Mensal": 31,
        "Trimestral": 90,
        "Anual": 365
    }

    today = datetime.today().date()
    delay_days = mapping_period[selected_period]
    history_dfs = history_dfs[
        (today - pd.Timedelta(delay_days, unit="d")):today
    ]

    f_candle = plot_candlestick(history_dfs)

    left_chart, right_indicator = st.columns([1.5, 1])

    with left_chart:
        st.plotly_chart(f_candle, use_container_width=True)

    with right_indicator:
        left_column, right_column = st.columns(2)

        with left_column:
            st.html('<span class="low_indicator"></span>')
            st.metric(
                "Menor volume negociado",
                f'{history_dfs["Volume"].min():,}'
            )

            st.metric(
                "Menor preço de fechamento",
                f'{history_dfs["Close"].min():,}'
            )

        with right_column:
            st.html('<span class="high_indicator"></span>')
            st.metric(
                "Maior volume negociado",
                f'{history_dfs["Volume"].max():,}'
            )

            st.metric(
                "Maior preço de fechamento",
                f'{history_dfs["Close"].max():,}'
            )

        with st.container():
            st.html('<span class="bottom_indicator"></span>')
            st.metric(
                "Média de volume negociado",
                f'{history_dfs["Volume"].mean():,}'
            )

            st.metric(
                "Atual Market Cap",
                "{:,} $".format(
                    ticker_df[ticker_df["ticker"] == selected_ticker][
                        "marketcap"
                    ].values[0]
                ),
            )


def plot_candlestick(history_dfs):
    """
    Cria um gráfico de candlestick com um gráfico de barras para o volume negociado.

    Parâmetros:
    history_dfs (pd.DataFrame): DataFrame contendo os dados históricos de preços de ações.
        Espera-se que o DataFrame contenha as colunas 'Open', 'High', 'Low', 'Close' e 'Volume'.

    Retorno:
    f_candle (plotly.graph_objs._figure.Figure): Objeto Figure do Plotly contendo o gráfico de candlestick.
    """
    f_candle = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1
    )

    f_candle.add_trace(
        go.Candlestick(
            x=history_dfs.index,
            open=history_dfs["Open"],
            high=history_dfs["High"],
            low=history_dfs["Low"],
            close=history_dfs["Close"],
            name="Reais",
        ),
        row=1,
        col=1
    )

    f_candle.add_trace(
        go.Bar(
            x=history_dfs.index,
            y=history_dfs["Volume"],
            name="Volume Negociado"
        ),
        row=2,
        col=1
    )

    f_candle.update_layout(
        title="Tendências de preços de ações",
        showlegend=True,
        xaxis_rangeslider_visible=False,
        yaxis1=dict(title="OHLC"),
        yaxis2=dict(title="Volume"),
        hovermode="x"
    )

    f_candle.update_layout(
        title_font_family="Open Sans",
        title_font_color="#174C4F",
        title_font_size=32,
        font_size=16,
        margin=dict(l=80, r=80, t=100, b=80, pad=0),
        height=500,
    )

    f_candle.update_xaxes(title_text="Date", row=2, col=1)
    f_candle.update_traces(selector=dict(name="Reais"), showlegend=True)

    return f_candle


@st.cache_data
def download_data(tickers, start_date, end_date=datetime.now(), period="1d"):
    """
    Baixa dados históricos de preços para uma lista de tickers e calcula métricas financeiras.

    Parâmetros:
    tickers (list): Lista de tickers para os quais os dados serão baixados.
    start_date (str): Data de início no formato 'YYYY-MM-DD'.
    end_date (str, opcional): Data de término no formato 'YYYY-MM-DD'. Padrão é a data e hora atual.
    period (str, opcional): Frequência dos dados. Padrão é '1d' (diário).

    Retorno:
    tuple: Contém um DataFrame com os dados dos tickers e um dicionário com os dados históricos para cada ticker.
    """
    history_dfs = {}
    ticker_data = []
    for ticker in tickers:
        data = yf.download(ticker, start=start_date, end=end_date, period=period)
        history_dfs[ticker] = data
        last_trade_time = data.index[-1]
        last_price = data['Close'].iloc[-1]
        # calcula o preço de fechamento do dia anterior
        previous_day_price = data['Close'].iloc[-2] if len(data) > 1 else last_price
        change = last_price - previous_day_price
        change_pct = (change / previous_day_price) * 100

        marketcap = yf.Ticker(ticker).info
        marketcap = marketcap['marketCap']

        ticker_data.append({
            'ticker': ticker,
            'last_trade_time': last_trade_time,
            'last_price': last_price,
            'previous_day_price': previous_day_price,
            'change': change,
            'change_pct': change_pct,
            'marketcap': marketcap,
        })

    ticker_df = pd.DataFrame(ticker_data)

    return ticker_df, history_dfs


st.title("Ações - Dashboard")

# Dicionário de tickers
dict_tickers = {
    'ITAUSA': 'ITSA4.SA',
    'BANCO DO BRASIL': 'BBAS3.SA',
    'BANCO BRADESCO': 'BBDC4.SA',
    'COPASA': 'CSMG3.SA',
    'SANEPAR': 'SAPR11.SA',
    'TAESA': 'TAEE11.SA',
    'CEMIG': 'CMIG4.SA',
    'BB SEGURIDADE': 'BBSE3.SA',
    'PORTO SEGURO': 'PSSA3.SA',
    'PETROBRAS': 'PETR4.SA'
}

ticker_df, history_dfs = download_data(list(dict_tickers.values()), start_date='2024-01-01', end_date=datetime.now())
ticker_df, history_dfs = transform_data(ticker_df, history_dfs)

display_watchlist(ticker_df)

st.divider()

display_symbol_history(ticker_df, history_dfs)
display_overview(ticker_df)
