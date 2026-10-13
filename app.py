import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import math

# Configuração da página e visual
st.set_page_config(page_title="Importador DiLady e Love Secret", page_icon="👙", layout="centered")

st.title("Conversor NFe: DiLady & Love Secret 👙")
st.write("Faça o upload do XML. Este sistema usa o código da fábrica (cProd) para extrair o Tamanho com 100% de precisão.")

def extrair_tamanho_cor(descricao, cprod):
    descricao_upper = str(descricao).upper()
    cprod_upper = str(cprod).upper()
    
    tamanho_encontrado = ""
    cor_encontrada = ""
    
    # 1. ESTRATÉGIA INFALÍVEL PARA O TAMANHO (Olhando o cProd)
    # Exemplo: Se cProd for "123801.503.42", ele corta nos pontos e pega a última parte ("42")
    if "." in cprod_upper:
        partes = cprod_upper.split(".")
        tamanho_encontrado = partes[-1].strip()
        
    # Plano B para o tamanho, caso o código não tenha ponto
    if not tamanho_encontrado:
        if "TAMANHO:" in descricao_upper:
            # Pega o que vem depois da palavra "TAMANHO:"
            pedaco = descricao_upper.split("TAMANHO:")[-1]
            tamanho_encontrado = pedaco.strip().split(" ")[0]
            
    # 2. BUSCA MAIS FLEXÍVEL PARA A COR
    # Adicionadas variações femininas (PRETA/BRANCA) que costumam vir nas calcinhas
    cores_comuns = [
        'PRETO', 'PRETA', 'BRANCO', 'BRANCA', 'BEGE', 'CHOCOLATE', 'NUDE', 'BLUSH', 
        'VERMELHO', 'VERMELHA', 'MARINHO', 'ROSA', 'CASTANHO', 'AVELA', 'MACADAMIA', 
        'CARMIN', 'BASE', 'SORTIDO', 'BLK', 'BNC'
    ]
    
    for cor in cores_comuns:
        if cor in descricao_upper:
            cor_encontrada = cor
            # Se achar "PRETA", preenche como "PRETO" para padronizar
            if cor_encontrada == 'PRETA': cor_encontrada = 'PRETO'
            if cor_encontrada == 'BRANCA': cor_encontrada = 'BRANCO'
            if cor_encontrada == 'VERMELHA': cor_encontrada = 'VERMELHO'
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
                
                # --- A EXTRAÇÃO AGORA ENVIA O CÓDIGO DA FÁBRICA TAMBÉM ---
                tamanho_extraido, cor_extraida = extrair_tamanho_cor(descricao, referencia)
                
                # Cálculo do Preço
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
