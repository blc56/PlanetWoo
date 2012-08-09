
.. _dist_multi:

Distributed Rendering Multiple Layers
======================================================

Overview
---------

PlanetWoo supports rendering multiple layers in a single pass. This is useful for rendering features and labels in a single pass while still storing the feature tiles and label tiles separately. 


Configfile
-----------

Instead of using the default Mapserver renderer, the config file is modified to use a ``MultiRenderer`` instead. Here are the attributes which are different than those documented :ref:`here <global_options_mapserver>`.

Global Options
--------------

We use the config file to override defaults for the following attributes.

cutter_type
 Must be ``"multi"``.

storage_type
 Must be ``"multi"``.

renderer_type
 Must be ``"multi"``.

Multi Specific Options
-----------------------

cutters
 When ``cutter_type`` is ``"multi"``, this is a list of configuration dictionaries for cutters, one per layer. :ref:`cutter_config`

storage_managers
 When ``storage_type`` is ``"multi"``, this is a list of configuration dictionaries for storage managers, one per layer. See: :ref:`storage_manager_config`


renderers
 When ``renderer_type`` is ``"multi"``, this is a list of configuration dictionaries for renderers, one per layer. See: :ref:`renderer_config`

