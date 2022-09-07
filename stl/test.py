#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cadquery as cq
from cadquery import exporters

result = cq.Workplane().box(10, 10, 10)

exporters.export(result, "/home/jcress/code/planter/stl/mesh.stl")
exporters.export(result, "~/mesh.stl")
exporters.export(result, "/home/jcress/mesh.stl")
