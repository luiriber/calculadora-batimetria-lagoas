import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RectBivariateSpline
import base64
from io import BytesIO
import json

# Configuração da página do Streamlit
st.set_page_config(page_title="Calculadora Batimétrica", layout="wide")

# ==========================================
# GERENCIAMENTO: IMPORTAR / CARREGAR DADOS
# ==========================================
st.sidebar.header("📂 Gerenciar Projeto")

arquivo_importado = st.sidebar.file_uploader("📥 Carregar Projeto Salvo (.json)", type=["json"])
if arquivo_importado is not None:
    try:
        dados_carregados = json.load(arquivo_importado)
        for key, value in dados_carregados.items():
            st.session_state[key] = value
        st.sidebar.success("Dados carregados com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao ler o arquivo: {e}")

# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================
def format_br(num, decimals=2):
    return f"{num:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_distancias(texto):
    t = texto.replace(';', ' ').replace(',', '.')
    return np.array([float(i) for i in t.split()])

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f'<img src="data:image/png;base64,{img_str}" style="width:100%; max-width:100%; margin-top: 15px;">'

# ==========================================
# INTERFACE DE USUÁRIO (STREAMLIT)
# ==========================================
st.title("🌊 Calculadora Batimétrica de Lagoas")
st.markdown("Preencha os dados abaixo para gerar o relatório técnico completo.")

with st.expander("📋 Cabeçalho do Relatório", expanded=True):
    logo_upload = st.file_uploader("Upload Logo (Opcional)", type=['png', 'jpg', 'jpeg'])
    col1, col2, col3 = st.columns(3)
    cliente_input = col1.text_input("Cliente:", placeholder="Nome da empresa cliente", key="cliente")
    data_input = col2.text_input("Data do Levantamento:", placeholder="Ex: 25/10/2023", key="data_lev")
    resp_input = col3.text_input("Resp. Técnico:", placeholder="Nome e CREA/CRQ", key="resp_tec")

with st.expander("🏢 Dados da ETE", expanded=True):
    col1, col2 = st.columns(2)
    nome_ete_input = col1.text_input("Nome da ETE:", key="nome_ete")
    municipio_input = col2.text_input("Município/UF:", key="municipio")
    coord_input = col1.text_input("Coordenadas:", placeholder="Ex: 23°33'S, 46°38'W", key="coord")
    link_maps_input = col2.text_input("Link Google Maps:", key="link_maps")
    img_maps_upload = st.file_uploader("Upload Imagem do Mapa (Opcional)", type=['png', 'jpg', 'jpeg'])
    desc_ete_input = st.text_area("Descrição da ETE:", placeholder="Breve descrição do local...", key="desc_ete")

with st.expander("💧 Dados da Lagoa", expanded=True):
    nome_lagoa_input = st.text_input("Nome da Lagoa:", placeholder="Ex: Lagoa Anaeróbia 01", key="nome_lagoa")
    desc_lagoa_input = st.text_area("Descrição da Lagoa:", placeholder="Breve descrição da lagoa...", key="desc_lagoa")

with st.expander("📝 Textos do Relatório", expanded=True):
    objetivo_input = st.text_area("Objetivo:", placeholder="Descreva o objetivo deste relatório...", key="objetivo")
    metodologia_input = st.text_area("Metodologia:", placeholder="Descreva a metodologia utilizada...", key="metodologia")
    conclusao_input = st.text_area("Conclusões e Recomendações:", placeholder="Descreva as conclusões...", key="conclusao")

