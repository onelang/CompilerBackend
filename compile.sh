set -e
echo
echo '    ===> Building Java in-memory compiler <==='
echo
cd InMemoryCompilers/Java
mvn compile
mkdir lib/ 2> /dev/null && exit 0
cp ~/.m2/repository/com/google/code/gson/gson/2.8.1/gson-2.8.1.jar lib/
cd ../../

echo
echo '    ===> Building C# in-memory compiler <==='
echo
cd InMemoryCompilers/CSharp
dotnet build
cd ../../

echo
echo '    ===> Installing npm dependencies <==='
echo
npm i
