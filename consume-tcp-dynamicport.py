#!/usr/bin/python3

import socket
import json
# import time
import subprocess

bufferSize = 4092
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.bind(("0.0.0.0", 6641))
sock.bind(("0.0.0.0", 0))
portnumber = sock.getsockname()[1]
sock.listen(1)

p = subprocess.Popen(['docker','exec','intelephense','intelephense','--socket='+str(portnumber) ])

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

def sendJsonRpc(sock, method, params, idparam=None):
    dictJsonRpc = {"jsonrpc":"2.0", "id":idparam, "method":method, "params":params}
    if idparam == None:
        del dictJsonRpc["id"]
        # NOTE: notification tidak boleh punya ID (akan menyebabkan error)
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

sendJsonRpc(sock=sockClient, idparam=1, method="initialize", params={
    "processId": 1,
    "clientInfo": {
      "name": "custom client",
      "version": "0.0.1"
    },
    "rootUri": "file:///home/kristian",
    "rootPath": "/home/kristian",
    "workspaceFolders": [
      {
        "name": "kristian",
        "uri": "file:///home/kristian"
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
      "clearCache": False,
      "logVerbosity": "verbose",
    }
})

message = recvJsonRpc(sockClient) # Initialising intelephense 1.12.6
message = recvJsonRpc(sockClient) # Reading state from /tmp/intelephense/...
message = recvJsonRpc(sockClient) # Initialised in ...
message = recvJsonRpc(sockClient) # capabilities ...

# time.sleep(2)
sendJsonRpc(sock=sockClient, method="initialized", params={})

# time.sleep(2)
sendJsonRpc(sock=sockClient, method="workspace/didChangeConfiguration", params={
    "settings":{"statusText":"mystatus"}
})
message = recvJsonRpc(sockClient) # workspace/configuration ...

# time.sleep(2)
sendJsonRpc(sock=sockClient, method="textDocument/didOpen", params={
    "textDocument":{
        "uri":"file:///home/kristian/test.php",
        "languageId":"php",
        "version":0,
        "text":"<?php echo -eee-33d($x);"
    }
})

message = recvJsonRpc(sockClient) # publishDiagnostics

sendJsonRpc(sock=sockClient, method="textDocument/didClose", params={
    "textDocument":{
        "uri":"file:///home/kristian/test.php"
    }
})

sendJsonRpc(sock=sockClient, method="textDocument/didOpen", params={
    "textDocument":{
        "uri":"file:///home/kristian/test2.php",
        "languageId":"php",
        "version":0,
        "text":"<?php echo yourfunc($x);"
    }
})

message = recvJsonRpc(sockClient)
message = recvJsonRpc(sockClient)

sendJsonRpc(sock=sockClient, idparam=2, method="textDocument/hover", params={
    "textDocument":{
        "uri":"file:///home/kristian/test2.php",
    },
    "position":{
        "line":0,
        "character":0,
    }
})

message = recvJsonRpc(sockClient)
message = recvJsonRpc(sockClient)
message = recvJsonRpc(sockClient)

