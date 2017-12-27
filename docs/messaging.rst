Messaging
=========

Dent runs its events off a messaging system. You can hook into this in order
to access system events such as keyboard input, mouse input and timers. Even
more, you can insert messages into the queue. This is the recommended way to
communicate between elements of your game.

Dent also saves a log of the message queue every time your game is run.

If you use messaging for all non-deterministic interactions in your game (random
die rolls for example), then Dent will be able to read a message log as a game
replay.  This is useful for debugging.

To fire an event, call::

  message = dent.messaging.Message('event_name', ('some', 'data'))
  dent.messaging.add_message(message)

Here we have made an event of type `event_name` and with two data.

To add a handler, simply call::

  dent.messaging.add_handler('event_name', handler_func)

The hander function must expect exactly the data that will be in the event.
Thus, in the above case it must take two parameters. The handler will be called
with ``some`` and ``data`` as the parameters, given the previous message.

Naturally there can be mulitple handlers for the same event from different parts
of the system. Thus, for example, a weapon object and the camera object might
define hooks for keyboard input.

Default Messages
----------------

Dent fires off a number of messages that you may write hooks for.  They are

================ ======================================== ============================================
Message Type     Description                              Arguments
================ ======================================== ============================================
``mouse``        A mouse button has been clicked          The mouse button, state and xy coordinates
``mouse_motion`` The mouse has moved                      The xy coordinates of the mouse
``keyboard``     A key has been pressed                   The pressed key character
``keyboard_up``  A key has been released                  The released key character
``timer``        Fired every timer tick                   The current number of frames per second
``game_start``   Fired once at the beginning of the game  None
================ ======================================== ============================================

API
---

.. automodule:: dent.messaging
    :members:
    :undoc-members:
    :show-inheritance:
