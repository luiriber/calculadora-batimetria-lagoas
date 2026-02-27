import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RectBivariateSpline

# Configuração da página para ocupar mais espaço na tela
st.set_page_config(page_title="Calculadora Batimétrica", layout="wide")

# Função auxiliar para formatar números no padrão brasileiro
def format_br(num, decimals=2):
    return f"{num:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Função para ler as distâncias digitadas
def parse_distancias(texto):
    t = texto.replace(';', ' ').replace(',', '.')
    return np.array([float(i) for i in t.split()])

# ==========================================
# INTERFACE DE USUÁRIO (Barra Lateral e Principal)
# ==========================================
st.title("Calculadora Batimétrica de Lagoas")
st.markdown("Preencha as dimensões totais da lagoa, as distâncias de medição e cole a matriz de lodo.")

# Criando colunas para organizar os inputs
col1, col2, col3, col4 = st.columns(4)

with col1:
    prof_max = st.number_input('Profundidade Máx. (m):', value=1.50, step=0.1)
with col2:
    comprimento_lagoa = st.number_input('Comprimento Total (m):', value=75.0, step=1.0)
with col3:
    largura_lagoa = st.number_input('Largura Total (m):', value=30.0, step=1.0)
with col4:
    sst = st.number_input('Concentração SST (%):', value=8.0, step=0.1)

st.markdown("---")
st.markdown("#### Coordenadas da Malha Medida")
st.caption("Separe os números por espaço ou vírgula. A quantidade de números deve bater com as linhas/colunas da matriz.")

col_x, col_y = st.columns(2)
with col_x:
    distancias_x_input = st.text_input('Distâncias X (Comprimento) [m]:', value="10 20 30 40 50 60 70 80")
with col_y:
    distancias_y_input = st.text_input('Distâncias Y (Largura) [m]:', value="10 20 30")

matriz_input = st.text_area(
    'Dados do Lodo (Matriz copiada do Excel):',
    value="0.90\t0.50\t0.15\t0.20\t0.40\t0.40\t0.80\t0.85\n0.95\t0.70\t0.25\t0.15\t0.10\t0.10\t0.40\t0.90\n1.00\t1.00\t0.60\t0.25\t0.20\t0.40\t0.70\t0.70",
    height=150
)

