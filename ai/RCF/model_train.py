from sagemaker import RandomCutForest

from ai.RCF.endpoint import EndpointPredictor
from ai.RCF.model_train_entry import ModelTrainEntry


class ModelTrain: 
    def train_model(self, model_train_entry: ModelTrainEntry): 
        iam = model_train_entry.boto_session.client('iam')
        role = iam.get_role(RoleName='AmazonSageMaker-ExecutionRole')['Role']['Arn']

        rcf = RandomCutForest(
            role=role,
            sagemaker_session=model_train_entry.sagemaker_session,
            instance_count=1,
            instance_type="ml.m4.xlarge",
            data_location=f"s3://{model_train_entry.bucket}/{model_train_entry.prefix}/",
            output_path=f"s3://{model_train_entry.bucket}/{model_train_entry.prefix}/output",
            num_samples_per_tree=512,
            num_trees=50,
        )

        rcf.fit(rcf.record_set(model_train_entry.data.value.to_numpy().reshape(-1, 1)))
        
        EndpointPredictor().createEndpoint(rcf=rcf)
