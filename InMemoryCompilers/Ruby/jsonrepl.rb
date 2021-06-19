require 'json'
require 'stringio'

trap 'INT' do exit end
$stdout.sync = true
$realStdout = $stdout
    
def resp(result)
    result["backendVersion"] = "one:ruby:jsonrepl:20180122"
    $realStdout.puts(JSON.generate(result))
end

while requestLine = gets
    begin
        $stdout = StringIO.new
        request = JSON.parse(requestLine)
        fileNames = request["packageSources"].map{|x| x["fileName"].sub(".rb", "")}

        def evalCode(code, fileNames)
            for fn in fileNames do
                code = code.sub("require '#{fn}'", "")
            end
            eval code
        end

        evalCode(request['stdlibCode'], fileNames) if request['stdlibCode']
        for pkgSource in request["packageSources"] do
            evalCode(pkgSource["code"], fileNames)
        end
        result = evalCode(request['code'], fileNames)
        resp({ :result => $stdout.string })
    rescue Exception
        resp({ :exceptionText => "#{$@.first}: #{$!.message} (#{$!.class})" + $@.drop(1).map{|s| "\n\t#{s}"}.join("") })
    ensure
        $stdout = $realStdout
    end
end
