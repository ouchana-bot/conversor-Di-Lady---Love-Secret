import streamlit as st
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Diagnóstico DiLady", layout="wide")
st.title("Diagnóstico de XML DiLady / Love Secret 🕵️‍♂️")
st.write("Faça o upload do XML para vermos onde estão escondidas a cor e o tamanho!")

uploaded_file = st.file_uploader("Arraste e solte o XML aqui", type=["xml"])

if uploaded_file is not None:
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        produtos = root.findall('.//nfe:det', ns)
        
        if not produtos:
            st.error("Nenhum produto encontrado.")
        else:
            st.success(f"Encontrei {len(produtos)} produtos. Veja a análise do primeiro:")
            
            # Vamos analisar apenas o primeiro produto
            det = produtos[0]
            prod = det.find('nfe:prod', ns)
            
            st.subheader("1. Dados Básicos (<prod>)")
            cProd = prod.find('nfe:cProd', ns)
            st.write(f"**Referência (cProd):** {cProd.text if cProd is not None else 'Vazio'}")
            
            xProd = prod.find('nfe:xProd', ns)
            st.write(f"**Descrição (xProd):** {xProd.text if xProd is not None else 'Vazio'}")
            
            st.subheader("2. Procurando em TODOS os outros campos...")
            # Percorre todas as tags dentro do <prod> do primeiro item
            for child in prod:
                tag_name = child.tag.split('}')[-1]
                if tag_name not in ['cProd', 'xProd']:
                    st.write(f"**Tag `{tag_name}`:** {child.text}")
                    
            st.subheader("3. Informações Adicionais (Pode estar aqui!)")
            infAdProd = det.find('nfe:infAdProd', ns)
            if infAdProd is not None:
                st.info(f"**Informação Adicional (<infAdProd>):** {infAdProd.text}")
            else:
                st.warning("O campo <infAdProd> não existe para este produto.")
                
            # Verifica se existe alguma tag diferente fora do <prod>
            st.subheader("4. Outras Tags no Produto")
            for child in det:
                tag_name = child.tag.split('}')[-1]
                if tag_name not in ['prod', 'imposto', 'infAdProd']:
                    st.write(f"**Tag `{tag_name}`:** {child.text}")

    except Exception as e:
        st.error(f"Erro ao ler o XML: {e}")
