#!/usr/bin/python3

import socket
import json
# import time
import subprocess
import os
import glob
import sys
import hashlib
import re

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
debugPrintAction = jsonConfig.get("debugPrintAction", False)
dryRun = jsonConfig.get("dryRun", False)
batchSize = jsonConfig.get("batchSize", 20)
ignoreMessageRegex = jsonConfig.get("ignoreMessageRegex", [])
ignoreSeverity = jsonConfig.get("ignoreSeverity", [])
ignoreCode = jsonConfig.get("ignoreCode", [])
ignoreSource = jsonConfig.get("ignoreSource", [])
additionalInfoCmd = jsonConfig.get("additionalInfoCmd", [])

if workingDirectory.startswith("./"):
    workingDirectory = workingDirectory.replace("./", os.getcwd()+"/")
    if debugPrintAction:
        print("workingDirectory starts with ./ replacing workingDirectory with current directory: "+workingDirectory)

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

# split files to be checked to batches
arrBatch = []
currentBatch = []
for filename in arrFileToBeChecked:
    if len(currentBatch) >= batchSize:
        arrBatch.append(currentBatch)
        currentBatch = []
    currentBatch.append(filename)
arrBatch.append(currentBatch)
numberOfBatch = len(arrBatch)
if debugPrintAction:
    print("splitting "+str(numberOfFileToBeChecked)+" to "+str(numberOfBatch)+" batch")

# if dryRun:
#     exit()

arrFileOpenedInLspServer = []
arrDiagnosticResult = []
arrDiagnosticHash = []
lspSubprocess = None

def processBatch():
    global arrFileToBeChecked
    global numberOfFileToBeChecked
    if len(arrBatch) == 0:
        finished()

    if debugPrintProgress:
        progressTotal = numberOfBatch
        progressCurrent = numberOfBatch-len(arrBatch)+1
        print("processing batch "+str(progressCurrent)+" of "+str(progressTotal)+" ("+str(progressCurrent/progressTotal*100)+"%)")

    arrFileToBeChecked = arrBatch.pop(0)
    arrFileOpenedInLspServer = []
    numberOfFileToBeChecked = len(arrFileToBeChecked)
    print(arrFileToBeChecked)
    startOpenDiagnostic()

def startOpenDiagnostic():
    global socketTimeout
    isMasihAdaFile = True
    socketTimeout = None
    while isMasihAdaFile :
        isMasihAdaFile = openForDiagnostic()
    socketTimeout = 10

def openForDiagnostic():
    if len(arrFileToBeChecked) == 0:
        return False

    if debugPrintProgress:
        progressTotal = numberOfFileToBeChecked
        progressCurrent = numberOfFileToBeChecked-len(arrFileToBeChecked)+1
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

dictSeverity = {"1":"Error","2":"Warning","3":"Information","4":"Hint"}

