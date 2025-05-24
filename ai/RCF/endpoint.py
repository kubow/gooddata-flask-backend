from sagemaker import RandomCutForest
from sagemaker.serializers import CSVSerializer
from sagemaker.deserializers import JSONDeserializer

from ai.RCF.predictor import predictor_session


class EndpointPredictor:
    def createEndpoint(self, rcf: RandomCutForest):
        rcf_inference = rcf.deploy(initial_instance_count=1, instance_type="ml.t2.medium")

        rcf_inference.serializer = CSVSerializer()
        rcf_inference.deserializer = JSONDeserializer()
        
        predictor_session.set_predictor(rcf_inference)
