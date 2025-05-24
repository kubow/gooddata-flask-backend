import json
import pandas as pd


class PredictorSession: 
    __predictor = None
    __data = None

    def set_predictor(self, predictor):
        self.__predictor = predictor

    def set_data(self, data):
        self.__data = data

    def get_predictor(self):
        return self.__predictor
    
    def get_data(self):
        return self.__data

predictor_session = PredictorSession()

class Predictor: 
    def predict(self):
        data = predictor_session.get_data()
        data_numpy = data.value.to_numpy().reshape(-1, 1)
        results = predictor_session.get_predictor().predict(data_numpy)
        scores = [datum["score"] for datum in results["scores"]]
        
        data["score"] = pd.Series(scores, index=data.index)
        data.head()

        start, end = 0, len(data)
        data_subset = data[start:end]
        score_mean = data["score"].mean()
        score_std = data["score"].std()
        score_cutoff = score_mean + 3 * score_std

        anomalies = data_subset[data_subset["score"] > score_cutoff]

        anomaly_detection = { "data": data.to_json(), "anomalies": anomalies.to_json() }
        
        return json.dumps(anomaly_detection, indent=4)