with st.expander("📊 Dados Batimétricos (Medições)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    profundidade_max_input = col1.number_input("Profundidade Máx. (m):", value=1.50, step=0.1, key="prof_max")
    comprimento_input = col2.number_input("Comprimento Total (m):", value=75.0, step=1.0, key="comprimento")
    largura_input = col3.number_input("Largura Total (m):", value=30.0, step=1.0, key="largura")
    sst_input = col4.number_input("Concentração SST (%):", value=8.0, step=0.1, key="sst")

    distancias_x_input = st.text_input("Distâncias X (Comprimento) [m]:", value="10 20 30 40 50 60 70 80", key="dist_x")
    distancias_y_input = st.text_input("Distâncias Y (Largura) [m]:", value="10 20 30", key="dist_y")

    # usando \n reais e \t reais
    matriz_padrao = (
        "0.90\t0.50\t0.15\t0.20\t0.40\t0.40\t0.80\t0.85\n"
        "0.95\t0.70\t0.25\t0.15\t0.10\t0.10\t0.40\t0.90\n"
        "1.00\t1.00\t0.60\t0.25\t0.20\t0.40\t0.70\t0.70"
    )
    matriz_input = st.text_area(
        "Dados do Lodo (Matriz copiada do Excel):",
        value=matriz_padrao,
        height=150,
        key="matriz"
    )

# ==========================================
# EXPORTAR / SALVAR DADOS
# ==========================================
chaves_para_salvar = [
    "cliente", "data_lev", "resp_tec", "nome_ete", "municipio", "coord", "link_maps", "desc_ete",
    "nome_lagoa", "desc_lagoa", "objetivo", "metodologia", "conclusao",
    "prof_max", "comprimento", "largura", "sst", "dist_x", "dist_y", "matriz"
]

dados_atuais = {k: st.session_state.get(k, "") for k in chaves_para_salvar}
json_dados = json.dumps(dados_atuais, indent=4, ensure_ascii=False)

st.sidebar.markdown("---")
st.sidebar.download_button(
    label="💾 Salvar Dados Atuais (.json)",
    data=json_dados,
    file_name="dados_batimetria.json",
    mime="application/json",
    use_container_width=True
)

# ==========================================
# PROCESSAMENTO E GERAÇÃO DO RELATÓRIO
# ==========================================
if st.button("🚀 Gerar Relatório Completo", type="primary", use_container_width=True):
    with st.spinner("Processando dados e gerando gráficos..."):
        try:
            # --- PROCESSAMENTO DE IMAGENS ---
            logo_tag = ""
            if logo_upload is not None:
                logo_b64 = base64.b64encode(logo_upload.getvalue()).decode('utf-8')
                logo_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 80px;">'

            img_mapa_tag = ""
            if img_maps_upload is not None:
                mapa_b64 = base64.b64encode(img_maps_upload.getvalue()).decode('utf-8')
                img_mapa_tag = (
                    f'<div style="text-align: center; margin-top: 15px;">'
                    f'<img src="data:image/png;base64,{mapa_b64}" '
                    f'style="max-width: 100%; border: 1px solid #bdc3c7;"></div>'
                )

            link_tag = "-"
            if link_maps_input:
                link_tag = (
                    f'<a href="{link_maps_input}" target="_blank" '
                    f'style="color: #2980b9; text-decoration: none;">'
                    f'📍 Ver no Google Maps</a>'
                )

            # --- PROCESSAMENTO MATEMÁTICO ---
            x = parse_distancias(distancias_x_input)
            y = parse_distancias(distancias_y_input)

            # BLOCO CORRIGIDO PARA A MATRIZ
            texto_matriz = matriz_input.replace('\r\n', '\n').replace('\r', '\n')
            texto_matriz = texto_matriz.replace('\\n', '\n').replace('\\t', '\t')

            linhas_str = [linha for linha in texto_matriz.split('\n') if linha.strip() != ""]

            matriz_lista = []
            for linha in linhas_str:
                valores = linha.strip().replace(',', '.').split()
                if len(valores) > 0:
                    matriz_lista.append([float(v) for v in valores])

            if len(matriz_lista) == 0:
                st.error("A matriz de dados está vazia. Verifique o preenchimento.")
                st.stop()

            z = np.array(matriz_lista)

            linhas_qtd, colunas_qtd = z.shape
            if len(y) != linhas_qtd or len(x) != colunas_qtd:
                st.error(
                    f"Erro de Dimensão: A matriz tem {linhas_qtd} linhas e {colunas_qtd} colunas. "
                    f"As distâncias Y têm {len(y)} valores e X têm {len(x)} valores. "
                    "Eles precisam ser iguais."
                )
                st.stop()

            # Cálculos de Volume
            area_lagoa = comprimento_input * largura_input
            volume_total_lagoa = area_lagoa * profundidade_max_input
            espessura_media_lodo = np.mean(z)
            volume_lodo_total_estimado = area_lagoa * espessura_media_lodo
            volume_livre_restante = volume_total_lagoa - volume_lodo_total_estimado

            percentual_lodo = (
                (volume_lodo_total_estimado / volume_total_lagoa) * 100
                if volume_total_lagoa > 0 else 0
            )

            densidade_lodo = 1000
            massa_seca_kg = volume_lodo_total_estimado * densidade_lodo * (sst_input / 100)

            # Interpolação
            grau_linhas = min(3, linhas_qtd - 1)
            grau_colunas = min(3, colunas_qtd - 1)
            interp_spline = RectBivariateSpline(y, x, z, kx=grau_linhas, ky=grau_colunas)

            x_smooth = np.linspace(0, comprimento_input, 200)
            y_smooth = np.linspace(0, largura_input, 100)
            X_smooth, Y_smooth = np.meshgrid(x_smooth, y_smooth)
            Z_smooth = interp_spline(y_smooth, x_smooth)
            Z_smooth = np.clip(Z_smooth, np.min(z), np.max(z))

            # --- GERAÇÃO DOS GRÁFICOS ---
            # Gráfico 1
            fig1, ax1 = plt.subplots(figsize=(8, 4))
            contorno_cor = ax1.contourf(X_smooth, Y_smooth, Z_smooth, levels=15, cmap='viridis')
            contorno_linhas = ax1.contour(X_smooth, Y_smooth, Z_smooth, levels=15,
                                          colors='black', linewidths=0.5, alpha=0.7)
            ax1.clabel(contorno_linhas, inline=True, fontsize=9, fmt='%1.2f m')
            fig1.colorbar(contorno_cor, label='Altura do Lodo (m)')
            ax1.set_title('Mapa Batimétrico (Planta) - Área Total da Lagoa', fontsize=12)
            ax1.set_xlabel('Comprimento (m)')
            ax1.set_ylabel('Largura (m)')
            img_grafico1 = fig_to_base64(fig1)

            # Gráfico 2
            fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(8, 7))
            z_longitudinal = np.mean(Z_smooth, axis=0)
            ax2a.fill_between(x_smooth, 0, z_longitudinal, color='#8B4513', alpha=0.8, label='Camada de Lodo')
            ax2a.fill_between(x_smooth, z_longitudinal, profundidade_max_input,
                              color='#00CED1', alpha=0.3, label='Camada de Água (Livre)')
            ax2a.set_title('Perfil Longitudinal Médio (Corte no Comprimento)', fontsize=10)
            ax2a.set_xlabel('Comprimento (m)')
            ax2a.set_ylabel('Altura (m)')
            ax2a.set_ylim(0, profundidade_max_input + 0.1)
            ax2a.legend(loc='upper left', fontsize=8)
            ax2a.grid(True, linestyle='--', alpha=0.5)

            z_transversal = np.mean(Z_smooth, axis=1)
            ax2b.fill_between(y_smooth, 0, z_transversal, color='#8B4513', alpha=0.8, label='Camada de Lodo')
            ax2b.fill_between(y_smooth, z_transversal, profundidade_max_input,
                              color='#00CED1', alpha=0.3, label='Camada de Água (Livre)')
            ax2b.set_title('Perfil Transversal Médio (Corte na Largura)', fontsize=10)
            ax2b.set_xlabel('Largura (m)')
            ax2b.set_ylabel('Altura (m)')
            ax2b.set_ylim(0, profundidade_max_input + 0.1)
            ax2b.legend(loc='upper left', fontsize=8)
            ax2b.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout(pad=2.0)
            img_grafico2 = fig_to_base64(fig2)

            # Gráfico 3
            fig3 = plt.figure(figsize=(8, 6))
            ax3 = fig3.add_subplot(111, projection='3d')
            cor_massa = 'lightgray'
            ax3.plot_surface(np.array([X_smooth[0, :], X_smooth[0, :]]),
                             np.array([Y_smooth[0, :], Y_smooth[0, :]]),
                             np.array([np.zeros_like(Z_smooth[0, :]), Z_smooth[0, :]]),
                             color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[-1, :], X_smooth[-1, :]]),
                             np.array([Y_smooth[-1, :], Y_smooth[-1, :]]),
                             np.array([np.zeros_like(Z_smooth[-1, :]), Z_smooth[-1, :]]),
                             color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[:, 0], X_smooth[:, 0]]),
                             np.array([Y_smooth[:, 0], Y_smooth[:, 0]]),
                             np.array([np.zeros_like(Z_smooth[:, 0]), Z_smooth[:, 0]]),
                             color=cor_massa, alpha=1.0)
            ax3.plot_surface(np.array([X_smooth[:, -1], X_smooth[:, -1]]),
                             np.array([Y_smooth[:, -1], Y_smooth[:, -1]]),
                             np.array([np.zeros_like(Z_smooth[:, -1]), Z_smooth[:, -1]]),
                             color=cor_massa, alpha=1.0)
            ax3.plot_surface(X_smooth, Y_smooth, np.zeros_like(Z_smooth), color=cor_massa, alpha=1.0)
            surf = ax3.plot_surface(X_smooth, Y_smooth, Z_smooth,
                                    cmap='viridis', edgecolor='none', alpha=1.0)
            Z_max = np.full_like(X_smooth, profundidade_max_input)
            ax3.plot_surface(X_smooth, Y_smooth, Z_max, color='cyan', alpha=0.15)
            ax3.set_title('Mapa 3D: Perfil de Acúmulo de Lodo na Lagoa', fontsize=12, pad=10)
            ax3.set_xlabel('Comprimento (m)')
            ax3.set_ylabel('Largura (m)')
            ax3.set_zlabel('Altura do Lodo (m)')
            ax3.set_zlim(0, profundidade_max_input)
            ax3.set_box_aspect((comprimento_input / largura_input, 1, 0.8))
            fig3.colorbar(surf, shrink=0.5, aspect=5, label='Altura do Lodo (m)', pad=0.1)
            img_grafico3 = fig_to_base64(fig3)

            # --- TABELAS HTML ---
            tabela_volumes = f"""
            <h3 style="color: #2980b9; margin-top: 30px;">5. Resultados Volumétricos</h3>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; margin-bottom: 20px;">
                <tr style="background-color: #34495e; color: white;">
                    <th style="padding: 12px; border: 1px solid #2c3e50;">Parâmetro</th>
                    <th style="padding: 12px; border: 1px solid #2c3e50;">Valor Calculado</th>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Capacidade Total da Lagoa</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{format_br(volume_total_lagoa)} m³</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Lodo Total Estimado</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #d35400;">{format_br(volume_lodo_total_estimado)} m³</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Percentual de Lodo (em relação ao volume total)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #d35400;">{format_br(percentual_lodo)} %</td>
                </tr>
                <tr>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">Volume Livre Restante (Água)</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6; font-weight: bold; color: #2980b9;">{format_br(volume_livre_restante)} m³</td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; margin-bottom: 20px;">
                <tr style="background-color: #ecf0f1;">
                    <th style="padding: 10px; border: 1px solid #bdc3c7; color: #34495e;">Total de Lodo (Massa Seca)</th>
                    <th style="padding: 10px; border: 1px solid #bdc3c7; color: #34495e;">Concentração Adotada</th>
                    <th style="padding: 10px; border: 1px solid #bdc3c7; color: #34495e;">Massa Seca Total</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #bdc3c7; color: #7f8c8d;">Baseado no Lodo Total Estimado</td>
                    <td style="padding: 10px; border: 1px solid #bdc3c7; color: #d35400;">SST: {format_br(sst_input)}%</td>
                    <td style="padding: 10px; border: 1px solid #bdc3c7; font-weight: bold; color: #d35400;">{format_br(massa_seca_kg)} kg</td>
                </tr>
            </table>
            """

            tabela_matriz = """
            <div class="avoid-break">
            <h3 style="color: #2980b9; margin-top: 30px;">6. Matriz de Dados Medidos (Alturas em metros)</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; margin-bottom: 20px;">
                <tr style="background-color: #ecf0f1;">
                    <th style="padding: 8px; border: 1px solid #bdc3c7; color: #34495e;">Largura \\ Comp.</th>
            """
            for val_x in x:
                tabela_matriz += (
                    f"<th style='padding: 8px; border: 1px solid #bdc3c7; "
                    f"color: #34495e;'>{val_x:g}m</th>"
                )
            tabela_matriz += "</tr>"

            for i in range(linhas_qtd):
                tabela_matriz += "<tr>"
                tabela_matriz += (
                    f"<th style='background-color: #ecf0f1; padding: 8px; "
                    f"border: 1px solid #bdc3c7; color: #34495e;'>{y[i]:g}m</th>"
                )
                for j in range(colunas_qtd):
                    tabela_matriz += (
                        f"<td style='padding: 8px; border: 1px solid #bdc3c7;'>"
                        f"{format_br(z[i, j])}</td>"
                    )
                tabela_matriz += "</tr>"
            tabela_matriz += "</table></div>"

            # --- HTML FINAL ---
            relatorio_html = f"""
            <div id="relatorio-container" style="font-family: Arial, sans-serif; max-width: 21cm; margin: 0 auto; background-color: white; padding: 20px; box-sizing: border-box;">

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="width: 30%; vertical-align: middle;">{logo_tag}</td>
                        <td style="width: 70%; text-align: right; line-height: 1.5; font-size: 14px; color: #34495e;">
                            <b>Cliente:</b> {cliente_input or '-'}<br>
                            <b>Data:</b> {data_input or '-'}<br>
                            <b>Responsável Técnico:</b> {resp_input or '-'}
                        </td>
                    </tr>
                </table>

                <h2 style="text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">RELATÓRIO TÉCNICO BATIMÉTRICO</h2>

                <h3 style="color: #2980b9; margin-top: 30px;">1. Identificação da ETE</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 10px;">
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold; width: 25%;">Nome da ETE:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{nome_ete_input or '-'}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold;">Município/UF:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{municipio_input or '-'}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold;">Coordenadas:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{coord_input or '-'}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold;">Localização:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{link_tag}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold;">Descrição:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{desc_ete_input or '-'}</td></tr>
                </table>
                {img_mapa_tag}

                <h3 style="color: #2980b9; margin-top: 30px;">2. Identificação da Lagoa</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 20px;">
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold; width: 25%;">Nome da Lagoa:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{nome_lagoa_input or '-'}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #bdc3c7; background-color: #ecf0f1; font-weight: bold;">Descrição:</td><td style="padding: 8px; border: 1px solid #bdc3c7;">{desc_lagoa_input or '-'}</td></tr>
                </table>

                <h3 style="color: #2980b9; margin-top: 30px;">3. Objetivo</h3>
                <p style="text-align: justify; font-size: 14px; color: #444; line-height: 1.6;">{objetivo_input or 'Não informado.'}</p>

                <h3 style="color: #2980b9; margin-top: 30px;">4. Metodologia</h3>
                <p style="text-align: justify; font-size: 14px; color: #444; line-height: 1.6;">{metodologia_input or 'Não informada.'}</p>

                {tabela_volumes}
                {tabela_matriz}

                <div class="avoid-break">
                    <h3 style="color: #2980b9; margin-top: 30px;">7. Conclusões e Recomendações</h3>
                    <p style="text-align: justify; font-size: 14px; color: #444; line-height: 1.6;">{conclusao_input or 'Não informada.'}</p>
                </div>

                <div class="avoid-break">
                    <h3 style="color: #2980b9; margin-top: 40px;">8. Anexos Gráficos</h3>
                    {img_grafico1}
                </div>
                <div class="avoid-break">{img_grafico2}</div>
                <div class="avoid-break">{img_grafico3}</div>

                <div class="avoid-break" style="margin-top: 60px; text-align: center;">
                    <div style="width: 350px; border-top: 1px solid #000; margin: 0 auto; padding-top: 10px;">
                        <b style="color: #2c3e50; font-size: 16px;">{resp_input or 'Responsável Técnico'}</b><br>
                        <span style="font-size: 13px; color: #555;">Assinatura do Responsável</span>
                    </div>
                </div>
            </div>
            """

            st.markdown("---")
            st.subheader("📄 Visualização do Relatório")

            st.download_button(
                label="💾 Baixar Relatório para Impressão (HTML)",
                data=relatorio_html,
                file_name="relatorio_batimetrico.html",
                mime="text/html",
                help="Baixe este arquivo, abra no seu navegador (Chrome/Edge) e aperte Ctrl+P para salvar como PDF limpo."
            )

            st.components.v1.html(relatorio_html, height=1200, scrolling=True)

        except Exception as e:
            st.error(f"Erro ao processar os dados: Verifique se os dados inseridos estão corretos. Detalhe do erro: {e}")
