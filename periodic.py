import asyncio
import cakeshow
import roster
import arrow
import messaging
from config import config
import prose


class Event:
    def __init__(self, duration=0, func=None):
        self.func_to_call = func
        self.duration = duration  # in minutes

    async def run(self):
        if self.func_to_call is not None:
            await self.func_to_call()
            return arrow.utcnow().shift(minutes=self.duration)
        else:
            print("Couldn't run a queued non-function")
            return arrow.utcnow()

async def send_elimination_warning():
    desc = "The judges meet in their soundproof chambers to discuss the rankings... :warning:"
    desc += "\n" + prose.random('elimination_warning.yaml')
    await messaging.send_general_message("THE JUDGES DELIBERATE...", desc)


async def send_bracket_warning():
    desc = "A new bracket begins."
    await messaging.send_general_message("A NEW BRACKET BEGINS!", desc)


class Periodic:
    def __init__(self):
        self.events = []
        self.hold_event_queue_until = arrow.utcnow()
        self.hold_show_until = arrow.utcnow()
        self.shows_since_last_elimination = 0
        self.brackets_remaining = config.brackets_before_shutdown-1

    def remove_event(self, event):
        self.events.remove(event)

    def add_event(self, event):
        self.events.append(event)

    async def update(self):
        if self.hold_event_queue_until >= arrow.utcnow():
            return
        elif self.hold_event_queue_until < arrow.utcnow() and len(self.events) > 0:
            self.hold_event_queue_until = await self.events[0].run()
            self.remove_event(self.events[0])
        else:
            if self.hold_show_until < arrow.utcnow():
                if len(cakeshow.shows) == 0:
                    if self.shows_since_last_elimination < get_matches_before_elimination():
                        if len(roster.players) > 2:
                            await cakeshow.start_random_show()
                        else:
                            await cakeshow.start_final_show()
                        delay = config.interval
                        if len(roster.players) >= 5:
                            delay = delay*0.5
                        self.hold_show_until = arrow.utcnow().shift(minutes=delay)
                    else:
                        self.shows_since_last_elimination = 0
                        await roster.eliminate_player()
                        if len(roster.players) >= 5:
                            await roster.eliminate_player()
                        self.hold_show_until = arrow.utcnow().shift(minutes=min(config.interval, 5))
                        if len(roster.players) == 1:
                            self.events = []  # CLEAR the event queue!
                            await cakeshow.finish_bracket()
                            if self.brackets_remaining > 0:
                                await cakeshow.new_bracket()
                                self.brackets_remaining += -1
                            else:
                                await messaging.send_general_message("THAT'S ALL SHE WROTE.", "Thanks for coming! The final bracket has concluded.")

                else:
                    await cakeshow.finish_show()
                    self.hold_show_until = arrow.utcnow().shift(minutes=min(config.interval, 2))
                    self.shows_since_last_elimination += 1
                    if self.shows_since_last_elimination >= get_matches_before_elimination() and len(roster.players) > 2:
                        schedule_new_event(func=send_elimination_warning, duration=min(config.interval, 1))


def get_matches_before_elimination():
    length = len(roster.players)
    if length >= 6:
        return 6
    if length >= 4:
        return 2
    if length >= 3:
        return 2
    if length >= 2:
        return 1

def schedule_new_event(duration=0, func=None):
    global periodic
    new_event = Event(duration=duration, func=func)
    periodic.add_event(new_event)


periodic = Periodic()


