# GoodData Cloud backend

Flask-based appication to gather and update GDC settings.

## Implemented functionality

- index page - status display
- `/export?ws="workspace_id"&db="dashboard_id"&vis="visual_id"`
  - exports predefined report as a PDF
- `/ws?action="{type}"&id="feature_id"&name="if_to_be_changed"`
  - action **view**: displays workspace tree structure (if id submitted only the corresponding sub-part)
  - action **create**: creates a new workspace (if no name defined, name = id)
  - action **manage**: changes name of a workspace
  - action **delete**: deletes a workspace
  - action **export**: exports workspace defintion (name specifies yaml/json - default)
- `/provision?source="workspace_id"&target="workspace_id"`
  - creates a copy of current workspace

This is just a prototype, that serves as an interchange layer between Custom frontend (https://github.com/davidzoufaly/fe-dd-hackathon-23) and a GoodData Cloud instance (https://www.gooddata.com/trial/)

[![](https://mermaid.ink/img/pako:eNptkdFLwzAQxv-VEF8UOh3iEIoI2wqbyKBon7Q-3JrrGrbmYnJllm3_u-m6qQ_mKXzfd7_L5XayIIUyluWGtkUFjkWW5EaEM36fNp6pFqUjw2jUh3gYDB738yxLb8bpk3D42aDnvZhcnpJLKNYhKPJA4Er7ELHkNZNrr3roRHSItOWKjHhNnn8h092MSCXAIKYbanpIgFnShg999fRY_YLekvEYGudGRrJGV4NWYYhdF8slV1hjLuNwVeDWuYxOuuYNZmQX4Fba9IHb0Y-9BDdHvar45Az_OjOwnXx3RpFNQSltVp16PzrJXiv8T2dS0Ia2a3Q93LOjNQ62WnEVj-xX1AvxBZTDiCwUmtt4eB0el5tDmBEaptfWFDJm12AkG6uAMdGwclDLuISND6oF80ZUn0Oouq9f9As-7vnwDRMWowM?type=png)](https://mermaid.live/edit#pako:eNptkdFLwzAQxv-VEF8UOh3iEIoI2wqbyKBon7Q-3JrrGrbmYnJllm3_u-m6qQ_mKXzfd7_L5XayIIUyluWGtkUFjkWW5EaEM36fNp6pFqUjw2jUh3gYDB738yxLb8bpk3D42aDnvZhcnpJLKNYhKPJA4Er7ELHkNZNrr3roRHSItOWKjHhNnn8h092MSCXAIKYbanpIgFnShg999fRY_YLekvEYGudGRrJGV4NWYYhdF8slV1hjLuNwVeDWuYxOuuYNZmQX4Fba9IHb0Y-9BDdHvar45Az_OjOwnXx3RpFNQSltVp16PzrJXiv8T2dS0Ia2a3Q93LOjNQ62WnEVj-xX1AvxBZTDiCwUmtt4eB0el5tDmBEaptfWFDJm12AkG6uAMdGwclDLuISND6oF80ZUn0Oouq9f9As-7vnwDRMWowM)

## Missing features

- Not currently fetching request headers (Bearer token will be part of that) = token endpoint is hardcoded upon run
- Main page is about to display all endpont status and will allow functionality (/ws, /provision)
