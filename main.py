import streamlit as st
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm
import plotly.graph_objects as go

# Função Objetivo
def funcao_objetivo(x):
    qtd_lote, z = x
    
    # Cálculo dos componentes de custo
    custo_estocar = (qtd_lote * custo_uni * taxa_m_custo_estoque) / 2
    custo_gestao_pedido = (custo_pedido * demanda_mensal) / (2 * qtd_lote)
    custo_es = z * np.sqrt(lt + std_lt**2 + std_d**2 + demanda_mensal**2) * custo_uni
    custo_faltar = fator_custo_falta * custo_uni * (1 - norm.cdf(z))
    
    return custo_estocar + custo_gestao_pedido + custo_es + custo_faltar

# Definindo as restrições
def restricao_qtd_lote_max(x):
    return maximo_lote - x[0]

def restricao_z_max(x):
    return maximo_z - x[1]

def restricao_qtd_lote_min(x):
    return x[0] - minimo_lote

def restricao_z_min(x):
    return x[1] - 1

def restricao_lote_multiplo(x):
    return x[0] % lote_multiplo

# Streamlit: Inputs do Usuário
st.title("Otimização de Política")

# Segmentando parâmetros por nome
with st.expander("Parâmetros de Custo"):
    col1, col2 = st.columns(2)
    with col1:
        custo_pedido = st.number_input("Custo por Pedido", value=40)
        taxa_m_custo_estoque = st.number_input("Taxa de Custo de Estoque", format="%.3f", value=0.084)
        custo_capital = st.number_input("Custo de Capital", format="%.3f", value=0.062)
        fator_custo_falta = st.number_input("Fator de Custo de Falta", value=500)

    with col2:
        custo_uni = st.number_input("Custo por Unidade ", value=15)
        demanda_mensal = st.number_input("Demanda Mensal", value=20)
        lt = st.number_input("Lead Time (lt)", value=180)
        std_d = st.number_input("Desvio Padrão da Demanda ", value=3)
        std_lt = st.number_input("Desvio Padrão do Lead Time ", value=10)

# Expansor para input das variáveis iniciais
with st.expander("Parâmetros Iniciais"):
    col5, col6 = st.columns(2)
    with col5:
        qtd_lote_inicial = st.number_input("Quantidade Inicial do Lote", value=140)
        z_inicial = st.number_input("Nível de Serviço Inicial (z)", value=1.95)

# Restrições
with st.expander("Restrições"):
    col3, col4 = st.columns(2)
    with col3:
        maximo_lote = st.number_input("Máximo Lote", value=240)
        maximo_z = st.number_input("Máximo Z (Nível de Serviço)", value=3)

    with col4:
        minimo_lote = st.number_input("Mínimo Lote", value=100)
        lote_multiplo = st.number_input("Múltiplo de Lote", value=20)

# Adicionando o botão de otimização
if st.button('Iniciar Otimização'):
    # Otimização
    z_values = np.linspace(0.1, maximo_z, 50)
    lote_values = np.linspace(minimo_lote, maximo_lote, 50)

    Z, Lote = np.meshgrid(z_values, lote_values)
    Custo = np.array([funcao_objetivo([lote, z]) for lote, z in zip(Lote.ravel(), Z.ravel())])
    Custo = Custo.reshape(Z.shape)

    # Função de otimização
    x0 = [qtd_lote_inicial, z_inicial]  # Valores iniciais para qtd_lote e z

    restricoes = [
        {'type': 'ineq', 'fun': restricao_qtd_lote_max},
        {'type': 'ineq', 'fun': restricao_z_max},
        {'type': 'ineq', 'fun': restricao_qtd_lote_min},
        {'type': 'ineq', 'fun': restricao_z_min},
        #{'type': 'eq', 'fun': restricao_lote_multiplo}
    ]

    # Executando a otimização
    resultado = minimize(funcao_objetivo, x0, method='trust-constr', constraints=restricoes)

    # Resultados da otimização
    qtd_lote_otimo = resultado.x[0]
    z_otimo = resultado.x[1]
    custo_minimo = resultado.fun

    # Cálculo do custo inicial
    custo_inicial = funcao_objetivo(x0)

    # Diferença de custo em valor e percentual
    diferenca_valor = custo_inicial - custo_minimo
    diferenca_percentual = (diferenca_valor / custo_inicial) * 100

    st.markdown("### **Resultados da Otimização**")

    # Exibindo os resultados lado a lado
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### **Ponto Inicial**")
        st.markdown(f"**Quantidade de lote inicial**: **{qtd_lote_inicial:.2f}**")
        st.markdown(f"**Nível de serviço (z) inicial**: **{z_inicial:.2f}**")
        st.markdown(f"**Custo inicial**: **{custo_inicial:.2f}**")

    with col2:
        st.markdown("#### **Ponto Otimizado**")
        st.markdown(f"**Quantidade de lote ótima**: **{qtd_lote_otimo:.2f}**")
        st.markdown(f"**Nível de serviço (z) ótimo**: **{z_otimo:.2f}**")
        st.markdown(f"**Custo mínimo**: **{custo_minimo:.2f}**")

    st.markdown("#### **Diferença de Custo**")
    st.markdown(f"**Diferença de custo (valor)**: **{diferenca_valor:.2f}**")
    st.markdown(f"**Diferença de custo (percentual)**: **{diferenca_percentual:.2f}%**")

    # Gráfico 3D com ponto ótimo e ponto inicial
    fig = go.Figure(data=[go.Surface(z=Custo, x=Lote, y=Z, colorscale='Viridis')])

    # Adicionando o ponto ótimo ao gráfico
    fig.add_trace(go.Scatter3d(
        x=[qtd_lote_otimo],
        y=[z_otimo],
        z=[custo_minimo],
        mode='markers',
        marker=dict(size=8, color='red', symbol='circle'),
        name="Ponto Ótimo"
    ))

    # Adicionando o ponto inicial ao gráfico
    fig.add_trace(go.Scatter3d(
        x=[qtd_lote_inicial],
        y=[z_inicial],
        z=[custo_inicial],
        mode='markers',
        marker=dict(size=8, color='blue', symbol='circle'),
        name="Ponto Inicial"
    ))

    fig.update_layout(
        title="Função Objetivo - Custo em função de z e qtd_lote",
        scene=dict(
            xaxis_title="Qtd Lote",
            yaxis_title="z (Nível de Serviço)",
            zaxis_title="Custo Total"
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    # Exibindo o gráfico
    st.plotly_chart(fig)
