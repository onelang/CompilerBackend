const readline = require("readline");
const process = require("process");
const vm = require("vm");
const ts = require("typescript");
const util = require("util");

function requireFromString(src, filename) {
    var Module = module.constructor;
    var m = new Module();
    m._compile(src, filename);
    return m.exports;
}

function tsCompile(code) {
    return ts.transpileModule(code, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
}

function resp(result) {
    result["backendVersion"] = "one:tsjs:jsonrepl:20180122";
    console.log(JSON.stringify(result));
}

readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false }).on('line', requestLine => {
    try {
        //console.error(requestLine);
        const requestJson = JSON.parse(requestLine);

        let code = requestJson.code;
        let stdlibCode = requestJson.stdlibCode || "";
        if (requestJson.lang === "typescript") {
           code = "// TS CODE\n" + tsCompile(code);
           stdlibCode = tsCompile(stdlibCode);
        }

        let result = "";
        const script = new vm.Script(code);
        const context = new vm.createContext({ 
            console: {
                log: (...args) => result += (util.format(...args) + '\n'),
            },
            require: (...args) => {
                const fullFn = `${args[0]}.js`;
                const pkgSource = requestJson.packageSources.find(x => `${x.packageName}/${x.fileName}` === fullFn);
                const result = pkgSource ? requireFromString(pkgSource.code, fullFn) : require(...args);
                console.error(`require: "${fullFn}" ->`, result);
                return result;
            }
        });

        script.runInContext(context);
        resp({ result });
    } catch(e) {
        resp({ exceptionText: `${e}\n\n${e.stack}` });
    }
});
