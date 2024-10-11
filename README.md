# LSP Diagnostic Command Line Client

Language server (LSP) [spec](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) is used to provide various feature for text editors/IDEs (e.g.: VSCode). Example of LSP features including showing diagnostic (possible error/warning/notice, like unused variable, undefined variable, etc), code highlighting, autocomple, etc. 

This project is aimed to display diagnostic from LSP language server from command line instead of a full text editor. Therefore this project can be used to integrate LSP diagnostic inside a CI/CD pipeline (e.g.: fail a build if a diagnostic above certain severity is encountered in the build process)

This project is made for `php` and `intelephense`, but should also work for other languages. Getting diagnostic is done by waiting for `textDocument/publishDiagnostics` notification from LSP language server. 

### Requirements
- Python3 with standard library (socket, json, subprocess, os, glob, sys, hashlib)
- Tested on Linux (should also work on Windows and Mac)

### Usage
- Download `client.py`
- Run command: `python3 client.py config.json`, which `config.json` is path to a text file containing this project's configuration
- Example configuration file:

```json
{
    "workingDirectory": "/var/www/html/uks_kristian/web",
    "outputFile": "/var/www/html/uks_kristian/output.json",
    "languageId": "php",
    "includes": [
        "/**/*.php",
    ],
    "excludes": [
        "vendor/**/*.php",
        "class/adodb5/**/*.php",
        "function/phpMailer/*.php"
    ],
    "lspServerCommand": ["docker","exec","intelephense","intelephense","--socket={PORT_NUMBER}"],
    "lspServerStdout": "/tmp/lsp-server-stdout",
    "lspServerStderr": "/tmp/lsp-server-stderr",
    "lspClientPort": 0,
    "lspClientAddress": "0.0.0.0",
    "incrementLineNumber": true,
    "debugPrintTargetFiles": true,
    "debugPrintLspComm": false,
    "debugPrintDiagnostics": false,
    "debugPrintProgress": true,
    "dryRun": false
}

```


- Configuration file contents:

    - `workingDirectory`: 
        - Directory of the project that will be diagnosed, 
        - LSP language server will index this directory and look for symbols, functions, etc. 
        - Default value: current directory

    - `outputFile`: 
        - File path to save the diagnostic result
        - file will be created if not exist, 
        - file will be truncated if exist
        - Default value: `output.json` file in `workingDirectory`, example: `/var/www/html/output.json` if parameter `workingDirectory` is `/var/www/html`

    - `languageId`: 
        - Parameter languageId in [TextDocumentItem](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocumentItem), 
        - Default value: `php`

    - `excludes` and `includes`: 
        - Array of glob patterns to include and exclude file for searching. 
        - Syntax `/**/` can be used for [recursive glob](https://stackoverflow.com/a/14798263) / also called [globstar](https://www.linuxjournal.com/content/globstar-new-bash-globbing-option)
        - Default value for `includes`: all files which have extension of `languageId`, example: `/**/*.php` if parameter `languageId` is `php`
        - Default value for `excludes`: empty array

    - `lspServerCommand`: 
        - Command to start LSP server, 
        - `{PORT_NUMBER}` will be substituted with the port number of this client's variable port number
        - Default value: `["intelephense","--socket={PORT_NUMBER}"]`

    - `lspServerStdout` and `lspServerStderr`:
        - For debugging purpose (e.g.: when LSP server crashes, output of STDOUT/STDERR should be examined). 
        - When this option is set to a file path (e.g.: `/tmp/stderr` and `/tmp/stdout`), it will log LSP server's STDOUT/STDERR to that file.
        - Example use case is for reporting bug/developing for this client, when this client send incorrect JSON, LSP server may crash and exit instead. The output of the crash may contain clue to fix bug in this client's implementation.
        - Default value: `null` for both (will discard STDOUT/STDERR output)

    - `lspClientPort`: 
        - Listen to custom port. 
        - If not specified (or `0` is passed), this client will listen to random port and pass the port number to `{PORT_NUMBER}` in `lspServerCommand`. 
        - Default value: 0

    - `lspClientAddress`: 
        - Bind to this address. 
        - Default value: 0.0.0.0 (listen to all interfaces)

    - `incrementLineNumber`:
        - LSP server diagnostic parameter `lineStart` and `lineEnd` starts at 0 (first line in a file is line 0, second line is line 1, etc)
        - If set to true, will increment `lineStart` and `lineEnd` by 1 (so first in a file is line 1, second line is line 2, etc)
        - Default value: true

    - `debugPrintTargetFiles`:
        - Toggle print/show target files (from processing option `includes` and `excludes`) before running the actual diagnostics
        - Default value: true

    - `debugPrintLspComm`:
        - Toggle print/show traffic/payload of LSP communications, useful for debugging or learning LSP protocol
        - Default value: false

    - `debugPrintDiagnostics`:
        - Toggle print/show diagnostics gained from LSP server
        - Default value: false

    - `debugPrintProgress`:
        - Toggle print/show progress percentage
        - Default value: true

    - `dryRun`:
        - When set to true, will only enumerate files to process and then exit
        - Default value: false

- Example usage with all default parameters: ```python3 client.py <(echo '{}')```

### Intelephense From Docker
To ease installation of Intelephense, which depends on NPM and node.js, author has prepared a docker image to ease the installation on system which have docker installed. On system which already have Intelephense installed, this step is optional.

```bash
docker run \
    --net=host \
    -v '/var/www/html:/var/www/html' \
    --name intelephense \
    krstian/intelephense-node22-alpine:latest
```


- option `--net=host` is used to enable LSP language client and LSP language server to communicate in same port number with host machine
- option `-v` should mount the project directory (inside `workingDirectory` configuration), so that Intelephense can index the project directory for symbols/functions/classes declarations


### Planned Development
- make this client available inside docker (which may or may not include intelephense), so users do not need to install python
- batch processing file (e.g.: only first 100 files) to reduce CPU/memory usage
