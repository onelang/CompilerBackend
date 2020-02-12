#!/usr/bin/env python
import subprocess
import os
import json
import urllib2
import time
import datetime
import traceback
import shutil
import errno
import sys
import random
import os.path
import hashlib

import SimpleHTTPServer
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer

PORT = 11111
TEST_SERVERS = False
TMP_DIR = "tmp/"
LANGS = {
    "java": { # uses in-memory compilation
        "jsonReplCmd": "java -cp target/classes:lib/* fastjavacompile.App",
        "testCode": '''
            class Program {
                public static void main(String[] args) {
                    System.out.println("hello world!");
                }
            }
        ''',
        "mainFn": "Program.java",
        "stdlibFn": "one.java",
        "cmd": "javac Program.java one.java && java Program",
        "versionCmd": "javac -version; java -version",
    },
    "typescript": { # uses in-memory compilation
        "jsonReplCmd": "node jsonrepl.js",
        "testCode": "console.log('hello world!');",
        "cmd": "tsc index.ts node_modules/one/index.ts > /dev/null; node index.js",
        "mainFn": "index.ts",
        "stdlibFn": "node_modules/one/index.ts",
        "versionCmd": "echo Node: `node -v`; echo TSC: `tsc -v`",
    },
    "javascript": { # uses in-memory compilation
        "jsonReplCmd": "node jsonrepl.js",
        "jsonReplDir": "TypeScript",
        "testCode": "console.log('hello world!');",
        "cmd": "node index.js",
        "mainFn": "index.js",
        "stdlibFn": "node_modules/one/index.js",
        "versionCmd": "echo Node: `node -v`",
    },
    "python": { # uses in-memory compilation
        "jsonReplCmd": "python -u jsonrepl.py",
        "testCode": "print 'hello world!'",
        "mainFn": "main.py",
        "stdlibFn": "one.py",
        "cmd": "python main.py",
        "versionCmd": "python --version",
    },
    "ruby": { # uses in-memory compilation
        "jsonReplCmd": "ruby jsonrepl.rb",
        "testCode": "puts 'hello world!'",
        "mainFn": "main.rb",
        "stdlibFn": "one.rb",
        "cmd": "ruby -I. main.rb",
        "versionCmd": "ruby -v",
    },
    "csharp": { # uses in-memory compilation
        "jsonReplCmd": "dotnet run --no-build",
        "testCode": """
            using System;
            public class Program
            {
                public static void Main(string[] args)
                {
                    Console.WriteLine("Hello World!");
                }
            }
        """,
        "cmd": "csc Program.cs StdLib.cs > /dev/null && ./Program.exe",
        "mainFn": "Program.cs",
        "stdlibFn": "StdLib.cs",
        "versionCmd": "dotnet --info; echo CSC version: `csc -version`",
    },
    "php": { # uses in-memory compilation
        #"jsonReplCmd": "php jsonrepl.php", # require_once causes fatal error which stops PHP execution
        #"serverCmd": "php -S 127.0.0.1:{port} server.php",
        "port": 8003,
        "testCode": "print 'hello world!';",
        "mainFn": "main.php",
        "stdlibFn": "one.php",
        "cmd": "php main.php",
        "versionCmd": "php -v",
    },
    "cpp": {
        "ext": "cpp",
        "mainFn": "main.cpp",
        "stdlibFn": "one.hpp",
        "cmd": "g++ -std=c++17 main.cpp -I. -o binary && ./binary",
        "versionCmd": "g++ -v",
    },
    "go": {
        "ext": "go",
        "mainFn": "main.go",
        "stdlibFn": "src/one/one.go",
        "cmd": "GOPATH=$PWD go run main.go",
        "versionCmd": "go version",
    },
    "perl": {
        "ext": "pl",
        "mainFn": "main.pl",
        "stdlibFn": "one.pm",
        "cmd": "perl -I. main.pl",
        "versionCmd": "perl -v",
    },
    "swift": {
        "ext": "swift",
        "mainFn": "main.swift",
        "stdlibFn": "one.swift",
        "cmd": "cat one.swift main.swift | swift -",
        "versionCmd": "swift --version",
    }
}

