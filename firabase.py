import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Carrega as variáveis de ambiente
load_dotenv()

class FirebaseManager:
    def __init__(self):
        """Inicializa conexão com Firebase"""
        try:
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            print("✅ Conectado ao Firebase!")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def adicionar_tarefa(self, titulo, descricao=""):
        """Adiciona uma nova tarefa"""
        try:
            tarefa = {
                'titulo': titulo,
                'descricao': descricao,
                'criado_em': datetime.now(),
                'concluida': False
            }
            
            doc_ref = self.db.collection('tarefas').document()
            doc_ref.set(tarefa)
            print(f"✅ Tarefa adicionada! ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            print(f"❌ Erro ao adicionar: {e}")
    
    def listar_tarefas(self):
        """Lista todas as tarefas"""
        try:
            tarefas = self.db.collection('tarefas').stream()
            
            print("\n📋 MINHAS TAREFAS:")
            print("-" * 40)
            
            for tarefa in tarefas:
                dados = tarefa.to_dict()
                status = "✅" if dados.get('concluida') else "⏳"
                print(f"{status} {dados.get('titulo')}")
                print(f"   ID: {tarefa.id}")
                if dados.get('descricao'):
                    print(f"   📝 {dados.get('descricao')}")
                print()
                
        except Exception as e:
            print(f"❌ Erro ao listar: {e}")
    
    def concluir_tarefa(self, tarefa_id):
        """Marca tarefa como concluída"""
        try:
            tarefa_ref = self.db.collection('tarefas').document(tarefa_id)
            tarefa_ref.update({
                'concluida': True,
                'concluida_em': datetime.now()
            })
            print(f"✅ Tarefa {tarefa_id} concluída!")
        except Exception as e:
            print(f"❌ Erro ao concluir: {e}")

# ===== MENU INTERATIVO =====
def main():
    firebase = FirebaseManager()
    
    while True:
        print("\n" + "="*40)
        print("📱 GERENCIADOR DE TAREFAS")
        print("="*40)
        print("1️⃣ - Adicionar tarefa")
        print("2️⃣ - Listar tarefas")
        print("3️⃣ - Concluir tarefa")
        print("4️⃣ - Sair")
        print("="*40)
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == '1':
            titulo = input("Título da tarefa: ")
            descricao = input("Descrição (opcional): ")
            firebase.adicionar_tarefa(titulo, descricao)
            
        elif opcao == '2':
            firebase.listar_tarefas()
            
        elif opcao == '3':
            tarefa_id = input("ID da tarefa para concluir: ")
            firebase.concluir_tarefa(tarefa_id)
            
        elif opcao == '4':
            print("👋 Até mais!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()