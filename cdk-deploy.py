#!/usr/bin/env python3
import os

from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_iam
)

import aws_cdk as core
from constructs import Construct
from dotenv import load_dotenv


class SheetGPTStack(core.Stack):

    def __init__(self, scope: Construct, id: str, oai_key: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cache_bucket = s3.Bucket(self, "SheetGPTCache",
                                 versioned=False,
                                 removal_policy=core.RemovalPolicy.DESTROY, )

        # lambda layer to keep dependencies away from main code
        # to keep it editable in UI no matter how many packages are there in the deps
        lambda_layer = _lambda.LayerVersion(self, 'sheetgpt-requirements',
                                            code=_lambda.Code.from_asset("cdk.out/custom-build/reqs",
                                                                         bundling=core.BundlingOptions(
                                                                             image=_lambda.Runtime.PYTHON_3_8.bundling_image,
                                                                             command=[
                                                                                 "bash", "-c",
                                                                                 "pip install --no-cache -r requirements.txt -t /asset-output/python && cp -au . /asset-output/python"
                                                                             ],
                                                                         ),
                                                                         ),
                                            compatible_runtimes=[_lambda.Runtime.PYTHON_3_8], )
        sgpt_fn = _lambda.Function(
            self, 'SheetGPTLambda',
            environment={
                "OPENAI_API_KEY": oai_key,
                "S3_BUCKET": cache_bucket.bucket_name
            },
            runtime=_lambda.Runtime.PYTHON_3_8,
            layers=[lambda_layer],
            code=_lambda.Code.from_asset("cdk.out/custom-build/lambda", ),
            handler='sheetgpt.lambda_handler',
            memory_size=256,
            timeout=core.Duration.minutes(1)
        )

        cache_bucket.grant_read_write(sgpt_fn)
        sgpt_fn.add_permission("InvokeLambda",
                               principal=aws_iam.AnyPrincipal(),
                               action="lambda:InvokeFunctionUrl",
                               function_url_auth_type=_lambda.FunctionUrlAuthType.NONE,
                               )
        lambda_url = _lambda.CfnUrl(self, "LambdaUrl",
                                    target_function_arn=sgpt_fn.function_arn,
                                    auth_type="NONE",
                                    cors={
                                        "allowCredentials": False,
                                        "allowMethods": ["*"],
                                        "allowOrigins": ["*"]
                                    }
                                    )

        core.CfnOutput(self, "TheUrl",
                       # The .url attributes will return the unique Function URL
                       value=lambda_url.attr_function_url
                       )


app = core.App()

# on CI/CD, pass OpenAI key in the environment, or just use local .env file
if 'OPENAI_API_KEY' not in os.environ:
    load_dotenv()
SheetGPTStack(app, "SheetGPTApp", os.environ['OPENAI_API_KEY'])
app.synth()
