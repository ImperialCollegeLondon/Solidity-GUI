"""Tests for detection of shared surfaces between volume elements."""

from itertools import combinations

from solidity_gui.main.geometry import get_shared_surfaces


def test_two_joined_boxes(geom):
    """Test shared surface detection with two fused boxes.

    Geometry shown below with *s for shared surfaces.

    -----*-----
    |    *    |
    |    *    |
    -----*-----
    """
    box1 = geom.add_box([0, 0, 0], [1, 1, 1])
    box2 = geom.add_box([1, 0, 0], [1, 1, 1])

    assert len(get_shared_surfaces([box1, box2])) == 0
    volumes = geom.boolean_fragments(box1, box2)
    shared_surfaces = get_shared_surfaces(volumes)
    assert shared_surfaces == {tuple(volumes)}


def test_two_joined_boxes_with_extra(geom):
    """Test shared surface detection with two fused boxes with an extra detached box.

    Geometry shown below with *s for shared surfaces.

    ------
    |    |
    |    |
    ------

    -----*-----
    |    *    |
    |    *    |
    -----*-----
    """
    geom.add_box([-10, -10, -10], [1, 1, 1])
    box1 = geom.add_box([0, 0, 0], [1, 1, 1])
    box2 = geom.add_box([1, 0, 0], [1, 1, 1])

    assert len(get_shared_surfaces([box1, box2])) == 0
    volumes = geom.boolean_fragments(box1, box2)
    shared_surfaces = get_shared_surfaces(volumes)
    assert len(shared_surfaces) == 1
    assert shared_surfaces == {tuple(volumes)}


def test_three_joined_boxes(geom):
    """Test shared surface detection with three fused boxes.

    Geometry shown below with *s for shared surfaces.

    ------
    |    |
    |    |
    ******-----
    |    *    |
    |    *    |
    -----*-----

    This arrangement has two shared surfaces.
    """
    boxes = [
        geom.add_box([0, 0, 0], [1, 1, 1]),
        geom.add_box([1, 0, 0], [1, 1, 1]),
        geom.add_box([0, 1, 0], [1, 1, 1]),
    ]

    assert len(get_shared_surfaces(boxes)) == 0
    geom.boolean_fragments([boxes[0]], boxes[1:])
    shared_surfaces = get_shared_surfaces(boxes)
    assert len(shared_surfaces) == 2

    for comb in [
        (boxes[0], boxes[1]),
        (boxes[0], boxes[2]),
    ]:
        assert comb in shared_surfaces or comb[::-1] in shared_surfaces


def test_three_staggered_joined_boxes(geom):
    """Test shared surface detection with three fused boxes in a staggered arrangement.

    Geometry shown below with *s for shared surfaces.

      -------
      |     |
      |     |
    --*******--
    |    *    |
    |    *    |
    -----*-----

    Under this arrangement each box should have a shared surface with the other two
    boxes.
    """
    boxes = [
        geom.add_box([0, 0, 0], [1, 1, 1]),
        geom.add_box([1, 0, 0], [1, 1, 1]),
        geom.add_box([0.5, 1, 0], [1, 1, 1]),
    ]

    assert len(get_shared_surfaces(boxes)) == 0

    geom.boolean_fragments(boxes[0], boxes[1:])

    shared_surfaces = get_shared_surfaces(boxes)
    assert len(shared_surfaces) == 3

    for comb in combinations(boxes, 2):
        assert comb in shared_surfaces or comb[::-1] in shared_surfaces


def test_four_joined_boxes(geom):
    """Test shared surface detection with four fused boxes.

    Geometry shown below with *s for shared surfaces.

    -----*-----
    |    *    |
    |    *    |
    ***********
    |    *    |
    |    *    |
    -----*-----

    Under this arrangement each box should have a shared surface with their vertical and
    horizontal but not diagonal neighbour.
    """
    boxes = [
        geom.add_box([0, 0, 0], [1, 1, 1]),
        geom.add_box([1, 0, 0], [1, 1, 1]),
        geom.add_box([0, 1, 0], [1, 1, 1]),
        geom.add_box([1, 1, 0], [1, 1, 1]),
    ]

    assert len(get_shared_surfaces(boxes)) == 0

    geom.boolean_fragments(boxes[0], boxes[1:])

    shared_surfaces = get_shared_surfaces(boxes)
    assert len(shared_surfaces) == 4

    for comb in [
        (boxes[0], boxes[1]),
        (boxes[0], boxes[2]),
        (boxes[1], boxes[3]),
        (boxes[2], boxes[3]),
    ]:
        assert comb in shared_surfaces or comb[::-1] in shared_surfaces
