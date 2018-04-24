"""Debugging procedures for dent games.

This module contains functions enabled by passing the ``-d`` or ``--debug`` flags on
the command line.  They may slow down performance."""

import dent.args
import dent.messaging
import dent.Shaders

t = 0


def reload_shaders(fps):
    global t
    if int(t + 1. / fps) != int(t):
        dent.Shaders.reload_all()
    t += 1. / fps


def initialise_debug():
    if dent.args.args.debug:
        dent.messaging.add_handler("timer", reload_shaders)
