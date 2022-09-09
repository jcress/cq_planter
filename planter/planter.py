#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

import cadquery as cq

_DIMS = [175, 175, 100]
_WALL = 5
_SIDES = 6


@dataclass
class base:
    """
    base of planter
    """

    dims: List[float] = field(default_factory=lambda: _DIMS)
    sides: int = _SIDES
    wall_thickness: int = _WALL

    def __post_init__(self):
        self.x, self.y, self.z = self.dims
        self.shape = cq.Workplane("XY").polygon(self.sides, self.x).extrude(
            self.z).faces("+Z").shell(self.wall_thickness).translate(
                cq.Vector(0, 0, self.wall_thickness))
        # todo: rescale when x != y


@dataclass
class insert:
    """
    define the insert
    """
    dims: List[float] = field(default_factory=_DIMS)
    sides: int = _SIDES
    wall_thickness: int = _WALL
    top_height: float = 20
    bottom_offset: float = .3

    def __post_init__(self):
        self.x, self.y, self.z = self.dims

        # basic shape
        self._xy_shape = (cq.Sketch().regularPolygon(n=self.sides,
                                                     r=int(self.x / 2)))

        # bottom
        self._bottom = (cq.Sketch().regularPolygon(n=self.sides,
                                                   r=int(self.x / 2) *
                                                   self.bottom_offset))

        self._hole = (cq.Sketch().trapezoid(7, 1, 111).fillet(0.5))

        # middle section
        self._middle = cq.Workplane().placeSketch(
            self._xy_shape.moved(cq.Location(cq.Vector(0, 0, self.z))),
            self._bottom).loft().faces("+Z").shell(self.wall_thickness *
                                                   -self.bottom_offset)

        # cut holes in bottom
        self._middle = self._middle.faces(">X and >Y").workplane().transformed(
            (0, 0, -90)).placeSketch(self._hole).cutThruAll()
        self._middle = self._middle.faces("<X and <Y").workplane().transformed(
            (0, 0, -90)).placeSketch(self._hole).cutThruAll()

        # top
        self._top = cq.Workplane("XY").placeSketch(
            self._xy_shape,
            self._xy_shape.moved(cq.Location(cq.Vector(0, 0,
                                                       self.top_height))),
        ).loft().faces("+Z or -Z").shell(self.wall_thickness).union(
            cq.Workplane("XY").placeSketch(
                self._xy_shape,
                self._xy_shape.moved(
                    cq.Location(cq.Vector(0, 0, self.top_height))),
            ).loft().faces("+Z or -Z").shell(-self.wall_thickness))

        self.shape = self._top.translate(cq.Vector(0, 0,
                                                   self.z)).union(self._middle)

        # cut holes
        self._holes = cq.Workplane("XY").transformed(
            offset=cq.Vector(0, -75, 10),
            rotate=cq.Vector(-90, 0, 90)).placeSketch(
                self._hole).extrude(150).rotateAboutCenter((0, 0, 1), 15)

        for i in range(12 * 6):
            self._holes = self._holes.union(
                cq.Workplane("XY").transformed(
                    offset=cq.Vector(0, -75, 10 * (i / 10 + 1)),
                    rotate=cq.Vector(-90, 0, 90)).placeSketch(
                        self._hole).extrude(150).rotateAboutCenter((0, 0, 1),
                                                                   15 * i))
        self.shape = self.shape.cut(self._holes)


def assembly(dims: List[float] = None):
    """assemble"""
    x, y, z = dims = _DIMS if dims is None else dims
    _base = base(dims=dims).shape
    _insert = insert(dims=dims).shape
    _out = (cq.Assembly().add(_base, name="base", color=cq.Color("red")).add(
        _insert, name="insert", color=cq.Color("blue")))
    _out.constrain("base@faces@Z", "insert@faces@<Z", "Plane")
    _out.constrain("insert", "FixedRotation", (0, 0, 90))
    _out.solve()

    # _out = _insert
    return _out


if __name__ == "__main__":
    import subprocess

    out = assembly()

    out_dir = subprocess.check_output("git rev-parse --show-toplevel",
                                      shell=True,
                                      text=True).rstrip()

    for s in range(3, 8):
        for ext in ['stl', 'svg']:
            _base = base(dims=_DIMS, sides=s).shape
            cq.exporters.export(_base, f"{out_dir}/stl/base_{s}.{ext}")
            _insert = insert(dims=_DIMS, sides=s).shape
            cq.exporters.export(_insert, f"{out_dir}/stl/insert_{s}.{ext}")

else:
    render = assembly()
    show_object(render)
