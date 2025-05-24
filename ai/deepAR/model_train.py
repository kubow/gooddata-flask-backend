import sagemaker

from ai.deepAR.endpoint_predictor import EndpointPredictor

class ModelTrainEntry: 
    def __init__(self, boto_session, sagemaker_session, image_name, s3_output_path, s3_data_path, freq, context_length, prediction_length):
        self.boto_session = boto_session
        self.sagemaker_session = sagemaker_session
        self.image_name = image_name
        self.s3_output_path = s3_output_path
        self.s3_data_path = s3_data_path
        self.freq = freq
        self.context_length = context_length
        self.prediction_length = prediction_length


class ModelTrain: 
    def train_model(self, train_model_entry: ModelTrainEntry): 
        iam = train_model_entry.boto_session.client('iam')
        role = iam.get_role(RoleName='AmazonSageMaker-ExecutionRole')['Role']['Arn']
        estimator = sagemaker.estimator.Estimator(
            image_uri=train_model_entry.image_name,
            sagemaker_session=train_model_entry.sagemaker_session,
            role=role,
            instance_count=1,
            instance_type="ml.c4.2xlarge",
            base_job_name="gooddata-demo",
            output_path=train_model_entry.s3_output_path,
        )
        hyperparameters = {
            "time_freq": train_model_entry.freq,
            "epochs": "400",
            "early_stopping_patience": "40",
            "mini_batch_size": "64",
            "learning_rate": "5E-4",
            "context_length": str(train_model_entry.context_length),
            "prediction_length": str(train_model_entry.prediction_length),
        }

        estimator.set_hyperparameters(**hyperparameters)

        data_channels = {"train": "{}/train/".format(train_model_entry.s3_data_path), "test": "{}/test/".format(train_model_entry.s3_data_path)}
        estimator.fit(inputs=data_channels, wait=True)

        EndpointPredictor().createEndpoint(estimator)
        