def receiveDiagnostic(diagnosticData):

    if debugPrintProgress:
        progressTotal = numberOfFileToBeChecked
        progressCurrent = numberOfFileToBeChecked-len(arrFileOpenedInLspServer)+1
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
            "fileName":diagnosticData.get("uri","").replace("file://","").replace(workingDirectory,"").lstrip("/"),
            "lineStart":diag.get("range").get("start").get("line"),
            "lineEnd":diag.get("range").get("end").get("line"),
            "characterStart":diag.get("range").get("start").get("character"),
            "characterEnd":diag.get("range").get("end").get("character"),
            "message":diag.get("message"),
            "severity":dictSeverity.get(str(diag.get("severity")),"Other"),
            "code":diag.get("code"),
            "source":diag.get("source"),
            "additionalInfo":None,
        }

        if incrementLineNumber:
            diagObj["lineStart"] = diagObj["lineStart"]+1
            diagObj["lineEnd"] = diagObj["lineEnd"]+1
        diagHash = hashlib.md5(json.dumps(diagObj).encode()).hexdigest()

        if diagHash not in arrDiagnosticHash:
            arrDiagnosticHash.append(diagHash)

            if (
                diagObj["severity"] not in ignoreSeverity and
                diagObj["code"] not in ignoreCode and
                diagObj["source"] not in ignoreSource and
                len(sum([ re.findall(x, diagObj["message"]) for x in ignoreMessageRegex ],[])) == 0
            ):
                if additionalInfoCmd != None and len(additionalInfoCmd) > 1:
                    cmd = additionalInfoCmd.copy()
                    cmd = [ x.replace("{WORKING_DIRECTORY}",workingDirectory) for x in cmd ]
                    cmd = [ x.replace("{FILE_NAME}",      str(diagObj["fileName"])) for x in cmd ]
                    cmd = [ x.replace("{LINE_START}",     str(diagObj["lineStart"])) for x in cmd ]
                    cmd = [ x.replace("{LINE_END}",       str(diagObj["lineEnd"])) for x in cmd ]
                    cmd = [ x.replace("{CHARACTER_START}",str(diagObj["characterStart"])) for x in cmd ]
                    cmd = [ x.replace("{CHARACTER_END}",  str(diagObj["characterEnd"])) for x in cmd ]
                    cmd = [ x.replace("{MESSAGE}",        str(diagObj["message"])) for x in cmd ]
                    cmd = [ x.replace("{SEVERITY}",       str(diagObj["severity"])) for x in cmd ]
                    cmd = [ x.replace("{CODE}",           str(diagObj["code"])) for x in cmd ]
                    cmd = [ x.replace("{SOURCE}",         str(diagObj["source"])) for x in cmd ]
                    additionalInfoSubprocess = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    additionalInfoSubprocess.wait()
                    diagObj["additionalInfo"] = ""
                    for line in additionalInfoSubprocess.stdout:
                        diagObj["additionalInfo"] = diagObj["additionalInfo"] + line.decode()
                    diagObj["additionalInfo"] = diagObj["additionalInfo"].strip()

                arrDiagnosticResult.append(diagObj)

    if debugPrintDiagnostics:
        print("got new diagnostic data")
        print(arrDiagnosticResult)

    if len(arrFileOpenedInLspServer) == 0:
        processBatch()

def finished():
    if debugPrintDiagnostics:
        print("finished!")
        print(arrDiagnosticResult)
    with open(outputFile, "w") as f:
        f.write(json.dumps(arrDiagnosticResult))
    if type(lspSubprocess) == subprocess.Popen:
        lspSubprocess.terminate()
        lspSubprocess.kill()
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
lspSubprocess = subprocess.Popen(lspServerCommand, stdout=lspServerStdout,stderr=lspServerStderr)

sockClient, addr = sock.accept()
socketTimeout = None
if debugPrintLspComm:
    print("CLIENT CONNECTED! ADDRESS: ", addr)

def sendLspMsg(sock, msg):
    # sock.sendall("Content-Type: application/vscode-jsonrpc; charset=utf-8".encode())
    # sock.sendall("\r\n".encode())
    sock.sendall(("Content-Length: "+str(len(msg))).encode())
    sock.sendall("\r\n".encode())
    sock.sendall("\r\n".encode())
    sock.sendall(msg.encode())
    # sock.sendall("\r\n".encode())
    # sock.sendall("\r\n".encode())
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
        sock.settimeout(socketTimeout)
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
    sock.settimeout(socketTimeout)
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
        try:
            message = recvJsonRpc(sockClient)
            eventHandler(sockClient, message)
        except Exception as e:
            print(e)
            raise e
            # print(arrFileOpenedInLspServer)
            # receiveDiagnostic({})

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
        processBatch()

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
      # storagePath: "/tmp/",
      # globalStoragePath: "/tmp/",
      # licenseKey: "/tmp/",
      "clearCache": True,
      "logVerbosity": "verbose",
    }
})
startEventPolling(sockClient)
