#!/usr/bin/python3

import socket
import json
# import time
import subprocess
import os
import glob
import sys
import hashlib

## config file
# example config file
"""
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
    "lspClientBuffer": 4092
}
"""
if len(sys.argv) == 2:
    configFilename = sys.argv[1]
    with open(configFilename) as f: configContent = f.read()
    jsonConfig = json.loads(configContent)
else:
    raise Exception("config file not supplied")
    jsonConfig = {}


workingDirectory = jsonConfig.get("workingDirectory", os.getcwd())
outputFile = jsonConfig.get("outputFile", workingDirectory+"/output.json")
languageId = jsonConfig.get("languageId", "php")
globFilesIncludes = jsonConfig.get("includes", ["/**/*."+languageId])
globFilesExcludes = jsonConfig.get("excludes", [])
lspServerCommand = jsonConfig.get("lspServerCommand", ["intelephense","--socket={PORT_NUMBER}"])
lspServerStdout = jsonConfig.get("lspServerStdout", None)
lspServerStderr = jsonConfig.get("lspServerStderr", None)
lspClientPort = jsonConfig.get("lspClientPort", 0)
lspClientAddress = jsonConfig.get("lspClientAddress", "0.0.0.0")
incrementLineNumber = jsonConfig.get("incrementLineNumber", True)
# lspClientBuffer = jsonConfig.get("lspClientBuffer", 4092)
debugPrintTargetFiles = jsonConfig.get("debugPrintTargetFiles", True)
debugPrintLspComm = jsonConfig.get("debugPrintLspComm", False)
debugPrintDiagnostics = jsonConfig.get("debugPrintDiagnostics", False)
debugPrintProgress = jsonConfig.get("debugPrintProgress", True)
dryRun = jsonConfig.get("dryRun", False)
batchSize = jsonConfig.get("batchSize", 10)

if workingDirectory.startswith("./"):
    workingDirectory = workingDirectory.replace("./", os.getcwd()+"/")

arrFileToBeChecked = []
for globFile in globFilesIncludes:
    for filename in glob.glob(workingDirectory+"/"+globFile, recursive=True):
        arrFileToBeChecked.append(filename)
# exit()

arrFileToBeIgnored = []
for globFile in globFilesExcludes:
    for filename in glob.glob(workingDirectory+"/"+globFile, recursive=True):
        # if debugPrintTargetFiles:
        #     print(filename)
        if filename in arrFileToBeChecked:
            arrFileToBeChecked.remove(filename)

numberOfFileToBeChecked = len(arrFileToBeChecked)
if debugPrintTargetFiles:
    print("file list: "+str(numberOfFileToBeChecked)+" file(s)")
    print(arrFileToBeChecked)
if len(arrFileToBeChecked) == 0:
    print("no file found")
    exit()

if dryRun:
    exit()

arrFileOpenedInLspServer = []
arrDiagnosticResult = []
arrDiagnosticHash = []

def openForDiagnostic():
    if len(arrFileToBeChecked) == 0:
        return False

    if debugPrintProgress:
        progressTotal = numberOfFileToBeChecked
        progressCurrent = numberOfFileToBeChecked-len(arrFileToBeChecked)
        print("opening file "+str(progressCurrent)+" of "+str(progressTotal)+" ("+str(progressCurrent/progressTotal*100)+"%)")

    filename = arrFileToBeChecked.pop(0)
    with open(filename) as f: content = f.read()

    sendJsonRpc(sock=sockClient, method="textDocument/didOpen", params={
        "textDocument":{
            "uri":"file://"+filename,
            "languageId":languageId,
            "version":0,
            "text":content,
        },
    })
    arrFileOpenedInLspServer.append(filename)
    return True

def receiveDiagnostic(diagnosticData):

    if debugPrintProgress:
        progressTotal = numberOfFileToBeChecked
        progressCurrent = numberOfFileToBeChecked-len(arrFileOpenedInLspServer)
        print("receive diagnostic "+str(progressCurrent)+" of "+str(progressTotal)+" ("+str(progressCurrent/progressTotal*100)+"%)")

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
        diagObj = {
            "filename":diagnosticData.get("uri","").replace("file://",""),
            "lineStart":diag.get("range").get("start").get("line"),
            "lineEnd":diag.get("range").get("end").get("line"),
            "characterStart":diag.get("range").get("start").get("character"),
            "characterEnd":diag.get("range").get("end").get("character"),
            "message":diag.get("message"),
            "severity":diag.get("severity"),
            "code":diag.get("code"),
            "source":diag.get("source"),
        }
        if incrementLineNumber:
            diagObj["lineStart"] = diagObj["lineStart"]+1
            diagObj["lineEnd"] = diagObj["lineEnd"]+1
        diagHash = hashlib.md5(json.dumps(diagObj).encode()).hexdigest()
        if diagHash not in arrDiagnosticHash:
            arrDiagnosticResult.append(diagObj)
            arrDiagnosticHash.append(diagHash)

    if debugPrintDiagnostics:
        print("got new diagnostic data")
        print(arrDiagnosticResult)

    if len(arrFileOpenedInLspServer) == 0:
        if debugPrintDiagnostics:
            print("finished!")
            print(arrDiagnosticResult)
        with open(outputFile, "w") as f:
            f.write(json.dumps(arrDiagnosticResult))
        exit()

# communication with LSP server

# bufferSize = lspClientBuffer
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((lspClientAddress, lspClientPort)) # if bind to port 0, then this will make python try to find unused port to bind to (portnumber will returned below)
portnumber = sock.getsockname()[1]
sock.listen(1)

lspServerCommand = [ x.replace("{PORT_NUMBER}",str(portnumber)) for x in lspServerCommand ]
if lspServerStdout != None:
    lspServerStdout = open(lspServerStdout, "w")
if lspServerStderr != None:
    lspServerStderr = open(lspServerStderr, "w")
p = subprocess.Popen(lspServerCommand, stdout=lspServerStdout,stderr=lspServerStderr)

sockClient, addr = sock.accept()
if debugPrintLspComm:
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
    if debugPrintLspComm:
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
    if debugPrintLspComm:
        print(length)
    msg = sock.recv(int(length)).decode()
    if debugPrintLspComm:
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
        if debugPrintProgress:
            print("indexingEnded")
        isMasihAdaFile = True
        while isMasihAdaFile :
            isMasihAdaFile = openForDiagnostic()

    elif message.get("id",None) == None and message.get("method",None) == "textDocument/publishDiagnostics":
        receiveDiagnostic(message.get("params"))

    elif message.get("id",None) == None and message.get("method",None) == "window/logMessage":
        pass

    elif message.get("id",None) == None and message.get("method",None) == "indexingStarted":
        if debugPrintProgress:
            print("indexingStarted")


    # generic non-handled
    elif message.get("id",None) == None:
        if debugPrintLspComm:
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
      "textDocument": {
        "synchronization": {
          "dynamicRegistration": True,
        },
        "documentLink": {
          "dynamicRegistration": True,
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
        "configuration": True,
        "diagnostics": {
          "refreshSupport": True
        }
      },
    },
    "initializationOptions": {
      # "clearCache": True,
      "clearCache": True,
      "logVerbosity": "verbose",
    }
})
startEventPolling(sockClient)

exit()