def log(text):
    print "[CompilerBackend] %s" % text

class JsonReplClient:
    def __init__(self, cmd, cwd):
        self.p = subprocess.Popen(cmd.split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, cwd=cwd)
    
    def request(self, request):
        self.p.stdin.write(json.dumps(request) + "\n")
        return json.loads(self.p.stdout.readline())

    def compile(self, code, stdlib):
        return self.request({"cmd": "compile", "code": code, "stdlibCode": stdlib, "className": "TestClass", "methodName": "testMethod" })

def postRequest(url, request):
    return urllib2.urlopen(urllib2.Request(url, request, headers={"Origin": "http://127.0.0.1:8000"})).read()

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise    

def providePath(fileName):
    mkdir_p(os.path.dirname(fileName))
    return fileName

allowRemote = not "--localOnly" in sys.argv
requireToken = allowRemote or "--requireToken" in sys.argv

version_cache = None
mkdir_p(TMP_DIR)

if requireToken:
    token = ""
    if os.path.isfile(".secret_token"):
        with open(".secret_token", "r") as f: token = f.read()
    if len(token) < 32:
        token = "%16x" % random.SystemRandom().getrandbits(128)
        with open(".secret_token", "w") as f: f.write(token)

if not "--noInMemoryCompilation" in sys.argv:
    for langName in LANGS:
        try:
            lang = LANGS[langName]
            cwd = "%s/InMemoryCompilers/%s" % (os.getcwd(), lang.get("jsonReplDir", langName))
            if "jsonReplCmd" in lang:
                log("Starting %s JSON-REPL..." % langName)
                lang["jsonRepl"] = JsonReplClient(lang["jsonReplCmd"], cwd)
            elif "serverCmd" in lang:
                log("Starting %s HTTP server..." % langName)
                args = lang["serverCmd"].replace("{port}", str(lang["port"])).split(" ") 
                lang["server"] = subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE) 
        except Exception as e:
            print "Failed to start compiler %s: %r" % (langName, e)

if TEST_SERVERS: # TODO
    testText = "Works!"
    requestJson = json.dumps(lang["testRequest"], indent=4).replace("{testText}", testText)

    maxTries = 10
    for i in xrange(maxTries):
        try:
            time.sleep(0.1 * (i + 1))
            log("  Checking %s compiler's status (%d / %d)..." % (langName, i + 1, maxTries))
            responseJson = postRequest("http://127.0.0.1:%d/compile" % lang["port"], requestJson)
            break
        except:
            pass

    response = json.loads(responseJson)
    log("  %s compiler's test response: %s" % (langName, response))
    if response["result"] != testText:
        log("Invalid response. Compiler will be disabled.")
    else:
        log("%s compiler is ready!" % langName)        

class HTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def resp(self, statusCode, result):
        result["controllerVersion"] = "one:v1:20180122"
        responseBody = json.dumps(result)
        self.send_response(statusCode)
        self.send_header("Content-Length", "%d" % len(responseBody))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(responseBody)
        self.wfile.close()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store")
        SimpleHTTPServer.SimpleHTTPRequestHandler.end_headers(self)

    def api_compile(self):
        requestJson = self.rfile.read(int(self.headers.getheader('content-length')))
        useCache = self.queryParams.get("useCache")
        if useCache:
            requestHash = hashlib.sha256(requestJson).hexdigest()
            cacheFn = "%s/compilation_cache_%s_response.json" % (TMP_DIR, requestHash)
            if os.path.exists(cacheFn):
                with open(cacheFn, "rt") as f: 
                    self.resp(200, json.loads(f.read()))
                    return

        request = json.loads(requestJson)
        request["cmd"] = "compile"
        langName = request["lang"]
        lang = LANGS[langName]

        start = time.time()
        if "jsonRepl" in lang:
            response = lang["jsonRepl"].request(request)
        elif "server" in lang:
            responseJson = postRequest("http://127.0.0.1:%d" % lang["port"], requestJson)
            response = json.loads(responseJson)
        else:
            dateStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            outDir = "%s%s_%s/" % (TMP_DIR, dateStr, langName)

            with open(providePath(outDir + lang["mainFn"]), "wt") as f: f.write(request["code"])

            if "stdlibCode" in request:
                with open(providePath(outDir + lang["stdlibFn"]), "wt") as f: f.write(request["stdlibCode"])

            for pkgSrc in request["packageSources"]:
                with open(providePath(outDir + pkgSrc["fileName"]), "wt") as f: f.write(pkgSrc["code"])
            
            pipes = subprocess.Popen(lang["cmd"], shell=True, cwd=outDir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = pipes.communicate()

            response = { "result": stdout }

            if pipes.returncode != 0 or len(stderr) > 0:
                response["exceptionText"] = stderr
            else:
                shutil.rmtree(outDir)

        if useCache:
            with open(cacheFn, "wt") as f: f.write(json.dumps(response))

        response["elapsedMs"] = int((time.time() - start) * 1000)
        self.resp(200, response)

    def api_compiler_versions(self):
        # TODO: thread-safety
        global version_cache
        if not version_cache:
            version_cache = {}
            for lang in LANGS:
                try:
                    version_cache[lang] = subprocess.check_output(LANGS[lang]["versionCmd"], shell=True, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    version_cache[lang] = e.output
        self.resp(200, version_cache)

    def api_status(self):
        self.resp(200, { "status": "ok" })

    def do_GET(self):
        return self.resp(403, { "exceptionText": "GET method is not allowed", "errorCode": "method_not_allowed" })            

    def originCheck(self):
        origin = self.headers.getheader('origin') or "<null>"
        if origin != "https://ide.onelang.io" and origin != "http://ide.onelang.io" and not origin.startswith("http://127.0.0.1:") and not origin.startswith("http://localhost:"):
            self.resp(403, { "exceptionText": "Origin is not allowed: " + origin, "errorCode": "origin_not_allowed" })
            return False
        return True

    def do_OPTIONS(self):
        if not self.originCheck(): return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", self.headers.getheader('origin'))
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "authentication")
        self.end_headers()
            

    def do_POST(self):
        try:
            if not self.originCheck(): return

            global requireToken, token
            if requireToken and self.headers.getheader('authentication') != "Token %s" % token:
                return self.resp(403, { "exceptionText": "Authentication token is invalid", "errorCode": "invalid_token" })

            pathParts = self.path.split('?', 1)
            self.path = pathParts[0]
            self.qs = pathParts[1] if len(pathParts) > 1 else ""
            self.queryParams = {}
            for keyValue in self.qs.split('&'):
                keyValueParts = keyValue.split("=", 1)
                self.queryParams[keyValueParts[0]] = keyValueParts[1] if len(keyValueParts) > 1 else True

            if self.path == '/compiler_versions':
                self.api_compiler_versions()
            elif self.path == '/compile':
                self.api_compile()
            elif self.path == '/status':
                self.api_status()
            else:
                self.resp(403, { "exceptionText": "API endpoint was not found: " + self.path, "errorCode": "endpoint_not_found" })            
        except Exception as e:
            log(repr(e))
            self.resp(400, { 'exceptionText': traceback.format_exc() })

log("Starting onelang.io CompilerBackend on port %d..." % PORT)
if requireToken:
    log("Please use this token for authentication:")
    log("  ===>   %s   <===" % token)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    """Handle requests in a separate thread."""

log("Press Ctrl+C to exit.")

try:
    ThreadedHTTPServer(("0.0.0.0" if allowRemote else "127.0.0.1", PORT), HTTPHandler).serve_forever()
except KeyboardInterrupt:
    pass

for langName in LANGS:
    lang = LANGS[langName]
    if not "subp" in lang: continue

    log("Send stop signal to %s compiler" % langName)
    lang["subp"].communicate("\n")
    log("Waiting for %s compiler to stop..." % langName)
    lang["subp"].wait()

log("Exiting...")
