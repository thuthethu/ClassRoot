# ClassRoot 🌱
**A raiz de toda sala de aula.**

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python) 
![Flask](https://img.shields.io/badge/Flask-Framework-lightgrey?logo=flask) 
![SQLite](https://img.shields.io/badge/SQLite-Database-blue?logo=sqlite) 
![License](https://img.shields.io/badge/License-GPL%20v3-green)

Para professores raiz, a alternativa digital ao diário de papel.
Base aberta para desenvolvedores fazerem a árvore crescer.

---

## O problema 📝

Professores dependem da memória, de papéis soltos e de sistemas online que exigem internet, login e paciência. O **ClassRoot** nasceu da vivência prática do professor para resolver isso de forma simples, offline e extremamente rápida.

---

## O que é o ClassRoot?

Um sistema local de gestão de turmas e aulas para professores de qualquer nível de ensino. Roda no próprio computador, sem internet, sem servidor, sem burocracia.

O projeto é **voltado para o professor** e não para uma instituição específica. Isso significa que, se você dá aula em mais de uma escola, pode gerenciar todos os seus diários pelo mesmo banco de dados, sem precisar de aplicações separadas. Basta identificar o nome da escola junto ao nome da turma (ex: "9º A - Escola X") para manter tudo organizado em um único lugar.

É um **esqueleto intencional**. Funciona. E foi pensado para que desenvolvedores possam construir em cima sem precisar começar do zero.

---

## Destaques (Teacher-First Logic) 💡

O ClassRoot foi desenvolvido focando na realidade do professor, com algumas automações que salvam tempo:

### 📸 Carômetro Inteligente (Fuzzy Matching)
O sistema não exige que o nome do arquivo da foto seja idêntico ao nome na lista oficial. Ele utiliza uma lógica de **Tokens e Fuzzy Matching** para associar fotos a alunos mesmo com abreviações ou nomes incompletos (ex: "Luiz Silva" casa automaticamente com "Luiz da Silva").

### ✅ Chamada Inteligente (Smart Sync)
Ao marcar a falta de um aluno na chamada, o sistema **limpa automaticamente** todos os registros de produtividade (atividade, comportamento, dever feito, bônus). Isso garante que o professor não precise clicar cinco vezes para registrar uma ausência.

---

## O que o professor consegue fazer

**Cadastro de turmas e alunos**
- Importar turmas a partir de uma planilha `.xlsx` (Suporte a múltiplas abas/turmas na mesma planilha)
- Adicionar, trocar e remover alunos manualmente
- Fazer upload de fotos para o carômetro da turma (reconhecimento automático)

**Gestão de aulas**
- Criar aulas com data e título
- Fazer chamada com registro individualizado por aluno (presença, atividade, comportamento, dever feito, cópia do quadro, bônus e observações)
- Observações gerais da aula como diário do professor
- Visualizar histórico de aulas por turma

**Apoio a Estudantes com NEE**
- Identificar alunos com Necessidade Educacional Especial
- Visualização **destacada e acessível** durante a chamada
- Armazenamento local de laudos e relatórios em PDF por aluno

---

## Por que 100% Offline? 🚫🌐

Dados de alunos são sensíveis. O ClassRoot prioriza a **portabilidade e a privacidade**:
- **Zero Configuração:** Não precisa instalar bancos de dados (SQLite embutido).
- **Sem Nuvem:** Nenhum dado sai do computador do professor.
- **Portátil:** No Windows, o sistema roda como um executável único (`.exe`) que pode ser levado em um pendrive entre diferentes escolas.

> [!TIP]
> Embora o ClassRoot não dependa de internet, você pode copiar o arquivo `classroot.db` para o seu **Google Drive ou OneDrive** periodicamente como um backup de segurança. Assim, seus registros estarão salvos mesmo se algo acontecer com o seu computador.

---

## Estrutura do projeto

```
ClassRoot/
├── app.py              # aplicação principal Flask
├── db.py               # conexão e estrutura do banco
├── alunos.py           # rotas de gestão de alunos
├── import_logic.py     # importação via Excel
├── run_app.py          # inicialização da aplicação
├── GERAR_DIARIO_ESCOLAR.bat  # gera o executável no Windows
├── classroot.db        # banco de dados local (gerado automaticamente)
├── static/
│   ├── fotos_alunos/   # carômetro da turma
│   └── relatorios_nee/ # PDFs de laudos e relatórios
├── templates/          # interface HTML
└── exemplos/           # modelos de planilha para importação
```

---

## Como usar

### Para Professores (Windows):
O ClassRoot é um sistema portátil. Você pode baixar a versão pronta para uso (executável) através do link abaixo:

🚀 **[Download ClassRoot para Windows (Google Drive)](https://drive.google.com/drive/folders/1RU4moMHH5YsRSfCn8IV59LBVwneEpMBg?usp=sharing)**

> [!NOTE]
> Ao baixar, extraia o conteúdo do arquivo `.zip` para uma pasta no seu computador ou pendrive. O banco de dados é criado automaticamente na primeira execução. Um modelo de planilha para importação está disponível na pasta `exemplos/` aqui no GitHub.

> [!CAUTION]
> **Sobre as Imagens de Exemplo:** As fotos contidas na pasta `exemplos/` são de figuras públicas e foram coletadas de fontes públicas (como Wikipedia e buscas em rede). Elas servem exclusivamente para fins de demonstração técnica das funcionalidades de carômetro do projeto e não devem ser utilizadas para fins comerciais.

### Para Desenvolvedores:
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/classroot
cd classroot

# Instale as dependências
pip install -r requirements.txt

# Rode em modo desenvolvimento
python run_app.py
```

Para gerar um novo executável portátil no Windows, rode `GERAR_DIARIO_ESCOLAR.bat`.

---

## Contribuição e Licença

O ClassRoot foi construído intencionalmente simples. Sem frameworks pesados, sem dependências desnecessárias. É um esqueleto funcional.

Se você quiser construir em cima dele, algumas direções possíveis:

- Interface mais elaborada
- Versão web com autenticação
- Integração com diários eletrônicos
- App mobile
- Relatórios e dashboards com os dados registrados

Qualquer derivação precisa respeitar a licença **GPL v3**, mantendo o código aberto e acessível a quem o educador mais precisa: o aluno.

---

## Origem

O ClassRoot foi criado por um professor do Ensino Fundamental do Distrito Federal que queria resolver seus próprios problemas e acabou construindo algo que pode ajudar outros professores. 

Foi desenvolvido com assistência de IA para a implementação técnica, conduzido por quem conhece o problema de dentro.

---

## Licença

GPL v3 — veja o arquivo `LICENSE` para detalhes.
