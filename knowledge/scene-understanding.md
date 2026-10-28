# Scene Understanding

Parse a scene into a coordinate frame, walkable ground, dominant anchors, entrances/exits, occluders, and depth layers. Use primitives with stable ids so camera and action plans can refer to them. Keep the horizon and floor readable; avoid decorative geometry that competes with the cast.

The scene manifest supports CUBE, CYLINDER, GATE, GRID, STAIRS, and BRIDGE. Add a new primitive only when it carries staging or camera meaning.
