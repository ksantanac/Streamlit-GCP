import streamlit as st
import re
import time

from google.cloud import storage
from datetime import datetime

# Configuração da página
st.title("Upload de Arquivo Sintegra")

# Funções auxiliares
def validar_cnpj(cnpj):
    """Verifica se o CNPJ é válido (apenas números e tamanho correto)."""
    return re.fullmatch(r"\d{14}", cnpj) is not None

def validar_arquivo_conteudo(conteudo):
    """Valida o conteúdo do arquivo para garantir que só contenha CNPJs válidos."""
    linhas = conteudo.splitlines()
    for linha in linhas:
        if not validar_cnpj(linha.strip()):
            return False
    return True

def contar_cnpjs_e_linhas(conteudo):
    """Conta o número de CNPJs e o total de linhas no arquivo."""
    linhas = conteudo.splitlines()
    cnpjs_validos = [linha.strip() for linha in linhas if validar_cnpj(linha.strip())]
    return len(cnpjs_validos), len(linhas)

def enviar_para_gcp(file_data, file_name):
    """Envia o arquivo para o bucket do GCP na pasta EXTRACT com nome alterado para incluir data e hora."""
    
    # Obter data e hora atual para adicionar no nome do arquivo
    data_hora_atual = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    
    # Extrair o nome original do arquivo (sem a extensão) e adicionar a data e hora antes da extensão
    nome_arquivo_sem_extensao = file_name.rsplit('.', 1)[0]
    nome_arquivo_com_data = f"{nome_arquivo_sem_extensao}_{data_hora_atual}.txt"
    
    bucket_name = "streamlit-upload1"
    client = storage.Client(project="streamlit-445200")
    bucket = client.bucket(bucket_name)
    
    # Coloca o arquivo na pasta EXTRACT
    blob = bucket.blob(f"EXTRACT/{nome_arquivo_com_data}")
    blob.upload_from_string(file_data)
    
    st.success(f"Arquivo enviado com sucesso para a pasta EXTRACT do bucket: {bucket_name} com o nome {nome_arquivo_com_data}")

# Inicializa o estado de sessão
if "arquivo_enviado" not in st.session_state:
    st.session_state.arquivo_enviado = False

# Upload do arquivo
arquivo = st.file_uploader("Selecione um arquivo .txt com CNPJs", type="txt")

if arquivo is not None and not st.session_state.arquivo_enviado:
    # Leitura do conteúdo
    conteudo = arquivo.getvalue().decode("utf-8")

    # Validações
    if validar_arquivo_conteudo(conteudo):
        st.success("O arquivo foi validado com sucesso!")

        # Contar e exibir o número de CNPJs e linhas
        total_cnpjs, total_linhas = contar_cnpjs_e_linhas(conteudo)
        st.info(f"O arquivo contém {total_cnpjs} CNPJs válidos em {total_linhas} linhas.")

        # Botão para enviar para o bucket
        if st.button("Enviar para o Bucket"):
            enviar_para_gcp(conteudo, arquivo.name)
            
            # Marcar que o arquivo foi enviado
            st.session_state.arquivo_enviado = True

    else:
        st.error("O arquivo contém linhas que não são CNPJs válidos.")

# Caso o arquivo tenha sido enviado com sucesso, exibe uma mensagem de sucesso
if st.session_state.arquivo_enviado:
    success_message = st.success("Arquivo já enviado para o bucket!")

    time.sleep(2)
    success_message.empty()

    # Resetar o estado para permitir novo upload
    st.rerun()

    # Limpar o estado da sessão para resetar a aplicação
    st.session_state.clear()