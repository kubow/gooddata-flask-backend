from dotenv import dotenv_values
import psycopg2
from datetime import datetime


def db_conn(env_file: str = ".env"):
    environment = dotenv_values(env_file)
    conn = psycopg2.connect(
        host=environment["POSTGRES_DB_HOST"],
        database=environment["POSTGRES_DB_NAME"],
        user=environment["POSTGRES_DB_USER"],
        password=environment["POSTGRES_DB_PASSWORD"]
    )

    return conn


class PredictorSession():
    __predictor = None
    __timeseries = None
    __id = None
    __is_endpoint_stopped = False

    def get_session_id(self):
        return self.__id

    def set_session_id(self, id):
        self.__id = id

    def set_predictor(self, predictor):
        self.__predictor = predictor

    def set_timeseries(self, timeseries):
        self.__timeseries = timeseries

    def get_predictor(self):
        return self.__predictor

    def get_timeseries(self):
        return self.__timeseries

    def stop_endpoint(self):
        self.__is_endpoint_stopped = True
        self.__predictor.delete_model()
        self.__predictor.delete_endpoint()

    def get_is_endpoint_stopped_state(self):
        return self.__is_endpoint_stopped


predictor_session = PredictorSession()


class Predictor:
    def predict(self, timeserie, stop_endpoint):
        conn = db_conn()
        id = predictor_session.get_session_id()

        if (predictor_session.get_is_endpoint_stopped_state() == True):
            cur = conn.cursor()
            cur.execute(f'''
                SELECT prediction_session_id, date, low_bound, low_bound_confidence, prediction, prediction_confidence, high_bound, high_bound_confidence
                FROM sagemaker.deepar_predictions
                WHERE prediction_session_id = '{id}';
            ''')
            stored_predictions = cur.fetchall()
            low_bound_confidence = float(stored_predictions[0][3])
            prediction_confidence = float(stored_predictions[0][5])
            high_bound_confidence = float(stored_predictions[0][7])
            result = {
                low_bound_confidence: {},
                prediction_confidence: {},
                high_bound_confidence: {}
            }

            for row in stored_predictions:
                print("row: ", row)
                timestamp = int(datetime.strptime(f"{row[1]}", "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
                result[low_bound_confidence][timestamp] = float(row[2])
                result[prediction_confidence][timestamp] = float(row[4])
                result[high_bound_confidence][timestamp] = float(row[6])

            cur.close()
            conn.close()

            print("res: ", result)

            return result

        confidence = 95

        assert confidence > 50 and confidence < 100
        low_quantile = 0.5 - confidence * 0.005
        up_quantile = confidence * 0.005 + 0.5

        args = {
            "ts": predictor_session.get_timeseries()[timeserie],
            "return_samples": False,
            "quantiles": [low_quantile, 0.5, up_quantile],
            "num_samples": 100,
        }

        prediction = predictor_session.get_predictor().predict(**args)
        print(prediction)

        insertVals = []
        for timestamp in prediction.index:
            # time = datetime.fromtimestamp(int(f"{timestamp}") / 1000).strftime('%Y-%m-%d %H:%M:%S')
            print("time")
            print(timestamp)
            insert = f"('{id}', timestamp '{timestamp}'"
            for col in prediction.columns:
                insert += f", {prediction._get_value(timestamp, col)}, {col}"
            insert += ")"
            insertVals.append(insert)

        insertVals = ', '.join(insertVals)
        insertVals += ";"

        print("insert: ", insertVals)

        if (stop_endpoint == True):
            predictor_session.stop_endpoint()
            cur = conn.cursor()
            cur.execute(f'''
                INSERT INTO sagemaker.deepar_predictions (prediction_session_id, date, low_bound, low_bound_confidence, prediction, prediction_confidence, high_bound, high_bound_confidence) VALUES {insertVals}
            ''')
            conn.commit()
            cur.close()
            conn.close()

        return prediction.to_json()

        # prediction = predictor_session.get_predictor().predict(ts=predictor_session.get_timeseries()[int(timeserie)], quantiles=[0.10, 0.5, 0.90]).head()
