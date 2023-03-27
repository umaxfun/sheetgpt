#!/bin/bash

if [ $# -eq 0 ]; then
  echo "Usage: $0 <cache_entry>"
  echo "  cache_entry could be found in in error output or logs (CloudWatch Logs / logs.sh)"
  exit 1
fi

# set path to template file
template_file="cdk.out/SheetGPTApp.template.json"

# get the bucket name from the template
bucket_name=$(jq -r '(.Resources | with_entries(select(.value.Type == "AWS::S3::Bucket")) | keys)[0]' cdk.out/SheetGPTApp.template.json "${template_file}" | head -1)

# echo "cfn ${bucket_name}"
bucket_name=$(aws s3 ls | grep -i "${bucket_name}" | awk '{ print $3 }')
#echo "s3 ${bucket_name}"
prefix="cache/$1"

#echo "s3://${bucket_name}/${prefix}"
aws s3 cp "s3://${bucket_name}/${prefix}" - | jq