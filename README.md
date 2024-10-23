# GoodData Cloud backend

Flask-based application to gather and update GDC settings and additionally train/deploy RCF, DeepAR ml-models
[![](https://mermaid.ink/img/pako:eNptkdFLwzAQxv-VEF8UOh3iEIoI2wqbyKBon7Q-3JrrGrbmYnJllm3_u-m6qQ_mKXzfd7_L5XayIIUyluWGtkUFjkWW5EaEM36fNp6pFqUjw2jUh3gYDB738yxLb8bpk3D42aDnvZhcnpJLKNYhKPJA4Er7ELHkNZNrr3roRHSItOWKjHhNnn8h092MSCXAIKYbanpIgFnShg999fRY_YLekvEYGudGRrJGV4NWYYhdF8slV1hjLuNwVeDWuYxOuuYNZmQX4Fba9IHb0Y-9BDdHvar45Az_OjOwnXx3RpFNQSltVp16PzrJXiv8T2dS0Ia2a3Q93LOjNQ62WnEVj-xX1AvxBZTDiCwUmtt4eB0el5tDmBEaptfWFDJm12AkG6uAMdGwclDLuISND6oF80ZUn0Oouq9f9As-7vnwDRMWowM?type=png)](https://mermaid.live/edit#pako:eNptkdFLwzAQxv-VEF8UOh3iEIoI2wqbyKBon7Q-3JrrGrbmYnJllm3_u-m6qQ_mKXzfd7_L5XayIIUyluWGtkUFjkWW5EaEM36fNp6pFqUjw2jUh3gYDB738yxLb8bpk3D42aDnvZhcnpJLKNYhKPJA4Er7ELHkNZNrr3roRHSItOWKjHhNnn8h092MSCXAIKYbanpIgFnShg999fRY_YLekvEYGudGRrJGV4NWYYhdF8slV1hjLuNwVeDWuYxOuuYNZmQX4Fba9IHb0Y-9BDdHvar45Az_OjOwnXx3RpFNQSltVp16PzrJXiv8T2dS0Ia2a3Q93LOjNQ62WnEVj-xX1AvxBZTDiCwUmtt4eB0el5tDmBEaptfWFDJm12AkG6uAMdGwclDLuISND6oF80ZUn0Oouq9f9As-7vnwDRMWowM)


## Implemented functionality

- main page 
  - status display
- `/export?ws="workspace_id"&db="dashboard_id"&vis="visual_id&type="PDF""`
  - exports predefined report as a PDF / PPT / ...
- `/ws?action="{type}"&id="feature_id"&name="if_to_be_changed"`
  - action **view**: displays workspace tree structure (if id submitted only the corresponding sub-part)
  - action **create**: creates a new workspace (if no name defined, name = id)
  - action **manage**: changes name of a workspace
  - action **delete**: deletes a workspace
  - action **export**: exports workspace defintion (name specifies yaml/json - default)
- `/provision?source="workspace_id"&target="workspace_id"`
  - creates a copy of current workspace
- `/create-deepAR?workspace_id=&insight_id=&prediction_length=90&context_length=90`
  - train model for a specific visual
  - p

Main prototype use-case, that serves as an interchange layer between Custom frontend (https://github.com/davidzoufaly/fe-dd-hackathon-23) and a GoodData Cloud instance (https://www.gooddata.com/trial/)


## Installation

I. How to run locally:

1. navigate to `cd backend/gd-flask` folder.
2. create virtual environment: `python3.11 -m venv flask`
3. activate virtual environment: `source ./flask/bin/activate`
4. install dependencies from requirements.txt: `pip install -r requirements.txt`
5. create a copy of .env file `.env.test` by default.
6. run flask: `flask --debug run`

II. Continuation of the steps to train the AWS DeepAR model:

1. prepare line chart where trend by date should be grouped daily.
2. create AmazonSageMaker execution role.
3. make training request navigating to `http://localhost:5000/create-deepAR?workspace_id=&insight_id=&prediction_length=90&context_length=90`, where: values of `workspace_id` and `insight_id` should be provided from panther gd cloud, `prediction_length` is how far model should predict, `context_length` is the number of time-points that the model gets to see before making the prediction on web. Wait until endpoint deployed in the AmazonSageMaker service.
4. make prediction request using endpoint: `http://localhost:5000/predict-deepAR?timeserie=0&stop_endpoint=True` where `timeserie` is trend index, `stop_endpoint` is parameter which stops SageMaker session's endpoint to avoid unnecessary costs and stores values to PostgresSQL database. It's recommended to make requests from developed DeepAr dashboard plugin for these purposes which is located on the repo in this path: `frontend/plugins/gd-deepar`

How to deploy application:

1. install `eb cli`
2. connect to aws command line interface: `eb init`
3. redeploy the application: `eb deploy gd-ml-flask-dev`

## Missing features

- Not currently fetching request headers (Bearer token will be part of that) = token endpoint is hardcoded upon run
- Main page is about to display all endpont status and will allow functionality (/ws, /provision)
- AI (DeepAR + RCF) needs to be re-done - will offer more options in the future 
