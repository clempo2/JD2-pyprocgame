from procgame.game import Mode

class ModeTimer(Mode):
    """timer for a timed mode"""

    def __init__(self, game, priority):
        super(ModeTimer, self).__init__(game, priority)
        self.timer = 0

    def mode_stopped(self):
        self.stop_timer()

    def start_timer(self, time, delay_time=1):
        # Tell the mode how much time it gets, if it cares.
        self.timer_update(time)
        self.timer = time
        self.delay_time = delay_time
        self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)

    def stop_timer(self):
        self.timer = 0
        self.cancel_delayed('decrement timer')

    def reset_timer(self, time, delay_time=1):
        # assign a new deadline and align the handler on the delay boundary
        self.stop_timer()
        self.start_timer(time, delay_time)

    def add_time(self, time):
        self.timer += time

    def pause(self):
        self.cancel_delayed('decrement timer')

    def resume(self):
        if self.timer > 0:
            self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)

    def decrement_timer(self):
        if self.timer > 0:
            self.timer -= 1
            self.delay(name='decrement timer', event_type=None, delay=self.delay_time, handler=self.decrement_timer)
            self.timer_update(self.timer)
        else:
            self.expired()

    def expired(self):
        pass

    def timer_update(self, time):
        pass
