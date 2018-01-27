touch .secret_token && docker run -a stdin -a stdout -p 127.0.0.1:11111:11111/tcp -i -v $(pwd)/.secret_token:/one/.secret_token --restart unless-stopped -t onelang_compiler_backend
