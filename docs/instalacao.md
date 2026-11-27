# Instalação

O Prumo roda de duas formas: com o **Python** (código-fonte) ou pelo **executável** do Windows. As duas usam os mesmos templates e geram projetos idênticos.

## Pré-requisitos

| Item | Para quê | Obrigatório |
|---|---|---|
| Python 3.9 ou superior | Rodar o Prumo pelo código e executar os hooks dos projetos | Sim, se não usar o `.exe` (recomendado mesmo com o `.exe`) |
| Git | Repositório de cada projeto e detecção de mudanças pelos hooks | Recomendado |
| Claude Code | Tarefas com IA (`prumo claude`, skills, hooks) | Para as tarefas com IA |
| Navegador Edge ou Chrome | Janela da interface gráfica | Para a interface |
| mermaid-cli (`npm i -g @mermaid-js/mermaid-cli`) | Validação completa dos diagramas (`prumo validar --mmdc`) | Opcional |

## Opção 1: código-fonte (Python)

```powershell
git clone https://github.com/tombfarias/prumo C:\Prumo
cd C:\Prumo
python prumo.py --versao
```

No Windows, `prumo.bat` permite chamar só `prumo` quando a pasta está no PATH. No Linux e no macOS, use o script `./prumo`.

## Opção 2: executável (Windows)

1. Baixe `prumo.exe` e `prumo-app.exe` da página de *Releases* do repositório (ou gere-os: veja [Executável](executavel.md)).
2. Coloque os dois na pasta do Prumo (por exemplo `C:\Prumo`). A pasta `config\` é criada ao lado deles.
3. `prumo.exe --versao` no terminal; duplo clique em `prumo-app.exe` abre a interface.

O executável já contém os templates e a interface. Projetos criados em máquinas sem Python passam a rodar os hooks pelo próprio `prumo.exe` (`hooks_via: "prumo"`).

## PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File C:\Prumo\powershell\instalar.ps1 -AdicionarAoPath
```

O instalador adiciona `Import-Module ...\Prumo.psm1` ao seu perfil do PowerShell e, com `-AdicionarAoPath`, coloca a pasta do Prumo no PATH do usuário. Abra um novo terminal e teste:

```powershell
prumo --versao
Send-Claude "olá" -Simular
```

Se o PowerShell bloquear o módulo: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Claude Code

Instale pelo instalador oficial ou com `npm install -g @anthropic-ai/claude-code`, rode `claude` uma vez para entrar na sua conta e confirme com `claude --version`. O Prumo encontra o Claude pelo PATH; para outro caminho, defina a variável `PRUMO_CLAUDE`.

## Seus dados de freelancer

Copie `config\freelancer.exemplo.json` para `config\freelancer.json` e preencha nome, e-mail, valor da hora e contingência padrão. Esse arquivo não vai para o git. Veja [Configuração](configuracao.md).
