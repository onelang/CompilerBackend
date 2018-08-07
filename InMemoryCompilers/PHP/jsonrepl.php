<?php

function resp($result) {
    $result["backendVersion"] = "one:php:server:20180122";
    print json_encode($result);
    exit;
}

$stdin = fopen("php://stdin", "r");

function exception_error_handler($errno, $errstr, $errfile, $errline) {
    throw new ErrorException($errstr, $errno, 0, $errfile, $errline);
}

set_error_handler("exception_error_handler");

function fatal_handler() {
    $errfile = "unknown file";
    $errstr  = "shutdown";
    $errno   = E_CORE_ERROR;
    $errline = 0;

    $error = error_get_last();

    if($error !== NULL) {
        $errno   = $error["type"];
        $errfile = $error["file"];
        $errline = $error["line"];
        $errstr  = $error["message"];

        $result = ob_get_clean();
        resp(array("result" => $result, "exceptionText" => "line #{$errline}: {$errstr}")) . "\n";
    }
}

register_shutdown_function("fatal_handler");

$requestIdx = 0;
while (true) {
    $line = trim(fgets($stdin));
    if (!$line) break;

    try {
        $requestIdx++;
        $request = json_decode($line, true);
        if ($request["cmd"] === "exit") break;
    
        $sources = array("main.php" => $request["code"]);
        foreach ($request["packageSources"] as $pkgSrc)
            $sources[$pkgSrc["fileName"]] = $pkgSrc["code"];

        $code = "";
        foreach ($sources as $fileName => $source)
            $code .= str_replace(array("<?php", "?>"), "", $source);
        
        foreach ($sources as $fileName => $source)
            $code = str_replace('require_once("'.$fileName.'");', "", $code);
            
        ob_start();
        eval("namespace Request$requestIdx;$code");
        $result = ob_get_clean();
        resp(array("result" => $result)) . "\n";
    } catch(Error $e) {
        $result = ob_get_clean();
        resp(array("result" => $result, "exceptionText" => "line #{$e->getLine()}: {$e->getMessage()}\n{$e->getTraceAsString()}")) . "\n";
    }
}
