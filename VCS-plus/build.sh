if [ -d bin ]; then
    rm -rf bin
fi
mkdir bin
javac src/*.java src/tc/wata/*/*.java -d bin

#  [Last modified: 2018 01 11 at 15:30:28 GMT]
