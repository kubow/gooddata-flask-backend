
class ModelEvaluationEntry:
  def __init__(self, boto_session, sagemaker_session, s3_output_path, s3_bucket, s3_prefix, s3_data_path, timeseries, image_name, deepAR_input):
    self.boto_session = boto_session
    self.sagemaker_session = sagemaker_session
    self.s3_output_path = s3_output_path
    self.s3_bucket = s3_bucket
    self.s3_prefix = s3_prefix
    self.s3_data_path = s3_data_path
    self.timeseries = timeseries
    self.image_name = image_name
    self.deepAR_input = deepAR_input
