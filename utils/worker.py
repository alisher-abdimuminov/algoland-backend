from threading import Thread


class Worker(Thread):
    def __init__(self, function: any, *args):
        self.function = function
        self.args = args
        super().__init__()

    def run(self):
        self.function(*self.args)
