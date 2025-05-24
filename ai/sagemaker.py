from __future__ import print_function

from dotenv import dotenv_values

env_file = dotenv_values(".env")

import boto3
import sagemaker

boto_session = boto3.Session(
    aws_access_key_id=env_file["AWS_SERVER_PUBLIC_KEY"],
    aws_secret_access_key=env_file["AWS_SERVER_SECRET_KEY"],
    region_name="us-east-1"
)

sagemaker_session = sagemaker.Session(boto_session)
