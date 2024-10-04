#!/usr/bin/python3

import socket
import json
import time
import subprocess

p = subprocess.Popen(['docker','exec','intelephense','intelephense','--stdio'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

def sendLspMsg(p, msg):
    # p.stdin.write("Content-Type: application/vscode-jsonrpc; charset=utf-8".encode())
    # p.stdin.write("\r\n".encode())
    p.stdin.write(("Content-Length: "+str(len(msg))).encode())
    p.stdin.write("\r\n".encode())
    p.stdin.write("\r\n".encode())
    p.stdin.write(msg.encode())
    p.stdin.write("\r\n".encode())
    p.stdin.write("\r\n".encode())
    # p.communicate()
    print("CLIENT")
    print("\t"+msg)

def sendJsonRpc(p, method, params, idparam=None):
    dictJsonRpc = {"jsonrpc":"2.0", "id":idparam, "method":method, "params":params}
    if idparam == None:
        del dictJsonRpc["id"]
        # NOTE: notification tidak boleh punya ID (akan menyebabkan error)
    return sendLspMsg(p, json.dumps(dictJsonRpc))

def recvUntil(p, substring):
    msg = ""
    while True:
        charIn = p.stdout.read(100).decode()
        print(charIn)
        # p.communicate()
        msg = msg + charIn
        if substring in msg:
            return msg

def recvLspMsg(p):
    print("recvLspMsg")
    str_headers = recvUntil(p, "\r\n\r\n")
    # str_headers = p.stdout.readline().decode()
    arr_headers = str_headers.split("\r\n")
    dict_headers = {}
    for line in arr_headers:
        split_by_colon = line.split(":")
        if len(split_by_colon) != 2:
            continue
        dict_headers[split_by_colon[0].strip().lower()] = split_by_colon[1].strip()

    length = dict_headers["content-length"]
    print(length)
    msg = p.stdout.read(int(length)).decode()
    # p.communicate()
    print("SERVER")
    print("\t"+msg)
    return msg

def recvJsonRpc(p):
    msg = recvLspMsg(p)
    return json.loads(msg)

sendJsonRpc(p=p, idparam=1, method="initialize", params={
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


message = recvJsonRpc(p) # Initialising intelephense 1.12.6
message = recvJsonRpc(p) # Reading state from /tmp/intelephense/...
message = recvJsonRpc(p) # Initialised in ...
message = recvJsonRpc(p) # capabilities ...

# time.sleep(2)
sendJsonRpc(p=p, method="initialized", params={})

# time.sleep(2)
sendJsonRpc(p=p, method="workspace/didChangeConfiguration", params={
    "settings":{"statusText":"mystatus"}
})
message = recvJsonRpc(p) # workspace/configuration ...

# time.sleep(2)
sendJsonRpc(p=p, method="textDocument/didOpen", params={
    "textDocument":{
        "uri":"file:///home/kristian/test.php",
        "languageId":"php",
        "version":0,
        "text":"<?php echo -eee-33d($x);"
    }
})

message = recvJsonRpc(p)
message = recvJsonRpc(p)
message = recvJsonRpc(p)
message = recvJsonRpc(p)
message = recvJsonRpc(p)
message = recvJsonRpc(p)

