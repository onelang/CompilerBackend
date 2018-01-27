echo
echo '    ===> Building Java in-memory compiler <==='
echo
pushd InMemoryCompilers/Java > /dev/null
mvn compile
mkdir lib/ 2> /dev/null
cp ~/.m2/repository/com/google/code/gson/gson/2.8.1/gson-2.8.1.jar lib/
popd > /dev/null

echo
echo '    ===> Building C# in-memory compiler <==='
echo
pushd InMemoryCompilers/CSharp > /dev/null
dotnet build
popd > /dev/null

echo
echo '    ===> Installing npm dependencies <==='
echo
npm i
