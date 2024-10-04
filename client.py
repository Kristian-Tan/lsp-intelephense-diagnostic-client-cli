#!/usr/bin/python3

import socket
import json
# import time
import subprocess
import os
import glob
import sys


# example usage:
# cd /var/www/html/uks_kristian/web
# python3 intelephense-cli.py '' '["vendor/**/*.php","class/adodb5/**/*.php","function/phpMailer/*.php"]'

workingDirectory = os.getcwd()

# get files to be checked
if len(sys.argv) < 2:
    jsonGlobFilesToBeChecked = '["/**/*.php"]'
else:
    jsonGlobFilesToBeChecked = sys.argv[1]

if jsonGlobFilesToBeChecked == '':
    jsonGlobFilesToBeChecked = '["/**/*.php"]'

jsonGlobFilesToBeChecked = json.loads(jsonGlobFilesToBeChecked)

arrFileToBeChecked = []
for globFile in jsonGlobFilesToBeChecked:
    for filename in glob.glob(workingDirectory+"/"+globFile, recursive=True):
        arrFileToBeChecked.append(filename)
# exit()

# get files to be ignored
if len(sys.argv) < 3:
    jsonGlobFilesToBeIgnored = '[]'
else:
    jsonGlobFilesToBeIgnored = sys.argv[2]

if jsonGlobFilesToBeChecked == '':
    jsonGlobFilesToBeChecked = '["/**/*.php"]'

jsonGlobFilesToBeIgnored = json.loads(jsonGlobFilesToBeIgnored)

arrFileToBeIgnored = []
for globFile in jsonGlobFilesToBeIgnored:
    for filename in glob.glob(workingDirectory+"/"+globFile, recursive=True):
        print(filename)
        if filename in arrFileToBeChecked:
            arrFileToBeChecked.remove(filename)

print("file list:")
print(arrFileToBeChecked)
if len(arrFileToBeChecked) == 0:
    print("no file found")
    exit()
# exit()

arrFileOpenedInLspServer = []
arrDiagnosticResult = []

def openForDiagnostic():
    if len(arrFileToBeChecked) == 0:
        return False

    filename = arrFileToBeChecked.pop(0)
    with open(filename) as f: content = f.read()

    sendJsonRpc(sock=sockClient, method="textDocument/didOpen", params={
        "textDocument":{
            "uri":"file://"+filename,
            "languageId":"php",
            "version":0,
            "text":content,
        },
    })
    arrFileOpenedInLspServer.append(filename)
    return True

def receiveDiagnostic(diagnosticData):
    filename = diagnosticData.get("uri")
    sendJsonRpc(sock=sockClient, method="textDocument/didClose", params={
        "textDocument":{
            "uri": "file://"+filename,
        },
    })
    filename = filename.replace("file://","")
    if filename in arrFileOpenedInLspServer:
        arrFileOpenedInLspServer.remove(filename)

    # save diagnostic result to an array
    for diag in diagnosticData.get("diagnostics",[]):
        arrDiagnosticResult.append({
            "filename":diagnosticData.get("uri",None),
            "lineStart":diag.get("range").get("start").get("line"),
            "lineEnd":diag.get("range").get("end").get("line"),
            "characterStart":diag.get("range").get("start").get("character"),
            "characterEnd":diag.get("range").get("end").get("character"),
            "message":diag.get("message"),
            "severity":diag.get("severity"),
            "code":diag.get("code"),
            "source":diag.get("source"),
        })

    print("got new diagnostic data")
    print(arrDiagnosticResult)

    if len(arrFileOpenedInLspServer) == 0:
        print("finished!")
        print(arrDiagnosticResult)
        exit()

# communication with LSP server

bufferSize = 4092
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", 0)) # bind to port 0, this will make python try to find unused port to bind to (portnumber will returned below)
portnumber = sock.getsockname()[1]
sock.listen(1)

p = subprocess.Popen(['docker','exec','intelephense','intelephense','--socket='+str(portnumber) ], stdout=open("/tmp/stdout1","w"),stderr=open("/tmp/stderr1","w"))

sockClient, addr = sock.accept()
print("CLIENT CONNECTED! ADDRESS: ", addr)

def sendLspMsg(sock, msg):
    # sock.sendall("Content-Type: application/vscode-jsonrpc; charset=utf-8".encode())
    # sock.sendall("\r\n".encode())
    sock.sendall(("Content-Length: "+str(len(msg))).encode())
    sock.sendall("\r\n".encode())
    sock.sendall("\r\n".encode())
    sock.sendall(msg.encode())
    sock.sendall("\r\n".encode())
    sock.sendall("\r\n".encode())
    print("CLIENT")
    print("\t"+msg)

def sendJsonRpc(sock, idparam=None, method=None, params=None, result=None, includes=[]):
    dictJsonRpc = {"jsonrpc":"2.0", "id":idparam, "method":method, "params":params, "result":result}
    if idparam == None and "id" not in includes:
        del dictJsonRpc["id"]
    if method == None and "method" not in includes:
        del dictJsonRpc["method"]
    if params == None and "params" not in includes:
        del dictJsonRpc["params"]
    if result == None and "result" not in includes:
        del dictJsonRpc["result"]
        # NOTE: jsonprc notification does not have id field (will throw error)
    return sendLspMsg(sock, json.dumps(dictJsonRpc))

