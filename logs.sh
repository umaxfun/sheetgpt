#!/bin/bash
# finds the name of deployed lambda function and starts live log tail
# requires `awslogs` command to present (pip install awslogs)

#set -x
ID=$(jq -r '(.Resources | with_entries(select(.value.Type == "AWS::Lambda::Function")) | keys)[0]' cdk.out/SheetGPTApp.template.json)
LOGG=$(aws logs describe-log-groups --query logGroups\[\*\].logGroupName --no-cli-pager | jq -r --arg ID "$ID" '.[] | select(contains($ID))')
awslogs get $LOGG ALL --watch

