BrowserBridge MVP
BrowserBridge é um protótipo de extensão para Firefox que importa
automaticamente favoritos e histórico de navegadores baseados em Chromium
(começando por Google Chrome, Microsoft Edge e Brave).
A proposta do MVP é:
sincronização local;
sem conta;
sem servidor;
execução automática ao iniciar o Firefox;
importação incremental do histórico;
deduplicação básica;
preservação da estrutura de pastas dos favoritos.
Arquitetura
```text
Chrome / Edge / Brave
        │
        │ arquivos locais (Bookmarks + History SQLite)
        ▼
BrowserBridge Native Host (Python)
        │
        │ Firefox Native Messaging
        ▼
BrowserBridge Extension
        │
        ├── bookmarks API
        └── history API
```
Estrutura
```text
browserbridge-mvp/
├── extension/
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   ├── popup.css
│   ├── popup.js
│   ├── options.html
│   ├── options.css
│   ├── options.js
│   └── icons/icon.svg
├── native-host/
│   ├── bridge.py
│   ├── browserbridge.bat
│   ├── browserbridge-host
│   ├── install-windows.ps1
│   ├── install-linux.sh
│   ├── uninstall-windows.ps1
│   └── uninstall-linux.sh
└── tests/
    └── test_bridge.py
```
Requisitos
Firefox
Python 3
Chrome, Edge ou Brave instalado localmente
O host não possui dependências externas de Python.
Teste rápido do leitor
Na raiz do projeto:
```bash
python tests/test_bridge.py
```
Windows
Abra PowerShell dentro de `native-host`:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install-windows.ps1
```
O instalador cria o manifesto do Native Messaging e registra o host em:
```text
HKCU\Software\Mozilla\NativeMessagingHosts\site.felipeleal.browserbridge
```
Carregar a extensão temporariamente
Abra `about:debugging#/runtime/this-firefox`.
Clique em Carregar extensão temporária.
Selecione `extension/manifest.json`.
Clique no ícone BrowserBridge.
Clique em Sincronizar agora.
Linux / Fedora
Dentro de `native-host`:
```bash
chmod +x install-linux.sh
./install-linux.sh
```
Depois:
Abra `about:debugging#/runtime/this-firefox`.
Clique em Carregar extensão temporária.
Selecione `extension/manifest.json`.
Teste Detectar navegadores em Configurações.
Execute Sincronizar agora.
O que o MVP lê
Somente:
arquivo `Bookmarks`;
banco SQLite `History`.
Ele não lê:
senhas;
cookies;
tokens;
dados de preenchimento;
cartões;
sessões autenticadas.
Comportamento atual
Ao iniciar o Firefox, `background.js` chama o host nativo. O host detecta os
perfis locais, lê os dados e envia JSON de volta à extensão.
Os favoritos importados ficam agrupados em:
```text
BrowserBridge/
├── Google Chrome — Default/
└── Microsoft Edge — Default/
```
O histórico é importado preservando o horário de visita sempre que possível.
Próximas etapas
Testar em Windows e Fedora com perfis reais.
Melhorar a resolução da pasta raiz de favoritos.
Adicionar Vivaldi e Opera.
Implementar importação de abas abertas.
Criar instalador único do Native Host.
Adicionar logs e tela de diagnóstico.
Assinar/publicar a extensão no Mozilla Add-ons.
Criar testes de integração e tratamento de bancos Chromium com schemas diferentes.