def recvUntil(sock, substring):
    msg = ""
    while True:
        charIn = sock.recv(1).decode()
        msg = msg + charIn
        if substring in msg:
            return msg

def recvLspMsg(sock):
    str_headers = recvUntil(sock, "\r\n\r\n")
    arr_headers = str_headers.split("\r\n")
    dict_headers = {}
    for line in arr_headers:
        split_by_colon = line.split(":")
        if len(split_by_colon) != 2:
            continue
        dict_headers[split_by_colon[0].strip().lower()] = split_by_colon[1].strip()

    length = dict_headers["content-length"]
    # print(length)
    msg = sock.recv(int(length)).decode()
    print("SERVER")
    print("\t"+msg)
    return msg

def recvJsonRpc(sock):
    msg = recvLspMsg(sock)
    return json.loads(msg)

def startEventPolling(sockClient):
    while True:
        message = recvJsonRpc(sockClient)
        eventHandler(sockClient, message)

def eventHandler(sockClient, message):
    if message.get("id",None) == 1 and message.get("result",{}).get("capabilities",None) != None :
        sendJsonRpc(sock=sockClient, method="initialized", params={})
        sendJsonRpc(sock=sockClient, method="workspace/didChangeConfiguration", params={
            "settings":{"statusText":"mystatus"}
        })
    elif message.get("id",None) != None and message.get("method",None) == "workspace/configuration":
        result = []
        for x in message.get("params",{"items":[]}).get("items"):
            result.append(None)
        sendJsonRpc(sock=sockClient, idparam=message.get("id",None), result=result)
    elif message.get("id",None) != None and message.get("method",None) == "client/registerCapability":
        sendJsonRpc(sock=sockClient, idparam=message.get("id",None), result=None, includes=["result"])

    elif message.get("id",None) == None and message.get("method",None) == "indexingEnded": # when indexing has ended, we can start opening first file
        isMasihAdaFile = True
        while isMasihAdaFile :
            isMasihAdaFile = openForDiagnostic()

    elif message.get("id",None) == None and message.get("method",None) == "textDocument/publishDiagnostics":
        receiveDiagnostic(message.get("params"))

    elif message.get("id",None) == None and message.get("method",None) in ["indexingStarted","window/logMessage"]:
        pass # ignored notification


    # generic non-handled
    elif message.get("id",None) == None:
        print("notification only")
    elif message.get("id",None) != None:
        raise Exception("unimplemented method called!")
    else:
        raise Exception("unimplemented event!")

# NOTE: textDocument/publishDiagnostics may sometime not show because this line is sent from server:
# Reading state from /tmp/intelephense/3f29bfe2.
# so maybe we need to force intelephense to reindex by removing /tmp/intelephense/* directory content
# also, we should set initializationOption.clearCache=true to force reindex, then clear state by running 'rm -r /tmp/intelephense/*'

