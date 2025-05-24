import os
from sys import modules
import zipfile
import random

import boto3
import sagemaker
import numpy as np
import pandas as pd
from ai.deepAR.deep_ar_input import DeepARInput
from ai.deepAR.model_evaluation import ModelEvaluation
import uuid

from ai.deepAR.model_evaluation_entry import ModelEvaluationEntry
from ai.deepAR.predictor import predictor_session


class DatasetImport: 
    def import_dataset(self, boto_session: boto3.Session, sagemaker_session: sagemaker.Session, deepAR_input: DeepARInput):
        np.random.seed(42)
        random.seed(42)

        s3_bucket = sagemaker.Session(boto_session).default_bucket()
        session_id = uuid.uuid1()
        predictor_session.set_session_id(session_id)
        s3_prefix = str(session_id)

        region = sagemaker_session.boto_region_name
        print(region)

        s3_data_path = "s3://{}/{}/data".format(s3_bucket, s3_prefix)
        s3_output_path = "s3://{}/{}/output".format(s3_bucket, s3_prefix)

        image_name = sagemaker.image_uris.retrieve("forecasting-deepar", region)

        DATA_HOST = f"sagemaker-example-files-prod-{region}"
        DATA_PATH = "datasets/timeseries/gooddata/"
        ARCHIVE_NAME = "insight_data.csv"
        FILE_NAME = ARCHIVE_NAME
        
        s3_client = boto_session.client("s3")

        print(os.path.isfile(FILE_NAME))

        s3_client.upload_file(ARCHIVE_NAME, s3_bucket, DATA_PATH + ARCHIVE_NAME)

        if not os.path.isfile(FILE_NAME):
            print("downloading dataset, can take a few minutes depending on your connection")
            s3_client.download_file(DATA_HOST, DATA_PATH + ARCHIVE_NAME, ARCHIVE_NAME)

            print("\nextracting data archive")
            zip_ref = zipfile.ZipFile(ARCHIVE_NAME, "r")
            zip_ref.extractall("./")
            zip_ref.close()
        else:
            print("File found skipping download")

        data = pd.read_csv(FILE_NAME, sep=",", index_col=0, parse_dates=True, decimal=",")        
        num_timeseries = data.shape[1]
        data_kw = data.resample("1D").sum()
        timeseries = []
        for i in range(num_timeseries):
            timeseries.append(np.trim_zeros(data_kw.iloc[:, i], trim="f"))

        print(timeseries)

        predictor_session.set_timeseries(timeseries)
        
        ModelEvaluation().model_evaluation(model_evaluation_entry=ModelEvaluationEntry(
            boto_session=boto_session, 
            sagemaker_session=sagemaker_session, 
            s3_output_path=s3_output_path,
            s3_bucket=s3_bucket, 
            s3_data_path=s3_data_path, 
            s3_prefix=s3_prefix, 
            timeseries=timeseries,
            image_name=image_name,
            deepAR_input=deepAR_input
        ))
