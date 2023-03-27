# executes before `cdk deploy` as defined in cdk.json
# copies lambda layer with requirements and lambda function 
# into cdk.out to prepare for packaging

rm -rf ./cdk.out/custom-build/
mkdir -p ./cdk.out/custom-build/lambda
cp sheetgpt.py ./cdk.out/custom-build/lambda

mkdir -p ./cdk.out/custom-build/reqs
cp requirements.txt ./cdk.out/custom-build/reqs