sendJsonRpc(sock=sockClient, idparam=1, method="initialize", params={
    "processId": 1,
    "clientInfo": {
      "name": "custom client",
      "version": "0.0.1"
    },
    "rootUri": "file://"+workingDirectory,
    "rootPath": workingDirectory,
    "workspaceFolders": [
      {
        "name": workingDirectory.split("/")[ len(workingDirectory.split("/"))-1 ],
        "uri": "file://"+workingDirectory,
      }
    ],
    "capabilities": {
      "general": {
        "regularExpressions": {
          "engine": "ECMAScript"
        },
        "markdown": {
          "parser": "Python-Markdown",
          "version": "3.2.2"
        }
      },
      "textDocument": {
        "synchronization": {
          "dynamicRegistration": True,
          "didSave": True,
          "willSave": True,
          "willSaveWaitUntil": True
        },
        "hover": {
          "dynamicRegistration": True,
          "contentFormat": [
            "markdown",
            "plaintext"
          ]
        },
        "completion": {
          "dynamicRegistration": True,
          "completionItem": {
            "snippetSupport": True,
            "deprecatedSupport": True,
            "documentationFormat": [
              "markdown",
              "plaintext"
            ],
            "tagSupport": {
              "valueSet": [
                1
              ]
            },
            "resolveSupport": {
              "properties": [
                "detail",
                "documentation",
                "additionalTextEdits"
              ]
            },
            "insertReplaceSupport": True,
            "insertTextModeSupport": {
              "valueSet": [
                2
              ]
            },
            "labelDetailsSupport": True
          },
          "completionItemKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25
            ]
          },
          "insertTextMode": 2,
          "completionList": {
            "itemDefaults": [
              "editRange",
              "insertTextFormat",
              "data"
            ]
          }
        },
        "signatureHelp": {
          "dynamicRegistration": True,
          "contextSupport": True,
          "signatureInformation": {
            "activeParameterSupport": True,
            "documentationFormat": [
              "markdown",
              "plaintext"
            ],
            "parameterInformation": {
              "labelOffsetSupport": True
            }
          }
        },
        "references": {
          "dynamicRegistration": True
        },
        "documentHighlight": {
          "dynamicRegistration": True
        },
        "documentSymbol": {
          "dynamicRegistration": True,
          "hierarchicalDocumentSymbolSupport": True,
          "symbolKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25,
              26
            ]
          },
          "tagSupport": {
            "valueSet": [
              1
            ]
          }
        },
        "documentLink": {
          "dynamicRegistration": True,
          "tooltipSupport": True
        },
        "formatting": {
          "dynamicRegistration": True
        },
        "rangeFormatting": {
          "dynamicRegistration": True,
          "rangesSupport": True
        },
        "declaration": {
          "dynamicRegistration": True,
          "linkSupport": True
        },
        "definition": {
          "dynamicRegistration": True,
          "linkSupport": True
        },
        "typeDefinition": {
          "dynamicRegistration": True,
          "linkSupport": True
        },
        "implementation": {
          "dynamicRegistration": True,
          "linkSupport": True
        },
        "codeAction": {
          "dynamicRegistration": True,
          "codeActionLiteralSupport": {
            "codeActionKind": {
              "valueSet": [
                "quickfix",
                "refactor",
                "refactor.extract",
                "refactor.inline",
                "refactor.rewrite",
                "source.fixAll",
                "source.organizeImports"
              ]
            }
          },
          "dataSupport": True,
          "isPreferredSupport": True,
          "resolveSupport": {
            "properties": [
              "edit"
            ]
          }
        },
        "rename": {
          "dynamicRegistration": True,
          "prepareSupport": True,
          "prepareSupportDefaultBehavior": 1
        },
        "colorProvider": {
          "dynamicRegistration": True
        },
        "publishDiagnostics": {
          "relatedInformation": True,
          "tagSupport": {
            "valueSet": [
              1,
              2
            ]
          },
          "versionSupport": True,
          "codeDescriptionSupport": True,
          "dataSupport": True
        },
        "diagnostic": {
          "dynamicRegistration": True,
          "relatedDocumentSupport": True
        },
        "selectionRange": {
          "dynamicRegistration": True
        },
        "foldingRange": {
          "dynamicRegistration": True,
          "foldingRangeKind": {
            "valueSet": [
              "comment",
              "imports",
              "region"
            ]
          }
        },
        "codeLens": {
          "dynamicRegistration": True
        },
        "inlayHint": {
          "dynamicRegistration": True,
          "resolveSupport": {
            "properties": [
              "textEdits",
              "label.command"
            ]
          }
        },
        "semanticTokens": {
          "dynamicRegistration": True,
          "requests": {
            "range": True,
            "full": {
              "delta": True
            }
          },
          "tokenTypes": [
            "namespace",
            "type",
            "class",
            "enum",
            "interface",
            "struct",
            "typeParameter",
            "parameter",
            "variable",
            "property",
            "enumMember",
            "event",
            "function",
            "method",
            "macro",
            "keyword",
            "modifier",
            "comment",
            "string",
            "number",
            "regexp",
            "operator",
            "decorator"
          ],
          "tokenModifiers": [
            "declaration",
            "definition",
            "readonly",
            "static",
            "deprecated",
            "abstract",
            "async",
            "modification",
            "documentation",
            "defaultLibrary"
          ],
          "formats": [
            "relative"
          ],
          "overlappingTokenSupport": False,
          "multilineTokenSupport": True,
          "augmentsSyntaxTokens": True
        },
        "callHierarchy": {
          "dynamicRegistration": True
        },
        "typeHierarchy": {
          "dynamicRegistration": True
        }
      },
      "workspace": {
        "applyEdit": True,
        "didChangeConfiguration": {
          "dynamicRegistration": True
        },
        "executeCommand": {},
        "workspaceEdit": {
          "documentChanges": True,
          "failureHandling": "abort"
        },
        "workspaceFolders": True,
        "symbol": {
          "dynamicRegistration": True,
          "resolveSupport": {
            "properties": [
              "location.range"
            ]
          },
          "symbolKind": {
            "valueSet": [
              1,
              2,
              3,
              4,
              5,
              6,
              7,
              8,
              9,
              10,
              11,
              12,
              13,
              14,
              15,
              16,
              17,
              18,
              19,
              20,
              21,
              22,
              23,
              24,
              25,
              26
            ]
          },
          "tagSupport": {
            "valueSet": [
              1
            ]
          }
        },
        "configuration": True,
        "codeLens": {
          "refreshSupport": True
        },
        "inlayHint": {
          "refreshSupport": True
        },
        "semanticTokens": {
          "refreshSupport": True
        },
        "diagnostics": {
          "refreshSupport": True
        }
      },
      "window": {
        "showDocument": {
          "support": True
        },
        "showMessage": {
          "messageActionItem": {
            "additionalPropertiesSupport": True
          }
        },
        "workDoneProgress": True
      }
    },
    "initializationOptions": {
      # "clearCache": True,
      "clearCache": True,
      "logVerbosity": "verbose",
    }
})
startEventPolling(sockClient)

exit()
