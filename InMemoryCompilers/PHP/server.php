<?php

header("Access-Control-Allow-Origin: *");

function resp($result) {
    $result["backendVersion"] = "one:php:server:20180122";
    print json_encode($result);
    exit;
}

$origin = isset($_SERVER["HTTP_ORIGIN"]) ? $_SERVER["HTTP_ORIGIN"] : "<null>";
if ($origin !== "https://ide.onelang.io" && strpos($origin, "http://127.0.0.1:") !== 0) {
    resp(array("exceptionText" => "Origin is not allowed: " . $origin, "errorCode" => "origin_not_allowed"));
}

function exception_error_handler($errno, $errstr, $errfile, $errline) {
    throw new ErrorException($errstr, $errno, 0, $errfile, $errline);
}

set_error_handler("exception_error_handler");

function fatal_handler() {
    $error = error_get_last();
    if($error !== NULL) {
        $errno   = $error["type"];
        $errfile = $error["file"];
        $errline = $error["line"];
        $errstr  = $error["message"];

        $result = ob_get_clean();
        print json_encode(array("result" => $result, "exceptionText" => "line #{$errline}: {$errstr}"));
    }
}

register_shutdown_function("fatal_handler");

try {
    $request = json_decode(file_get_contents("php://input"), true);
    
    $includes = array("one.php");
    $sources = array($request["code"]);
    foreach ($request["packageSources"] as $pkgSrc) {
        $includes[] = $pkgSrc["fileName"];
        $sources[] = $pkgSrc["code"];
    }

    $code = "";
    foreach ($sources as $source)
        $code .= str_replace(array("<?php", "?>"), "", $source);
    
    foreach ($includes as $include)
        $code = str_replace('require_once("'.$include.'");', "", $code);
    
    $className = $request["className"];
    $methodName = $request["methodName"];
    
    print "executing code: " . $code;

    ob_start();
    $startTime = microtime(true);
    eval($code);
    $elapsedMs = (int)((microtime(true) - $startTime) * 1000);
    $result = ob_get_clean();
    resp(array("result" => $result, "elapsedMs" => $elapsedMs));
} catch(Error $e) {
    $result = ob_get_clean();
    resp(array("result" => $result, "exceptionText" => "line #{$e->getLine()}: {$e->getMessage()}\n{$e->getTraceAsString()}"));
} catch(Exception $e) {
    $result = ob_get_clean();
    resp(array("result" => $result, "exceptionText" => "line #{$e->getLine()}: {$e->getMessage()}\n{$e->getTraceAsString()}"));
}
