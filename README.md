# GoodData Cloud backend

Flask-based appication to gather and update GDC settings.

## Implemented functionality

- index page - status display
- `/ws?action="{type}"&id="feature_id"&name="if_to_be_changed"`
  - action **view**: displays workspace tree structure (if id submitted only the corresponding sub-part)
  - action **create**: creates a new workspace (if no name defined, name = id)
  - action **manage**: changes name of a workspace
  - action **delete**: deletes a workspace
  - action **export**: exports workspace defintion (name specifies yaml/json - default)
- `/provision?source="workspace_id"&target="workspace_id"`
  - creates a copy of current workspace

This is just a prototype, that serves as an interchange layer between GDC and custom forntend (https://github.com/davidzoufaly/fe-dd-hackathon-23)
