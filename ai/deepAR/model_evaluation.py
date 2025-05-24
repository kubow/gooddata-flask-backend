import os
from sys import modules
import json
from datetime import timedelta
from dotenv import dotenv_values
import pandas as pd

from ai.deepAR.model_evaluation_entry import ModelEvaluationEntry
from ai.deepAR.model_train import ModelTrain, ModelTrainEntry
from ai.deepAR.predictor import predictor_session

env_file = dotenv_values(".env")


def write_dicts_to_file(path, data):
    with open(path, "wb") as fp:
        for d in data:
            fp.write(json.dumps(d).encode("utf-8"))
            fp.write("\n".encode("utf-8"))


def copy_to_s3(local_file, s3_path, s3, s3_bucket, override=False):
    assert s3_path.startswith("s3://")
    split = s3_path.split("/")
    bucket = split[2]
    path = "/".join(split[3:])
    buk = s3.Bucket(bucket)

    if len(list(buk.objects.filter(Prefix=path))) > 0:
        if not override:
            print(
                "File s3://{}/{} already exists.\nSet override to upload anyway.\n".format(
                    s3_bucket, s3_path
                )
            )
            return
        else:
            print("Overwriting existing file")
    with open(local_file, "rb") as data:
        print("Uploading file to {}".format(s3_path))
        buk.put_object(Key=path, Body=data)


class ModelEvaluation:
    def model_evaluation(self, model_evaluation_entry: ModelEvaluationEntry):
        freq = "1D"

        prediction_length = model_evaluation_entry.deepAR_input.prediction_length

        context_length = model_evaluation_entry.deepAR_input.context_length

        start_dataset = pd.Timestamp(predictor_session.get_timeseries()[0].keys()[0], freq=freq)
        end_training = pd.Timestamp(predictor_session.get_timeseries()[0].keys()[-1], freq=freq)

        print(start_dataset)
        print(end_training)

        training_data = [
            {
                "start": str(start_dataset),
                "target": ts[
                          start_dataset: end_training - timedelta(days=1)
                          ].tolist(),
            }
            for ts in model_evaluation_entry.timeseries
        ]
        print(len(training_data))

        num_test_windows = 4

        print(prediction_length)

        test_data = [
            {
                "start": str(start_dataset),
                "target": ts[start_dataset: end_training + timedelta(days=k * prediction_length)].tolist(),
            }
            for k in range(1, num_test_windows + 1)
            for ts in model_evaluation_entry.timeseries
        ]
        print(len(test_data))

        write_dicts_to_file("train.json", training_data)
        write_dicts_to_file("test.json", test_data)

        s3 = model_evaluation_entry.boto_session.resource("s3")

        copy_to_s3("train.json", model_evaluation_entry.s3_data_path + "/train/train.json", s3,
                   model_evaluation_entry.s3_bucket)
        copy_to_s3("test.json", model_evaluation_entry.s3_data_path + "/test/test.json", s3,
                   model_evaluation_entry.s3_bucket)

        s3_sample = \
            s3.Object(model_evaluation_entry.s3_bucket,
                      model_evaluation_entry.s3_prefix + "/data/train/train.json").get()[
                "Body"].read()
        StringVariable = s3_sample.decode("UTF-8", "ignore")
        lines = StringVariable.split("\n")
        print(lines[0][:100] + "...")

        ModelTrain().train_model(train_model_entry=ModelTrainEntry(
            boto_session=model_evaluation_entry.boto_session,
            sagemaker_session=model_evaluation_entry.sagemaker_session,
            image_name=model_evaluation_entry.image_name,
            s3_output_path=model_evaluation_entry.s3_output_path,
            s3_data_path=model_evaluation_entry.s3_data_path,
            freq=freq,
            context_length=context_length,
            prediction_length=prediction_length,
        ))
