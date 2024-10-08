## REFERENCE:
https://en.wikipedia.org/wiki/JSON-RPC
https://microsoft.github.io/language-server-protocol/overviews/lsp/overview/
https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
https://medium.com/@malintha1996/understanding-the-language-server-protocol-5c0ba3ac83d2

## JSONRPC

- Protocol to call RPC (remote procedure call) using JSON. Can be thought as HTTP REST API but without HTTP as envelope (do not have HTTP url, HTTP method, HTTP headers).
- Server and client communicates by sending JSON across an established data stream (e.g.: TCP socket, STDIO pipe).
- An RPC (remote procedure call) can be either a **procedure** call (the request must answered by a response), or a **notification** call (the request does not need to be answered)
- Both procedure call or notification call can be sent from server to client or from client to server, e.g.: this sequence of communication is possible:
    - SERVER: CALL Method1(param1)
    - CLIENT: RETURN_FROM Method1
    - CLIENT: CALL Method2(param2)
    - SERVER: RETURN_FROM Method2
- Also, procedure call or notification call can be done asynchronously, e.g.: this sequence of communication is possible:
    - SERVER: CALL Method1(param1)
    - SERVER: CALL Method2(param2)
    - CLIENT: RETURN_FROM Method2
    - CLIENT: RETURN_FROM Method1
- The act of initiating procedure call or notification call is called **request**
- The act of returning result of a procedure call is called **response**

#### Procedure Call
- example: calling ```ConcatenateString("Hello","World")``` returns ```"HelloWorld"```
- request:
```json
{
  "jsonrpc": "2.0",
  "id": 101,
  "method": "ConcatenateString",
  "params": {
    "parameter1": "Hello",
    "parameter2": "World"
  }
}
```
- response:
```json
{
  "jsonrpc": "2.0",
  "id": 101,
  "result": "HelloWorld"
}
```
- or in case there's an error:
```json
{
  "jsonrpc": "2.0",
  "id": 101,
  "error": "string too long!"
}
```
- procedure call request **must** have "id" and "method"
    - "id" is used to identify which one is the return of which call
    - "method" is used to identify what method/function is being called
    - "params" is optional, may contain anything, e.g.: json object/array/string/int/boolean/null
- procedure call response **must** have "id" and ("result" or "error")

#### Notification Call
- example: notifying that user has clicked `button1`
- request:
```json
{
  "jsonrpc": "2.0",
  "method": "buttonClicked",
  "params": {
    "buttonId": "button1"
  }
}
```
- notification call request **must** have "method", and **must not** have "id"
    - "id" **must not** be present, since having id would means that it's a procedure call instead of notification call
    - "method" is used to identify what event/notification is happening
    - "params" is optional, may contain anything, e.g.: json object/array/string/int/boolean/null
- notification call does not require a response

#### Communicating JSONRPC Over Data Stream
- since JSONRPC must be communicated over data stream (e.g.: TCP socket), receiver must know the length of JSONRPC message
- alternatively, each JSONRPC message must be delimited with a delimiter (e.g.: line break or null bytes), but it might not be the best choice since some implementation may have 'prettified' JSON which have line breaks
- therefore, the actual message on data stream should include 'Content-Length' header to indicate JSONRPC body length, e.g.:
```
Content-Length: 38

{"id":2,"jsonrpc":"2.0","result":null}
``` 


## LSP (Language Server Protocol)
- LSP is an effort to support various programming language specific IDE capability (e.g.: code highlighting, diagnostic, linting, autocomplete, documentation) from various text editor/IDE by abstracting the capabilities as a service (client-server model)
- In short, instead of every editor/IDE implementing their highlighting/diagnostic/autocomplete/etc logic; which would only work in their own tools, LSP would put those logic in a server, so that each editor/IDE would be just a client
- In learning LSP protocol, reference links above may help

#### Sniffing LSP Traffic/Communication
- since the goal of this project is not to create a complete text editor, understanding of whole LSP protocol is not needed, instead example traffic of LSP communication is needed to just replicate "diagnostic" part of a LSP server implementation (e.g.: PHP intelephense)
- tools:
    - Linux PC (might be substituteable by Windows PC with WSL or just plain old git bash or cygwin, author has not tried it yet)
    - Sublime Text 3 (or any text editor that support LSP)
    - Node.js (required for running PHP intelephense LSP server)
    - Various GNU utilities (e.g.: bash, tee, cat, ps, grep)
- steps below

