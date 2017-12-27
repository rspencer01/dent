Actions and Animations
======================

Any :class:`~dent.Object.Object` may have a
:class:`~dent.ActionController.ActionController` assigned to it.
If so, this action controller will take control if the object's
:attr:`~dent.Object.Object.position` and :attr:`~dent.Object.Object.angle`.

You add animations to an action controller through the object, calling
:attr:`~dent.Object.Object.add_animation()`. The action controller will at all
times select an animation and apply it to the object.

Currently animations `must` be humanoid with a ``Hips`` bone at the root, as
the motion of this bone will be used as the basis of the motion of the object
itself.

When an action completes, the action controller will select a new action to
apply to the object. This will be chosen according to some `weights`. By default
the weights of the actions are all equal, but you can override this by supplying
a :attr:`~dent.ActionController.ActionController.action_weight` function.
