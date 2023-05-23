.. _import_asset:
.. |import_asset| image:: ../../../python/trigger/ui/icons/import_asset.png

===========================
Import Asset |import_asset|
===========================

Import Asset action is used to dynamically import any kind of asset into the build session. This is probably the most commonly used action in all Trigger sessions.

Any valid format can be brought in into the scene. Please note that, the import method is not using any namespaces and changes the names in case of
clashes. If you want to collect assets together sharing a similar hierarchy use Assemble action instead.

Valid formats are:

- Maya ASCII (.ma)
- Maya Binary (.mb)
- USD (.usd)
- Alembic (.abc)
- FBX (.fbx)
- OBJ (.obj)

This action has the following features:
    
    - **File Path**: Absolute path of the asset that is going to be brought in
    - **Scale**: Post Scale compensation of the asset. Always uses the world origin as scale pivot.
    - **Root Suffix**: Adds the value in here as suffix to the root group of imported asset
    - **Parent Under**: The imported asset will be parented under the node defined here if defined.
 
.. tip ::
    Import Asset Action does not use namespaces and changes names if a node already exists in the scene