# ==========================================
# PROCESSAMENTO DOS DADOS
# ==========================================
if st.button("Gerar Relatório e Gráficos", type="primary"):
    try:
        # Processa a matriz Z
        texto_bruto = matriz_input.strip().replace(',', '.')
        linhas = texto_bruto.split('\n')
        dados_z = []
        for linha in linhas:
            if linha.strip():
                valores = [float(v) for v in linha.split()]
                dados_z.append(valores)

        z = np.array(dados_z)
        linhas_qtd, colunas_qtd = z.shape

        # Processa as distâncias X e Y
        x = parse_distancias(distancias_x_input)
        y = parse_distancias(distancias_y_input)

        # Validações de segurança
        erros = []
        if len(x) != colunas_qtd:
            erros.append(f"Erro no Eixo X: Você digitou {len(x)} distâncias, mas a matriz tem {colunas_qtd} colunas.")
        if len(y) != linhas_qtd:
            erros.append(f"Erro no Eixo Y: Você digitou {len(y)} distâncias, mas a matriz tem {linhas_qtd} linhas.")

        if erros:
            for erro in erros:
                st.error(erro)
        else:
            # --- CÁLCULOS DE ÁREA E VOLUME ---
            area_total_lagoa = comprimento_lagoa * largura_lagoa
            espessura_media_lodo = np.mean(z)

            volume_nominal = area_total_lagoa * prof_max
            volume_lodo_total_estimado = area_total_lagoa * espessura_media_lodo
            volume_livre_restante = volume_nominal - volume_lodo_total_estimado
            profundidade_media_livre = prof_max - espessura_media_lodo

            densidade_lodo = 1000
            massa_seca_kg = volume_lodo_total_estimado * densidade_lodo * (sst / 100)

            # --- CONSTRUÇÃO DA TABELA HTML DE VOLUMES ---
            tabela_volumes_html = f"""
            <h4 style='color: #2c3e50;'>1. Resumo Volumétrico</h4>
            <table style='width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; background-color: white; border: 1px solid #bdc3c7;'>
                <tr style='background-color: #ecf0f1; border-bottom: 2px solid #bdc3c7;'>
                    <th style='padding: 12px; border: 1px solid #bdc3c7; color: #34495e;'>Parâmetro</th>
                    <th style='padding: 12px; border: 1px solid #bdc3c7; color: #34495e;'>Área de Referência</th>
                    <th style='padding: 12px; border: 1px solid #bdc3c7; color: #34495e;'>Profundidade / Espessura</th>
                    <th style='padding: 12px; border: 1px solid #bdc3c7; color: #34495e;'>Volume Calculado</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #555;">Capacidade Total da Lagoa</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(area_total_lagoa, 0)} m² ({format_br(comprimento_lagoa, 0)}x{format_br(largura_lagoa, 0)}m)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(prof_max)} m (máxima)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{format_br(volume_nominal)} m³</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #555;">Lodo Total Estimado*</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(area_total_lagoa, 0)} m² ({format_br(comprimento_lagoa, 0)}x{format_br(largura_lagoa, 0)}m)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(espessura_media_lodo)} m (média projetada)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{format_br(volume_lodo_total_estimado)} m³</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #555;">Volume Livre Restante</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(area_total_lagoa, 0)} m² ({format_br(comprimento_lagoa, 0)}x{format_br(largura_lagoa, 0)}m)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(profundidade_media_livre)} m (média livre)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold;">{format_br(volume_livre_restante)} m³</td>
                </tr>
                <tr style="background-color: #fff3e0;">
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #d35400;">Total de Lodo (Massa Seca)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; color: #7f8c8d; font-size: 12px;"><i>Baseado no Lodo Total Estimado</i></td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">SST: {format_br(sst)}%</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #d35400;">{format_br(massa_seca_kg)} kg</td>
                </tr>
            </table>
            """

            # --- CONSTRUÇÃO DA TABELA HTML DE DADOS (Matriz) ---
            tabela_html = "<h4 style='margin-top: 20px; margin-bottom: 10px; color: #2c3e50;'>2. Matriz de Dados Medidos (Alturas em metros)</h4>"
            tabela_html += "<div style='overflow-x: auto;'><table style='width: 100%; border-collapse: collapse; font-size: 13px; text-align: center; background-color: white; border: 1px solid #bdc3c7;'>"
            tabela_html += "<tr style='background-color: #ecf0f1; border-bottom: 2px solid #bdc3c7;'>"
            tabela_html += "<th style='padding: 8px; border: 1px solid #bdc3c7; color: #34495e;'>Largura \ Comp.</th>"
            for val_x in x:
                tabela_html += f"<th style='padding: 8px; border: 1px solid #bdc3c7; color: #34495e;'>{val_x:g}m</th>"
            tabela_html += "</tr>"

            for i in range(linhas_qtd):
                tabela_html += "<tr>"
                tabela_html += f"<th style='background-color: #ecf0f1; padding: 8px; border: 1px solid #bdc3c7; color: #34495e;'>{y[i]:g}m</th>"
                for j in range(colunas_qtd):
                    tabela_html += f"<td style='padding: 8px; border: 1px solid #bdc3c7;'>{format_br(z[i, j])}</td>"
                tabela_html += "</tr>"
            tabela_html += "</table></div>"

            # Renderiza as tabelas no Streamlit
            st.markdown(tabela_volumes_html, unsafe_allow_html=True)
            st.markdown(tabela_html, unsafe_allow_html=True)
            st.markdown("---")

            # --- SUAVIZAÇÃO E TRAVA ANTI-ELÁSTICO ---
            grau_linhas = min(3, linhas_qtd - 1)
            grau_colunas = min(3, colunas_qtd - 1)
            interp_spline = RectBivariateSpline(y, x, z, kx=grau_linhas, ky=grau_colunas)

            x_smooth = np.linspace(0, comprimento_lagoa, 200)
            y_smooth = np.linspace(0, largura_lagoa, 100)
            X_smooth, Y_smooth = np.meshgrid(x_smooth, y_smooth)
            Z_smooth = interp_spline(y_smooth, x_smooth)

            z_min_real = np.min(z)
            z_max_real = np.max(z)
            Z_smooth = np.clip(Z_smooth, z_min_real, z_max_real)

            # --- GRÁFICOS ---
            st.markdown("<h4 style='color: #2c3e50;'>3. Visualizações Gráficas</h4>", unsafe_allow_html=True)

            # Gráfico 1
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            contorno_cor = ax1.contourf(X_smooth, Y_smooth, Z_smooth, levels=15, cmap='viridis')
            contorno_linhas = ax1.contour(X_smooth, Y_smooth, Z_smooth, levels=15, colors='black', linewidths=0.5, alpha=0.7)
            ax1.clabel(contorno_linhas, inline=True, fontsize=9, fmt='%1.2f m')
            fig1.colorbar(contorno_cor, label='Altura do Lodo (m)')
            ax1.set_title('Mapa Batimétrico (Planta) - Área Total da Lagoa', fontsize=14)
            ax1.set_xlabel('Comprimento (m)')
            ax1.set_ylabel('Largura (m)')
            st.pyplot(fig1)

            # Gráfico 2
            fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(12, 10))
            z_longitudinal = np.mean(Z_smooth, axis=0)
            ax2a.fill_between(x_smooth, 0, z_longitudinal, color='#8B4513', alpha=0.8, label='Camada de Lodo')
            ax2a.fill_between(x_smooth, z_longitudinal, prof_max, color='#00CED1', alpha=0.3, label='Camada de Água (Livre)')
            ax2a.set_title('Perfil Longitudinal Médio (Corte no Comprimento)', fontsize=12)
            ax2a.set_xlabel('Comprimento (m)')
            ax2a.set_ylabel('Altura (m)')
            ax2a.set_ylim(0, prof_max + 0.1)
            ax2a.legend(loc='upper left')
            ax2a.grid(True, linestyle='--', alpha=0.5)

            z_transversal = np.mean(Z_smooth, axis=1)
            ax2b.fill_between(y_smooth, 0, z_transversal, color='#8B4513', alpha=0.8, label='Camada de Lodo')
            ax2b.fill_between(y_smooth, z_transversal, prof_max, color='#00CED1', alpha=0.3, label='Camada de Água (Livre)')
            ax2b.set_title('Perfil Transversal Médio (Corte na Largura)', fontsize=12)
            ax2b.set_xlabel('Largura (m)')
            ax2b.set_ylabel('Altura (m)')
            ax2b.set_ylim(0, prof_max + 0.1)
            ax2b.legend(loc='upper left')
            ax2b.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout(pad=3.0)
            st.pyplot(fig2)

            # Gráfico 3
            fig3 = plt.figure(figsize=(14, 7))
            ax3 = fig3.add_subplot(111, projection='3d')
            cor_massa = 'lightgray'
            ax3.plot_surface(np.array([X_smooth[0,:], X_smooth[0,:]]), np.array([Y_smooth[0,:], Y_smooth[0,:]]), np.array([np.zeros_like(Z_smooth[0,:]), Z_smooth[0,:]]), color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[-1,:], X_smooth[-1,:]]), np.array([Y_smooth[-1,:], Y_smooth[-1,:]]), np.array([np.zeros_like(Z_smooth[-1,:]), Z_smooth[-1,:]]), color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[:,0], X_smooth[:,0]]), np.array([Y_smooth[:,0], Y_smooth[:,0]]), np.array([np.zeros_like(Z_smooth[:,0]), Z_smooth[:,0]]), color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[:,-1], X_smooth[:,-1]]), np.array([Y_smooth[:,-1], Y_smooth[:,-1]]), np.array([np.zeros_like(Z_smooth[:,-1]), Z_smooth[:,-1]]), color=cor_massa, alpha=1.0)
            ax3.plot_surface(X_smooth, Y_smooth, np.zeros_like(Z_smooth), color=cor_massa, alpha=1.0)

            surf = ax3.plot_surface(X_smooth, Y_smooth, Z_smooth, cmap='viridis', edgecolor='none', alpha=1.0)
            Z_max = np.full_like(X_smooth, prof_max)
            ax3.plot_surface(X_smooth, Y_smooth, Z_max, color='cyan', alpha=0.15)

            ax3.set_title('Mapa 3D: Perfil de Acúmulo de Lodo na Lagoa', fontsize=14, pad=20)
            ax3.set_xlabel('Comprimento (m)')
            ax3.set_ylabel('Largura (m)')
            ax3.set_zlabel('Altura do Lodo (m)')
            ax3.set_zlim(0, prof_max)

            proporcao_x = comprimento_lagoa / largura_lagoa
            ax3.set_box_aspect((proporcao_x, 1, 0.8))
            fig3.colorbar(surf, shrink=0.5, aspect=5, label='Altura do Lodo (m)', pad=0.1)
            st.pyplot(fig3)

    except Exception as e:
        st.error(f"Erro ao processar os dados: Verifique se os dados inseridos estão corretos. Detalhe do erro: {e}")