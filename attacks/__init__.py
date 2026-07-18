"""Reference attack library.

Each subpackage groups attacks by the boundary they target.
A new attack should subclass :class:`attacks.base.Attack` and implement
``setup``/``execute``/``teardown``.
"""