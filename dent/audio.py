import dent.messaging
import openal

openal.oalSetStreamBufferCount(8)

streams = {}


def stream_update(fps):
    for i in streams.values():
        i.update()


dent.messaging.add_handler("timer", stream_update)


def play_sound(name, path, gain=1.):
    if name not in streams:
        streams[name] = openal.oalOpen(path)
    streams[name].set_gain(gain)
    streams[name].play()
