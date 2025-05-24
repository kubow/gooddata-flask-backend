class ModelTrainEntry: 
    def __init__(self, boto_session, sagemaker_session, bucket, prefix, data):
        self.boto_session = boto_session
        self.sagemaker_session = sagemaker_session
        self.bucket = bucket
        self.prefix = prefix
        self.data = data
        