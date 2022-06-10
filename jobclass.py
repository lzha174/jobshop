import typing
import draw
class Stage:
    def __init__(self, stage, duration, priority = 0):
        self.duration = duration
        self.priority = priority
        self.stage = stage
        self.start = None
        self.end = None
        self.finish = False

class Job:
    def __init__(self, id = 0, arrival = 0, isTwoHour = False):
        self.data: typing.Dict[int, Stage] = {}
        self.data_array: list[Stage] = []
        self.arrival = arrival
        self.isTwoHour = isTwoHour
        self.id = id

    def add_stage(self, stage, duration, priority = 0):
        s = Stage(stage=stage, duration=duration, priority=priority)
        self.data_array.append(s)
        self.data[stage] = s

    def add_stat(self, stage_idx, start = None, end = None):
        if (start != None):
            self.data_array[stage_idx].start =start
        if (end != None):
            self.data_array[stage_idx].end = end
            self.data_array[stage_idx].finish = True

    def get_stat(self):
        # return tuple (stage, start, duration)
        result = []
        for s in self.data_array:
            assert(s.finish != None)
            assert(s.start != None)
            result.append((s.stage, s.start, s.duration))
            start_time = draw.format_time(s.start)
            end_time = draw.format_time(s.end)
            print(f'job {self.id} start {start_time} end {end_time}')
        return result






class JobCollection:
    def __init__(self):
        self.jobs: typing.Dict[int, Job]   = {}
    def add(self, id, job: Job):
        self.jobs[id] = job

    def __getitem__(self, idx):
        return self.jobs[idx]

    def isNewJob(self, key):
        if key in self.jobs:
            return False
        return True

    def get_stat(self):
        # loop every job
        result = {}
        for id, job in self.jobs.items():
            r = job.get_stat()
            result[id] = r
        return result

