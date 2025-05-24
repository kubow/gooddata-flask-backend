from ai.deepAR.predictor import predictor_session


class CleanUp:
    def clean_up(self):
        predictor = predictor_session.get_predictor()
        predictor.delete_model()
        predictor.delete_endpoint()
