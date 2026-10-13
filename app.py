import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import math
import re  # Ferramenta avançada para buscar padrões de texto

# Configuração da página e visual
st.set_page_config(page_title="Importador DiLady e Love Secret", page_icon="👙", layout="centered")

st.title("Conversor NFe: DiLady & Love Secret 👙")
st.write("Faça o upload do XML. Este sistema extrai as Cores e Tamanhos do padrão DiLady/Love Secret automaticamente.")

def extrair_tamanho_cor(descricao):
    descricao_upper = descricao.upper()
    
    tamanho_encontrado = ""
    cor_encontrada = ""
    
    # 1. BUSCA CIRÚRGICA DO TAMANHO
    # Procura exatamente por "TAMANHO:" e captura a letra ou número que vem depois
    match_tamanho = re.search(r'TAMANHO:\s*([A-Z0-9]+)', descricao_upper)
    if match_tamanho:
        tamanho_encontrado = match_tamanho.group(1)
        
    # 2. BUSCA DA COR
    # Lista atualizada com as cores do fornecedor (incluindo as siglas como BLK e BNC)
    cores_comuns = ['PRETO', 'BRANCO', 'BEGE', 'CHOCOLATE', 'NUDE', 'BLUSH', 'VERMELHO', 'MARINHO', 'ROSA', 'CASTANHO', 'AVELA', 'MACADAMIA', 'CARMIN', 'BASE', 'SORTIDO', 'BLK', 'BNC']
    
    for cor in cores_comuns:
        # A regra \b garante que ele ache a cor como palavra inteira (ex: BEGE)
        if re.search(r'\b' + cor + r'\b', descricao_upper):
            cor_encontrada = cor
            break
            
    return tamanho_encontrado, cor_encontrada

# Botão de Upload na interface
uploaded_file = st.file_uploader("Arraste e solte o arquivo XML aqui", type=["xml"])

if uploaded_file is not None:
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        produtos = root.findall('.//nfe:det', ns)
        
        if not produtos:
            st.error("❌ Nenhum produto encontrado neste XML.")
        else:
            # Estrutura do Microvix (já sem a coluna Código Integracao OMS)
            colunas_microvix = [
                "Código", "Descrição", "Referência", "Cód. Auxiliar", "Fornecedor", 
                "Fornecedor exclusivo", "Comprador", "Empresa", "Contabiliza saldo em estoque", 
                "Indisponível para venda", "Setor", "Linha", "Marca", "Coleção", 
                "Espessura", "Classificação", "Tamanho", "Cores", "Unidade de compra", 
                "Unidade de venda", "Fator de conversão", "Múltiplo de venda", "Moeda", 
                "Custo com ICMS (R$)", "Desconto (%)", "Acréscimo (%)", "IPI (%)", 
                "Frete (R$)", "Despesas acessórias (R$)", "Substituição tributária (R$)", 
                "Diferencial ICMS (R$)", "Mark-up (%)", "Preço de venda R$", "Permite desconto", 
                "Comissão %", "Configuração tributária", "NCM", "CEST", "Produto supérfluo", 
                "Tipo de item", "Origem da mercadoria", "Regime de Incidência PIS e COFINS", 
                "Produto é brinde", "Produto de catálogo", "Descrição de catálogo", 
                "Disponível na loja virtual", "Exige controle", "Tipo de controle", 
                "Tamanho controle", "Peso bruto (kg)", "Peso líquido (kg)", "Descrição complementar?", 
                "Altura (frete)", "Largura (frete)", "Comprimento (frete)", "Altura", 
                "Largura", "Comprimento", "Importado por balança", "Produto vendido por (balança)", 
                "Quantidade mínima", "Quantidade máxima", "Quantidade compra", "Localização", 
                "Observação", "Código de barras", "Características", "Status", 
                "Produto Desativado", "Bloqueia atualização de preço franqueadora"
            ]
            
            dados_planilha = []
            
            for det in produtos:
                prod = det.find('nfe:prod', ns)
                
                descricao = prod.find('nfe:xProd', ns).text if prod.find('nfe:xProd', ns) is not None else ""
                referencia = prod.find('nfe:cProd', ns).text if prod.find('nfe:cProd', ns) is not None else ""
                ncm = prod.find('nfe:NCM', ns).text if prod.find('nfe:NCM', ns) is not None else ""
                ean = prod.find('nfe:cEAN', ns).text if prod.find('nfe:cEAN', ns) is not None else ""
                unidade = prod.find('nfe:uCom', ns).text if prod.find('nfe:uCom', ns) is not None else ""
                
                # --- A MÁGICA DE EXTRAÇÃO ACONTECE AQUI ---
                tamanho_extraido, cor_extraida = extrair_tamanho_cor(descricao)
                
                # Cálculo do Preço (Dobro e arredonda para cima terminando em .90)
                custo_str = prod.find('nfe:vUnCom', ns).text if prod.find('nfe:vUnCom', ns) is not None else "0"
                preco_venda_formatado = ""
                try:
                    custo_float = float(custo_str)
                    if custo_float > 0:
                        dobro = custo_float * 2
                        preco_calculado = math.ceil(dobro - 0.90) + 0.90
                        preco_venda_formatado = f"{preco_calculado:.2f}".replace('.', ',')
                except ValueError:
                    preco_venda_formatado = ""
                
                if ean == "SEM GTIN": ean = ""
                
                linha_excel = {coluna: "" for coluna in colunas_microvix}
                
                linha_excel["Descrição"] = descricao
                linha_excel["Referência"] = referencia
                linha_excel["Custo com ICMS (R$)"] = custo_str.replace('.', ',')
                linha_excel["NCM"] = ncm
                linha_excel["Código de barras"] = ean
                
                # Preenchendo as colunas Cor e Tamanho
                linha_excel["Tamanho"] = tamanho_extraido
                linha_excel["Cores"] = cor_extraida
                
                # Mantendo os seus padrões e fórmulas
                linha_excel["Unidade de compra"] = unidade
                linha_excel["Unidade de venda"] = unidade
                linha_excel["Preço de venda R$"] = preco_venda_formatado
                linha_excel["Fator de conversão"] = "1"
                linha_excel["Configuração tributária"] = "1"
                linha_excel["Espessura"] = "0"
                linha_excel["Tipo de item"] = "1"
                linha_excel["Comprador"] = "14"
                linha_excel["Empresa"] = "5"
                linha_excel["Contabiliza saldo em estoque"] = "S"
                
                dados_planilha.append(linha_excel)
                
            df = pd.DataFrame(dados_planilha, columns=colunas_microvix)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            excel_data = output.getvalue()
            
            st.success(f"✅ Sucesso! {len(produtos)} produtos processados.")
            
            st.download_button(
                label="📥 Baixar Excel DiLady/Love Secret",
                data=excel_data,
                file_name="importacao_dilady.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
