import boto3
import botocore
import sagemaker
import pandas as pd
import os

from ai.RCF.model_train import ModelTrain
from ai.RCF.model_train_entry import ModelTrainEntry
from ai.RCF.predictor import predictor_session


class DatasetImport: 
    def import_dataset(self, boto_session: boto3.Session, sagemaker_session: sagemaker.Session):
        bucket = (
            sagemaker_session.default_bucket()
        )
        prefix = "sagemaker/rcf-benchmarks"

        # S3 bucket where the original data is downloaded and stored.
        downloaded_data_bucket = f"{bucket}"
        downloaded_data_prefix = "datasets/tabular/anomaly_gd_insight"

        def check_bucket_permission(bucket):
            # check if the bucket exists
            permission = False
            try:
                boto_session.client("s3").head_bucket(Bucket=bucket)
            except botocore.exceptions.ParamValidationError as e:
                print(
                    "Hey! You either forgot to specify your S3 bucket"
                    " or you gave your bucket an invalid name!"
                )
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "403":
                    print(f"Hey! You don't have permission to access the bucket, {bucket}.")
                elif e.response["Error"]["Code"] == "404":
                    print(f"Hey! Your bucket, {bucket}, doesn't exist!")
                else:
                    raise
            else:
                permission = True
            return permission


        if check_bucket_permission(bucket):
            print(f"Training input/output will be stored in: s3://{bucket}/{prefix}")
        if check_bucket_permission(downloaded_data_bucket):
            print(
                f"Downloaded training data will be read from s3://{downloaded_data_bucket}/{downloaded_data_prefix}"
            )

        s3 = boto_session.client("s3")
        filename = "insight_data.csv"
        data_filename = "training_data.csv"

        data = pd.read_csv(filename, delimiter=",")
        training_data = data.rename(columns={data.keys()[0]: "timestamp", data.keys()[1]: "value"})

        training_data.to_csv("training_data.csv", index=False)

        s3.upload_file(data_filename, bucket, f"{downloaded_data_prefix}/{data_filename}")
        s3.download_file(downloaded_data_bucket, f"{downloaded_data_prefix}/{data_filename}", data_filename)
            
        data = pd.read_csv(data_filename, delimiter=",")
        
        predictor_session.set_data(data)
        data.head()
        
        ModelTrain().train_model(model_train_entry=ModelTrainEntry(
            boto_session=boto_session, 
            sagemaker_session=sagemaker_session,
            bucket=bucket,
            prefix=prefix,
            data=data
        ))
