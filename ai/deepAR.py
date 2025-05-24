# from __future__ import print_function

from sys import modules

# from dotenv import dotenv_values

# from deepAR.dataset_import import DatasetImport

pass
# env_file = dotenv_values(".env")
#
# import boto3
# import sagemaker
#
#
# boto_session = boto3.Session(
#     aws_access_key_id=env_file["AWS_SERVER_PUBLIC_KEY"],
#     aws_secret_access_key=env_file["AWS_SERVER_SECRET_KEY"],
# )
#
# sagemaker_session = sagemaker.Session(boto_session)
#
# def deepAR(deepAR_input):
#     DatasetImport().import_dataset(boto_session, sagemaker_session, deepAR_input)
#
# modules[__name__] = deepAR
