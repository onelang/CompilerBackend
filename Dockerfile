FROM ubuntu:16.04

MAINTAINER Tamas Koczka <koczkatamas@gmail.com>

RUN apt-get update
RUN apt-get install -qqy python
RUN apt-get install -qqy ruby
RUN apt-get install -qqy php
RUN apt-get install -qqy perl
RUN apt-get install -qqy default-jdk
RUN apt-get install -qqy maven
RUN apt-get install -qqy mono-mcs
RUN apt-get install -qqy golang-go
RUN apt-get install -qqy nano
RUN apt-get install -qqy clang libicu-dev
RUN apt-get install -qqy wget

RUN wget https://swift.org/builds/swift-4.0-release/ubuntu1604/swift-4.0-RELEASE/swift-4.0-RELEASE-ubuntu16.04.tar.gz
RUN tar xzf swift-4.0-RELEASE-ubuntu16.04.tar.gz -C /
ENV PATH="/swift-4.0-RELEASE-ubuntu16.04/usr/bin:${PATH}"
RUN rm swift-4.0-RELEASE-ubuntu16.04.tar.gz

ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
RUN apt-get install -qqy apt-transport-https && \
    wget -O - https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg && \
    sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-xenial-prod xenial main" > /etc/apt/sources.list.d/dotnetdev.list' && \
    apt-get update && \
    apt-get install -qqy dotnet-sdk-2.1.3

RUN wget -O - https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get install -qqy nodejs
    
RUN mkdir /one
WORKDIR /one
COPY compile.sh compiler_backend.py package.json package-lock.json ./
COPY InMemoryCompilers ./InMemoryCompilers

RUN ./compile.sh

EXPOSE 11111

CMD ["./compiler_backend.py"]
