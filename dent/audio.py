import dent.messaging
import openal

openal.oalSetStreamBufferCount(2)

streams = {}

to_play = set()


def stream_update(fps):
    global to_play
    for i in streams.values():
        if i.get_state() == openal.AL_PLAYING:
            i.update()
    for n in to_play:
        streams[n].play()
    to_play = set()


dent.messaging.add_handler("timer", stream_update)


def play_sound(name, path, gain=1.):
    if name not in streams:
        streams[name] = openal.oalStream(path)
    streams[name].set_gain(gain)
    to_play.add(name)