##### Finding LSP Process
1. open up text editor/IDE, configure LSP server and PHP LSP intelephense on said editor (look up for tutorial online if needed)
2. open a PHP project to confirm that PHP LSP intelephense is working (try to make an obviously wrong code, e.g.: syntax error, or calling undefined method)
3. run `ps aux | grep -i intelephense` or `ps -ef | grep -i intelephense` to try to find out what command is intelephense is running as
4. in this step, we found that the command is `/usr/bin/node /home/kristian/.cache/sublime-text/Package Storage/LSP-intelephense/22.7.0/language-server/node_modules/intelephense/lib/intelephense.js --stdio`
5. from PHP LSP intelephense home page, we found out that it's installable as NPM package by using `npm -g install intelephense`
6. after getting the process, the arguments, and the file location, we can inspect the server
7. run `cd '/home/kristian/.cache/sublime-text/Package Storage/LSP-intelephense/22.7.0/language-server/node_modules/intelephense/lib/'` then simple `cat` or `file` command on `intelephense.js` reveals that it is a simple node.js file, minified
8. running `node intelephense.js` without arguments reveals that accepted command line arguments are `--stdio` or `--socket={port-number}` or `--node-ipc`; since LSP server needs to communicate with its client, and that sublime text is using `--stdio` parameter, this reveals that sublime text's communication with intelephense is using stdio (stdin and stdout)
9. (optional) for development purpose, or for ease of deployment, we install "development" version of intelephense with docker, built from this dockerfile (or just use prebuilt one from https://hub.docker.com/r/krstian/intelephense-node22-alpine )
```dockerfile
FROM node:22-alpine
RUN npm i intelephense -g
#ENTRYPOINT ["intelephense", "--stdio"]
#ENTRYPOINT ["sh"]
ENTRYPOINT ["sleep", "99999999999"]
```

##### Attempt at Sniffing on LSP Communication
1. from previous step we also got the PID of intelephense server, in order to sniff STDIO of a certain process, we used this command: `strace -p{PID} -s9999 -e write/read`, then we observe the output, reference: https://unix.stackexchange.com/a/58601, example output:
```
read(0, "Content-Length: 265\r\n\r\n{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/didOpen\",\"params\":{\"textDocument\":{\"uri\":\"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php\",\"languageId\":\"php\",\"version\":0,\"text\":\"<?php echo myfunc($x);\"}}}", 65536) = 288

write(1, "{\"jsonrpc\":\"2.0\",\"method\":\"textDocument/publishDiagnostics\",\"params\":{\"uri\":\"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php\",\"diagnostics\":[{\"range\":{\"start\":{\"line\":0,\"character\":11},\"end\":{\"line\":0,\"character\":17}},\"message\":\"Undefined function 'myfunc'.\",\"severity\":1,\"code\":\"P1010\",\"source\":\"intelephense\"}]}}", 383) = 383
```
2. this attempt confirms that the communication of this process is obeying LSP protocol and is using JSONRPC
3. attempt to sniff initialization phase of LSP communication is not possible using this method; because when the process has already started, the initialization JSONRPC message has already been lost, therefore we need to sniff from the start
4. since intelephense is just a node.js script, we can modify the node.js script so it intercepts and logs its stdio (stdin and stdout) somewhere

##### Modify Intelephense.js to Log STDIO
1. save original `intelephense.js` to `intelephense.js.original` (we need to call this file later)
2. change `intelephense.js` content to lines below, ref: https://stackoverflow.com/a/55044587
```js
const { spawn } = require('child_process')
const shell = spawn('/home/kristian/bin/sniff-intelephense',[], { stdio: 'inherit' })
// shell.on('close',(code)=>{console.log('[shell] terminated :',code)})
```
3. we redirect the STDIO of `intelephense.js` to any executable `/home/kristian/bin/sniff-intelephense` (it can be bash script, php script, compiled binary, or anything)
4. we need to write `/home/kristian/bin/sniff-intelephense` executable to log its stdin and stdout, and also pipe them to original `intelephense.js` file, in this case, author decided to write it in bash:
```bash
#!/bin/bash
cat - | tee -a /tmp/log-lsp-in | tee -a /tmp/log-lsp-inout | /usr/bin/node '/home/kristian/.cache/sublime-text/Package Storage/LSP-intelephense/22.7.0/language-server/node_modules/intelephense/lib/intelephense.js.original' --stdio 2>&1 | tee -a /tmp/log-lsp-out | tee -a /tmp/log-lsp-inout
```
5. example output of `/tmp/log-lsp-in`, `/tmp/log-lsp-out`, and `/tmp/log-lsp-inout`
traffic in (from client to server)
```json
Content-Length: 4768

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":54070,"clientInfo":{"name":"Sublime Text LSP","version":"2.2.0"},"rootUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","rootPath":"/home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","workspaceFolders":[{"name":"api","uri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"name":"voices","uri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}],"capabilities":{"general":{"regularExpressions":{"engine":"ECMAScript"},"markdown":{"parser":"Python-Markdown","version":"3.2.2"}},"textDocument":{"synchronization":{"dynamicRegistration":true,"didSave":true,"willSave":true,"willSaveWaitUntil":true},"hover":{"dynamicRegistration":true,"contentFormat":["markdown","plaintext"]},"completion":{"dynamicRegistration":true,"completionItem":{"snippetSupport":true,"deprecatedSupport":true,"documentationFormat":["markdown","plaintext"],"tagSupport":{"valueSet":[1]},"resolveSupport":{"properties":["detail","documentation","additionalTextEdits"]},"insertReplaceSupport":true,"insertTextModeSupport":{"valueSet":[2]},"labelDetailsSupport":true},"completionItemKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]},"insertTextMode":2,"completionList":{"itemDefaults":["editRange","insertTextFormat","data"]}},"signatureHelp":{"dynamicRegistration":true,"contextSupport":true,"signatureInformation":{"activeParameterSupport":true,"documentationFormat":["markdown","plaintext"],"parameterInformation":{"labelOffsetSupport":true}}},"references":{"dynamicRegistration":true},"documentHighlight":{"dynamicRegistration":true},"documentSymbol":{"dynamicRegistration":true,"hierarchicalDocumentSymbolSupport":true,"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"documentLink":{"dynamicRegistration":true,"tooltipSupport":true},"formatting":{"dynamicRegistration":true},"rangeFormatting":{"dynamicRegistration":true,"rangesSupport":true},"declaration":{"dynamicRegistration":true,"linkSupport":true},"definition":{"dynamicRegistration":true,"linkSupport":true},"typeDefinition":{"dynamicRegistration":true,"linkSupport":true},"implementation":{"dynamicRegistration":true,"linkSupport":true},"codeAction":{"dynamicRegistration":true,"codeActionLiteralSupport":{"codeActionKind":{"valueSet":["quickfix","refactor","refactor.extract","refactor.inline","refactor.rewrite","source.fixAll","source.organizeImports"]}},"dataSupport":true,"isPreferredSupport":true,"resolveSupport":{"properties":["edit"]}},"rename":{"dynamicRegistration":true,"prepareSupport":true,"prepareSupportDefaultBehavior":1},"colorProvider":{"dynamicRegistration":true},"publishDiagnostics":{"relatedInformation":true,"tagSupport":{"valueSet":[1,2]},"versionSupport":true,"codeDescriptionSupport":true,"dataSupport":true},"diagnostic":{"dynamicRegistration":true,"relatedDocumentSupport":true},"selectionRange":{"dynamicRegistration":true},"foldingRange":{"dynamicRegistration":true,"foldingRangeKind":{"valueSet":["comment","imports","region"]}},"codeLens":{"dynamicRegistration":true},"inlayHint":{"dynamicRegistration":true,"resolveSupport":{"properties":["textEdits","label.command"]}},"semanticTokens":{"dynamicRegistration":true,"requests":{"range":true,"full":{"delta":true}},"tokenTypes":["namespace","type","class","enum","interface","struct","typeParameter","parameter","variable","property","enumMember","event","function","method","macro","keyword","modifier","comment","string","number","regexp","operator","decorator"],"tokenModifiers":["declaration","definition","readonly","static","deprecated","abstract","async","modification","documentation","defaultLibrary"],"formats":["relative"],"overlappingTokenSupport":false,"multilineTokenSupport":true,"augmentsSyntaxTokens":true},"callHierarchy":{"dynamicRegistration":true},"typeHierarchy":{"dynamicRegistration":true}},"workspace":{"applyEdit":true,"didChangeConfiguration":{"dynamicRegistration":true},"executeCommand":{},"workspaceEdit":{"documentChanges":true,"failureHandling":"abort"},"workspaceFolders":true,"symbol":{"dynamicRegistration":true,"resolveSupport":{"properties":["location.range"]},"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"configuration":true,"codeLens":{"refreshSupport":true},"inlayHint":{"refreshSupport":true},"semanticTokens":{"refreshSupport":true},"diagnostics":{"refreshSupport":true}},"window":{"showDocument":{"support":true},"showMessage":{"messageActionItem":{"additionalPropertiesSupport":true}},"workDoneProgress":true}},"initializationOptions":{"clearCache":false}}}Content-Length: 52

{"jsonrpc":"2.0","method":"initialized","params":{}}Content-Length: 156

{"jsonrpc":"2.0","method":"workspace/didChangeConfiguration","params":{"settings":{"statusText":"{% if server_version %}v{{ server_version }}{% endif %}"}}}Content-Length: 267

{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","languageId":"php","version":0,"text":"<?php echo -eee-33d($x);"}}}Content-Length: 50

{"id":0,"jsonrpc":"2.0","result":[null,null,null]}Content-Length: 38

{"id":1,"jsonrpc":"2.0","result":null}Content-Length: 38

{"id":2,"jsonrpc":"2.0","result":null}
```
traffic out (from server to client)
```json
Content-Length: 111

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialising intelephense 1.12.6"}}Content-Length: 125

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Reading state from /tmp/intelephense/36632feb."}}Content-Length: 99

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialised in 18 ms"}}Content-Length: 794

{"jsonrpc":"2.0","id":1,"result":{"capabilities":{"textDocumentSync":2,"documentSymbolProvider":true,"workspaceSymbolProvider":true,"completionProvider":{"triggerCharacters":["$",">",":","\\","/","'","\"","*",".","<"],"resolveProvider":true},"signatureHelpProvider":{"triggerCharacters":["(",",",":"]},"definitionProvider":true,"documentFormattingProvider":false,"documentRangeFormattingProvider":false,"referencesProvider":true,"hoverProvider":true,"documentHighlightProvider":true,"foldingRangeProvider":false,"implementationProvider":false,"declarationProvider":false,"workspace":{"workspaceFolders":{"supported":true,"changeNotifications":true}},"renameProvider":false,"typeDefinitionProvider":false,"selectionRangeProvider":false,"codeActionProvider":false,"typeHierarchyProvider":false}}}Content-Length: 319

{"jsonrpc":"2.0","id":0,"method":"workspace/configuration","params":{"items":[{"section":"intelephense"},{"section":"intelephense","scopeUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"section":"intelephense","scopeUri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}]}}Content-Length: 487

{"jsonrpc":"2.0","id":1,"method":"client/registerCapability","params":{"registrations":[{"id":"f5b46eee-8467-47ba-a6c0-e226a6cfd5fa","method":"textDocument/formatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}},{"id":"361e6653-74ce-4ee6-90f0-f8325ec4f9b7","method":"textDocument/rangeFormatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}}]}}Content-Length: 225

{"jsonrpc":"2.0","id":2,"method":"client/registerCapability","params":{"registrations":[{"id":"0cc7aef5-5a5e-4aa0-8cfb-656b3861d3ce","method":"workspace/didChangeConfiguration","registerOptions":{"section":"intelephense"}}]}}Content-Length: 243

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/.cache/sublime-text/Package%20Storage/LSP-intelephense/22.8.0/language-server/node_modules/intelephense/lib/stub for files to index."}}Content-Length: 181

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api for files to index."}}Content-Length: 387

{"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","diagnostics":[{"range":{"start":{"line":0,"character":18},"end":{"line":0,"character":19}},"message":"Unexpected 'Name'. Expected ','.","severity":1,"code":"P1001","source":"intelephense"}]}}
```
traffic both (merged interleaved):
```json

Content-Length: 4768

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":54070,"clientInfo":{"name":"Sublime Text LSP","version":"2.2.0"},"rootUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","rootPath":"/home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","workspaceFolders":[{"name":"api","uri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"name":"voices","uri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}],"capabilities":{"general":{"regularExpressions":{"engine":"ECMAScript"},"markdown":{"parser":"Python-Markdown","version":"3.2.2"}},"textDocument":{"synchronization":{"dynamicRegistration":true,"didSave":true,"willSave":true,"willSaveWaitUntil":true},"hover":{"dynamicRegistration":true,"contentFormat":["markdown","plaintext"]},"completion":{"dynamicRegistration":true,"completionItem":{"snippetSupport":true,"deprecatedSupport":true,"documentationFormat":["markdown","plaintext"],"tagSupport":{"valueSet":[1]},"resolveSupport":{"properties":["detail","documentation","additionalTextEdits"]},"insertReplaceSupport":true,"insertTextModeSupport":{"valueSet":[2]},"labelDetailsSupport":true},"completionItemKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]},"insertTextMode":2,"completionList":{"itemDefaults":["editRange","insertTextFormat","data"]}},"signatureHelp":{"dynamicRegistration":true,"contextSupport":true,"signatureInformation":{"activeParameterSupport":true,"documentationFormat":["markdown","plaintext"],"parameterInformation":{"labelOffsetSupport":true}}},"references":{"dynamicRegistration":true},"documentHighlight":{"dynamicRegistration":true},"documentSymbol":{"dynamicRegistration":true,"hierarchicalDocumentSymbolSupport":true,"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"documentLink":{"dynamicRegistration":true,"tooltipSupport":true},"formatting":{"dynamicRegistration":true},"rangeFormatting":{"dynamicRegistration":true,"rangesSupport":true},"declaration":{"dynamicRegistration":true,"linkSupport":true},"definition":{"dynamicRegistration":true,"linkSupport":true},"typeDefinition":{"dynamicRegistration":true,"linkSupport":true},"implementation":{"dynamicRegistration":true,"linkSupport":true},"codeAction":{"dynamicRegistration":true,"codeActionLiteralSupport":{"codeActionKind":{"valueSet":["quickfix","refactor","refactor.extract","refactor.inline","refactor.rewrite","source.fixAll","source.organizeImports"]}},"dataSupport":true,"isPreferredSupport":true,"resolveSupport":{"properties":["edit"]}},"rename":{"dynamicRegistration":true,"prepareSupport":true,"prepareSupportDefaultBehavior":1},"colorProvider":{"dynamicRegistration":true},"publishDiagnostics":{"relatedInformation":true,"tagSupport":{"valueSet":[1,2]},"versionSupport":true,"codeDescriptionSupport":true,"dataSupport":true},"diagnostic":{"dynamicRegistration":true,"relatedDocumentSupport":true},"selectionRange":{"dynamicRegistration":true},"foldingRange":{"dynamicRegistration":true,"foldingRangeKind":{"valueSet":["comment","imports","region"]}},"codeLens":{"dynamicRegistration":true},"inlayHint":{"dynamicRegistration":true,"resolveSupport":{"properties":["textEdits","label.command"]}},"semanticTokens":{"dynamicRegistration":true,"requests":{"range":true,"full":{"delta":true}},"tokenTypes":["namespace","type","class","enum","interface","struct","typeParameter","parameter","variable","property","enumMember","event","function","method","macro","keyword","modifier","comment","string","number","regexp","operator","decorator"],"tokenModifiers":["declaration","definition","readonly","static","deprecated","abstract","async","modification","documentation","defaultLibrary"],"formats":["relative"],"overlappingTokenSupport":false,"multilineTokenSupport":true,"augmentsSyntaxTokens":true},"callHierarchy":{"dynamicRegistration":true},"typeHierarchy":{"dynamicRegistration":true}},"workspace":{"applyEdit":true,"didChangeConfiguration":{"dynamicRegistration":true},"executeCommand":{},"workspaceEdit":{"documentChanges":true,"failureHandling":"abort"},"workspaceFolders":true,"symbol":{"dynamicRegistration":true,"resolveSupport":{"properties":["location.range"]},"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"configuration":true,"codeLens":{"refreshSupport":true},"inlayHint":{"refreshSupport":true},"semanticTokens":{"refreshSupport":true},"diagnostics":{"refreshSupport":true}},"window":{"showDocument":{"support":true},"showMessage":{"messageActionItem":{"additionalPropertiesSupport":true}},"workDoneProgress":true}},"initializationOptions":{"clearCache":false}}}Content-Length: 111

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialising intelephense 1.12.6"}}Content-Length: 125

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Reading state from /tmp/intelephense/36632feb."}}Content-Length: 99

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialised in 18 ms"}}Content-Length: 794

{"jsonrpc":"2.0","id":1,"result":{"capabilities":{"textDocumentSync":2,"documentSymbolProvider":true,"workspaceSymbolProvider":true,"completionProvider":{"triggerCharacters":["$",">",":","\\","/","'","\"","*",".","<"],"resolveProvider":true},"signatureHelpProvider":{"triggerCharacters":["(",",",":"]},"definitionProvider":true,"documentFormattingProvider":false,"documentRangeFormattingProvider":false,"referencesProvider":true,"hoverProvider":true,"documentHighlightProvider":true,"foldingRangeProvider":false,"implementationProvider":false,"declarationProvider":false,"workspace":{"workspaceFolders":{"supported":true,"changeNotifications":true}},"renameProvider":false,"typeDefinitionProvider":false,"selectionRangeProvider":false,"codeActionProvider":false,"typeHierarchyProvider":false}}}Content-Length: 52

{"jsonrpc":"2.0","method":"initialized","params":{}}Content-Length: 156

{"jsonrpc":"2.0","method":"workspace/didChangeConfiguration","params":{"settings":{"statusText":"{% if server_version %}v{{ server_version }}{% endif %}"}}}Content-Length: 319

{"jsonrpc":"2.0","id":0,"method":"workspace/configuration","params":{"items":[{"section":"intelephense"},{"section":"intelephense","scopeUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"section":"intelephense","scopeUri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}]}}Content-Length: 267

{"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","languageId":"php","version":0,"text":"<?php echo -eee-33d($x);"}}}Content-Length: 50

{"id":0,"jsonrpc":"2.0","result":[null,null,null]}Content-Length: 487

{"jsonrpc":"2.0","id":1,"method":"client/registerCapability","params":{"registrations":[{"id":"f5b46eee-8467-47ba-a6c0-e226a6cfd5fa","method":"textDocument/formatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}},{"id":"361e6653-74ce-4ee6-90f0-f8325ec4f9b7","method":"textDocument/rangeFormatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}}]}}Content-Length: 225

{"jsonrpc":"2.0","id":2,"method":"client/registerCapability","params":{"registrations":[{"id":"0cc7aef5-5a5e-4aa0-8cfb-656b3861d3ce","method":"workspace/didChangeConfiguration","registerOptions":{"section":"intelephense"}}]}}Content-Length: 38

{"id":1,"jsonrpc":"2.0","result":null}Content-Length: 38

{"id":2,"jsonrpc":"2.0","result":null}Content-Length: 243

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/.cache/sublime-text/Package%20Storage/LSP-intelephense/22.8.0/language-server/node_modules/intelephense/lib/stub for files to index."}}Content-Length: 181

{"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api for files to index."}}Content-Length: 387

{"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","diagnostics":[{"range":{"start":{"line":0,"character":18},"end":{"line":0,"character":19}},"message":"Unexpected 'Name'. Expected ','.","severity":1,"code":"P1001","source":"intelephense"}]}}
```

##### Annotating Output
1. with such output, we can annotate the output to understand them better
```json
// this is initialization phase
CLIENT
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":54070,"clientInfo":{"name":"Sublime Text LSP","version":"2.2.0"},"rootUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","rootPath":"/home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","workspaceFolders":[{"name":"api","uri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"name":"voices","uri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}],"capabilities":{"general":{"regularExpressions":{"engine":"ECMAScript"},"markdown":{"parser":"Python-Markdown","version":"3.2.2"}},"textDocument":{"synchronization":{"dynamicRegistration":true,"didSave":true,"willSave":true,"willSaveWaitUntil":true},"hover":{"dynamicRegistration":true,"contentFormat":["markdown","plaintext"]},"completion":{"dynamicRegistration":true,"completionItem":{"snippetSupport":true,"deprecatedSupport":true,"documentationFormat":["markdown","plaintext"],"tagSupport":{"valueSet":[1]},"resolveSupport":{"properties":["detail","documentation","additionalTextEdits"]},"insertReplaceSupport":true,"insertTextModeSupport":{"valueSet":[2]},"labelDetailsSupport":true},"completionItemKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]},"insertTextMode":2,"completionList":{"itemDefaults":["editRange","insertTextFormat","data"]}},"signatureHelp":{"dynamicRegistration":true,"contextSupport":true,"signatureInformation":{"activeParameterSupport":true,"documentationFormat":["markdown","plaintext"],"parameterInformation":{"labelOffsetSupport":true}}},"references":{"dynamicRegistration":true},"documentHighlight":{"dynamicRegistration":true},"documentSymbol":{"dynamicRegistration":true,"hierarchicalDocumentSymbolSupport":true,"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"documentLink":{"dynamicRegistration":true,"tooltipSupport":true},"formatting":{"dynamicRegistration":true},"rangeFormatting":{"dynamicRegistration":true,"rangesSupport":true},"declaration":{"dynamicRegistration":true,"linkSupport":true},"definition":{"dynamicRegistration":true,"linkSupport":true},"typeDefinition":{"dynamicRegistration":true,"linkSupport":true},"implementation":{"dynamicRegistration":true,"linkSupport":true},"codeAction":{"dynamicRegistration":true,"codeActionLiteralSupport":{"codeActionKind":{"valueSet":["quickfix","refactor","refactor.extract","refactor.inline","refactor.rewrite","source.fixAll","source.organizeImports"]}},"dataSupport":true,"isPreferredSupport":true,"resolveSupport":{"properties":["edit"]}},"rename":{"dynamicRegistration":true,"prepareSupport":true,"prepareSupportDefaultBehavior":1},"colorProvider":{"dynamicRegistration":true},"publishDiagnostics":{"relatedInformation":true,"tagSupport":{"valueSet":[1,2]},"versionSupport":true,"codeDescriptionSupport":true,"dataSupport":true},"diagnostic":{"dynamicRegistration":true,"relatedDocumentSupport":true},"selectionRange":{"dynamicRegistration":true},"foldingRange":{"dynamicRegistration":true,"foldingRangeKind":{"valueSet":["comment","imports","region"]}},"codeLens":{"dynamicRegistration":true},"inlayHint":{"dynamicRegistration":true,"resolveSupport":{"properties":["textEdits","label.command"]}},"semanticTokens":{"dynamicRegistration":true,"requests":{"range":true,"full":{"delta":true}},"tokenTypes":["namespace","type","class","enum","interface","struct","typeParameter","parameter","variable","property","enumMember","event","function","method","macro","keyword","modifier","comment","string","number","regexp","operator","decorator"],"tokenModifiers":["declaration","definition","readonly","static","deprecated","abstract","async","modification","documentation","defaultLibrary"],"formats":["relative"],"overlappingTokenSupport":false,"multilineTokenSupport":true,"augmentsSyntaxTokens":true},"callHierarchy":{"dynamicRegistration":true},"typeHierarchy":{"dynamicRegistration":true}},"workspace":{"applyEdit":true,"didChangeConfiguration":{"dynamicRegistration":true},"executeCommand":{},"workspaceEdit":{"documentChanges":true,"failureHandling":"abort"},"workspaceFolders":true,"symbol":{"dynamicRegistration":true,"resolveSupport":{"properties":["location.range"]},"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"configuration":true,"codeLens":{"refreshSupport":true},"inlayHint":{"refreshSupport":true},"semanticTokens":{"refreshSupport":true},"diagnostics":{"refreshSupport":true}},"window":{"showDocument":{"support":true},"showMessage":{"messageActionItem":{"additionalPropertiesSupport":true}},"workDoneProgress":true}},"initializationOptions":{"clearCache":false}}}
SERVER
    {"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialising intelephense 1.12.6"}}
SERVER
    {"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Reading state from /tmp/intelephense/36632feb."}}
SERVER
    {"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Initialised in 18 ms"}}


// this is server announcing its capabilities (response of client's initialization request)    
SERVER
    {"jsonrpc":"2.0","id":1,"result":{"capabilities":{"textDocumentSync":2,"documentSymbolProvider":true,"workspaceSymbolProvider":true,"completionProvider":{"triggerCharacters":["$",">",":","\\","/","'","\"","*",".","<"],"resolveProvider":true},"signatureHelpProvider":{"triggerCharacters":["(",",",":"]},"definitionProvider":true,"documentFormattingProvider":false,"documentRangeFormattingProvider":false,"referencesProvider":true,"hoverProvider":true,"documentHighlightProvider":true,"foldingRangeProvider":false,"implementationProvider":false,"declarationProvider":false,"workspace":{"workspaceFolders":{"supported":true,"changeNotifications":true}},"renameProvider":false,"typeDefinitionProvider":false,"selectionRangeProvider":false,"codeActionProvider":false,"typeHierarchyProvider":false}}}
CLIENT
    {"jsonrpc":"2.0","method":"initialized","params":{}}


// this one is optional: client notify server that a configuration in client side has changed, the change is also trivial (just status text)
CLIENT
    {"jsonrpc":"2.0","method":"workspace/didChangeConfiguration","params":{"settings":{"statusText":"{% if server_version %}v{{ server_version }}{% endif %}"}}}
SERVER
    {"jsonrpc":"2.0","id":0,"method":"workspace/configuration","params":{"items":[{"section":"intelephense"},{"section":"intelephense","scopeUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"section":"intelephense","scopeUri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}]}}

// client notify server that it's opening a document
CLIENT
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","languageId":"php","version":0,"text":"<?php echo -eee-33d($x);"}}}
CLIENT
    {"id":0,"jsonrpc":"2.0","result":[null,null,null]}
SERVER
    {"jsonrpc":"2.0","id":1,"method":"client/registerCapability","params":{"registrations":[{"id":"f5b46eee-8467-47ba-a6c0-e226a6cfd5fa","method":"textDocument/formatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}},{"id":"361e6653-74ce-4ee6-90f0-f8325ec4f9b7","method":"textDocument/rangeFormatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}}]}}Content-Length: 225
SERVER
    {"jsonrpc":"2.0","id":2,"method":"client/registerCapability","params":{"registrations":[{"id":"0cc7aef5-5a5e-4aa0-8cfb-656b3861d3ce","method":"workspace/didChangeConfiguration","registerOptions":{"section":"intelephense"}}]}}
CLIENT
    {"id":1,"jsonrpc":"2.0","result":null}
CLIENT
    {"id":2,"jsonrpc":"2.0","result":null}
SERVER
    {"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/.cache/sublime-text/Package%20Storage/LSP-intelephense/22.8.0/language-server/node_modules/intelephense/lib/stub for files to index."}}
SERVER
    {"jsonrpc":"2.0","method":"window/logMessage","params":{"type":3,"message":"Searching file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api for files to index."}}Content-Length: 387

// server notify client about the result of diagnostics of opened documents
SERVER
    {"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","diagnostics":[{"range":{"start":{"line":0,"character":18},"end":{"line":0,"character":19}},"message":"Unexpected 'Name'. Expected ','.","severity":1,"code":"P1001","source":"intelephense"}]}}
```
2. we can further remove unnecesssary calls and group/pair each call by its id
```json
// initialization phase
// initialization request (client to server)
CLIENT
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":54070,"clientInfo":{"name":"Sublime Text LSP","version":"2.2.0"},"rootUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","rootPath":"/home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api","workspaceFolders":[{"name":"api","uri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"name":"voices","uri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}],"capabilities":{"general":{"regularExpressions":{"engine":"ECMAScript"},"markdown":{"parser":"Python-Markdown","version":"3.2.2"}},"textDocument":{"synchronization":{"dynamicRegistration":true,"didSave":true,"willSave":true,"willSaveWaitUntil":true},"hover":{"dynamicRegistration":true,"contentFormat":["markdown","plaintext"]},"completion":{"dynamicRegistration":true,"completionItem":{"snippetSupport":true,"deprecatedSupport":true,"documentationFormat":["markdown","plaintext"],"tagSupport":{"valueSet":[1]},"resolveSupport":{"properties":["detail","documentation","additionalTextEdits"]},"insertReplaceSupport":true,"insertTextModeSupport":{"valueSet":[2]},"labelDetailsSupport":true},"completionItemKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25]},"insertTextMode":2,"completionList":{"itemDefaults":["editRange","insertTextFormat","data"]}},"signatureHelp":{"dynamicRegistration":true,"contextSupport":true,"signatureInformation":{"activeParameterSupport":true,"documentationFormat":["markdown","plaintext"],"parameterInformation":{"labelOffsetSupport":true}}},"references":{"dynamicRegistration":true},"documentHighlight":{"dynamicRegistration":true},"documentSymbol":{"dynamicRegistration":true,"hierarchicalDocumentSymbolSupport":true,"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"documentLink":{"dynamicRegistration":true,"tooltipSupport":true},"formatting":{"dynamicRegistration":true},"rangeFormatting":{"dynamicRegistration":true,"rangesSupport":true},"declaration":{"dynamicRegistration":true,"linkSupport":true},"definition":{"dynamicRegistration":true,"linkSupport":true},"typeDefinition":{"dynamicRegistration":true,"linkSupport":true},"implementation":{"dynamicRegistration":true,"linkSupport":true},"codeAction":{"dynamicRegistration":true,"codeActionLiteralSupport":{"codeActionKind":{"valueSet":["quickfix","refactor","refactor.extract","refactor.inline","refactor.rewrite","source.fixAll","source.organizeImports"]}},"dataSupport":true,"isPreferredSupport":true,"resolveSupport":{"properties":["edit"]}},"rename":{"dynamicRegistration":true,"prepareSupport":true,"prepareSupportDefaultBehavior":1},"colorProvider":{"dynamicRegistration":true},"publishDiagnostics":{"relatedInformation":true,"tagSupport":{"valueSet":[1,2]},"versionSupport":true,"codeDescriptionSupport":true,"dataSupport":true},"diagnostic":{"dynamicRegistration":true,"relatedDocumentSupport":true},"selectionRange":{"dynamicRegistration":true},"foldingRange":{"dynamicRegistration":true,"foldingRangeKind":{"valueSet":["comment","imports","region"]}},"codeLens":{"dynamicRegistration":true},"inlayHint":{"dynamicRegistration":true,"resolveSupport":{"properties":["textEdits","label.command"]}},"semanticTokens":{"dynamicRegistration":true,"requests":{"range":true,"full":{"delta":true}},"tokenTypes":["namespace","type","class","enum","interface","struct","typeParameter","parameter","variable","property","enumMember","event","function","method","macro","keyword","modifier","comment","string","number","regexp","operator","decorator"],"tokenModifiers":["declaration","definition","readonly","static","deprecated","abstract","async","modification","documentation","defaultLibrary"],"formats":["relative"],"overlappingTokenSupport":false,"multilineTokenSupport":true,"augmentsSyntaxTokens":true},"callHierarchy":{"dynamicRegistration":true},"typeHierarchy":{"dynamicRegistration":true}},"workspace":{"applyEdit":true,"didChangeConfiguration":{"dynamicRegistration":true},"executeCommand":{},"workspaceEdit":{"documentChanges":true,"failureHandling":"abort"},"workspaceFolders":true,"symbol":{"dynamicRegistration":true,"resolveSupport":{"properties":["location.range"]},"symbolKind":{"valueSet":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]},"tagSupport":{"valueSet":[1]}},"configuration":true,"codeLens":{"refreshSupport":true},"inlayHint":{"refreshSupport":true},"semanticTokens":{"refreshSupport":true},"diagnostics":{"refreshSupport":true}},"window":{"showDocument":{"support":true},"showMessage":{"messageActionItem":{"additionalPropertiesSupport":true}},"workDoneProgress":true}},"initializationOptions":{"clearCache":false}}}
// initialization response (server to client)
SERVER
    {"jsonrpc":"2.0","id":1,"result":{"capabilities":{"textDocumentSync":2,"documentSymbolProvider":true,"workspaceSymbolProvider":true,"completionProvider":{"triggerCharacters":["$",">",":","\\","/","'","\"","*",".","<"],"resolveProvider":true},"signatureHelpProvider":{"triggerCharacters":["(",",",":"]},"definitionProvider":true,"documentFormattingProvider":false,"documentRangeFormattingProvider":false,"referencesProvider":true,"hoverProvider":true,"documentHighlightProvider":true,"foldingRangeProvider":false,"implementationProvider":false,"declarationProvider":false,"workspace":{"workspaceFolders":{"supported":true,"changeNotifications":true}},"renameProvider":false,"typeDefinitionProvider":false,"selectionRangeProvider":false,"codeActionProvider":false,"typeHierarchyProvider":false}}}
// initialized notification (must be sent, specified by protocol)
CLIENT
    {"jsonrpc":"2.0","method":"initialized","params":{}}


// this one is optional: client notify server that a configuration in client side has changed, the change is also trivial (just status text)
CLIENT
    {"jsonrpc":"2.0","method":"workspace/didChangeConfiguration","params":{"settings":{"statusText":"{% if server_version %}v{{ server_version }}{% endif %}"}}}
SERVER
    {"jsonrpc":"2.0","id":0,"method":"workspace/configuration","params":{"items":[{"section":"intelephense"},{"section":"intelephense","scopeUri":"file:///home/kristian/mnt/dev239/var/www/html/neowebservice_kristian/api"},{"section":"intelephense","scopeUri":"file:///home/kristian/tools/dahua/dokumentasi-dahua/voices"}]}}
CLIENT
    {"id":0,"jsonrpc":"2.0","result":[null,null,null]}

// client notify server that it's opening a document
CLIENT
    {"jsonrpc":"2.0","method":"textDocument/didOpen","params":{"textDocument":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","languageId":"php","version":0,"text":"<?php echo -eee-33d($x);"}}}

// unknown procedure call
SERVER
    {"jsonrpc":"2.0","id":1,"method":"client/registerCapability","params":{"registrations":[{"id":"f5b46eee-8467-47ba-a6c0-e226a6cfd5fa","method":"textDocument/formatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}},{"id":"361e6653-74ce-4ee6-90f0-f8325ec4f9b7","method":"textDocument/rangeFormatting","registerOptions":{"documentSelector":[{"language":"php","scheme":"file"},{"language":"php","scheme":"untitled"}]}}]}}
CLIENT
    {"id":1,"jsonrpc":"2.0","result":null}

// unknown procedure call
SERVER
    {"jsonrpc":"2.0","id":2,"method":"client/registerCapability","params":{"registrations":[{"id":"0cc7aef5-5a5e-4aa0-8cfb-656b3861d3ce","method":"workspace/didChangeConfiguration","registerOptions":{"section":"intelephense"}}]}}
CLIENT
    {"id":2,"jsonrpc":"2.0","result":null}

// server notify client about the result of diagnostics of opened documents
SERVER
    {"jsonrpc":"2.0","method":"textDocument/publishDiagnostics","params":{"uri":"file:///home/kristian/mnt/dev239/home/kristian/docker-node-alpine-intelephense/docker_volumes/home_kristian/test.php","diagnostics":[{"range":{"start":{"line":0,"character":18},"end":{"line":0,"character":19}},"message":"Unexpected 'Name'. Expected ','.","severity":1,"code":"P1001","source":"intelephense"}]}}
```
