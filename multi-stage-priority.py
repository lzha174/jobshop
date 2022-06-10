import datetime

import simpy

from simpyExtension import *
import draw
import collections
from jobclass import *

job_data_type= collections.namedtuple('job_data', 'stage duration priority')

job_set = JobCollection()

def get_my_resource_preemp(env, id, current_stage_res, job: Job, specifc_worker = None):
        w = None
        worker_id = specifc_worker
        yield env.timeout(job.arrival - env.now)
        print (f'job {id} arrive at {env.now}')
        mid_day = 15

        # go throuch each stage in job data
        for idx, data in enumerate(job.data_array):
            done_in = data.duration
            priority = data.priority
            stage = data.stage
            stage_res = current_stage_res[stage]
            # for stage 0, if time is before 15, make 2-hour job high priroity
            if stage == 0: # pretend this is a pre-batcing stage
                if job.isTwoHour:
                    if env.now < mid_day:
                        priority = 0
                else:
                    if env.now > mid_day:
                        priority = 0
                    # this means if a pre-batching job comes before time 15, make it high piroity for next avlaible worker
            while done_in:
                with stage_res.request(priority=priority, event = NewJobEvent(worker_id = worker_id, job_id = id)) as req:
                    try:
                        start = env.now
                        # I can get intruppted here by a break at the same time, I yield, then break will intrurpt this process at this point
                        worker = yield req
                        w = worker
                        start = env.now

                        debug_output(f'stage {stage} job {id} priority {priority} get resouece worker {worker.id} at  {draw.format_time(env.now)}')
                        try:
                            job_set[id].add_stat(stage_idx=idx, start=env.now)
                            yield env.timeout(done_in)
                            done_in = 0
                            debug_output(f'stage {stage} job {id} finish at {env.now}')

                        except simpy.Interrupt as interrupt:
                            done_in -= env.now - start  # How much time left?
                            by = interrupt.cause.by
                            usage = env.now - interrupt.cause.usage_since
                            worker_id = w.id

                            debug_output(f' {id} got preempted by {by} at {env.now} ' f' after {usage} with {done_in} left')
                    except simpy.Interrupt as interrupt:
                        done_in -= env.now - start  # How much time left?
                        by = interrupt.cause.by
                        usage = env.now - interrupt.cause.usage_since

                        debug_output(f' {id} got preempted by {by} at {env.now} ' f' after {usage} with {done_in} left')
            job_set[id].add_stat(stage_idx=idx, end=env.now)

def break_process(env, resource:MyPriorityResource = None, worker_id: int = 0, stage = 1, start = 3, duration = 3):
    # insert a breat at time 5 and last 5
    yield env.timeout(start)
    with resource.request(priority = -3, event = BreakEvent(worker_id)) as req:
        yield req
        # I want to know which worker start break
        print(f'stage {stage} worker {worker_id} start break at {(env.now)}')
        yield env.timeout(duration)
        print(f'stage {stage} worker {worker_id}  break finish at {(env.now)}')

def monitor(env, resource: MyPreemptiveResouce):
    for i in range(10):
        yield env.timeout(1)
        print(f' worker is free {resource.workers[0].isFree} at time {env.now}')


def get_time(mins):
    day = mins // 1440
    hour = (mins - day * 1440) / 60
    t = f'day {day} hour {hour}'
    return t

seconds_per_min = 60
min_per_hour = 60
day_in_seconds = 60 * 24 * 60
seconds_per_hour = 60 * 60

def debug_output(str):
    show = False
    if show:
        print(str)

def create_jobs():
    # create 10 jobs for each hour


    nbHours = 1
    global job_set
    for i in range(nbHours):
        duration = 36 # seconds
        priority = 0
        arrival = seconds_per_hour * i
        for j in range(1):
            job = Job(id=len(job_set.jobs), arrival=arrival);
            job.add_stage(stage=0, duration=duration, priority=0)
            job.add_stage(stage=1, duration=duration, priority=0)
            job.add_stage(stage=0, duration=duration, priority=0)
            job.add_stage(stage=1, duration=duration, priority=0)
            job.add_stage(stage=0, duration=duration, priority=0)
            job.add_stage(stage=1, duration=duration, priority=0)
            #job.add_stage(stage=1, duration=duration, priority=0)
            job_set.add(id=len(job_set.jobs), job=job)

step = seconds_per_hour * 2;
def load_next_job_set(env: simpy.Environment, stage_resources, period = step ):
    load_next = True

    while env.now < 5 * day_in_seconds:
        at_least_one = False
        last_period = period - step
        job_included = []
        for key, job in job_set.jobs.items():
            arrival = job.arrival
            if last_period<= arrival < env.now + step:
                job_included.append(key)
                env.process(get_my_resource_preemp(env, key, stage_resources, job))
                at_least_one =True
        if not at_least_one:
            load_next = False
        print(f'load jobs {job_included}')
        yield env.timeout(step)
        period = period + step


def jobs():
    start = 0
    end = 100


    day_index = 0
    sec =  30
    job = Job(arrival = sec)
    job.add_stage(stage=0, duration=15, priority=0)
    job.add_stage(stage=1, duration=15, priority=0)

    job_set.add(id =0, job=job)


    sec =  35
    job = Job(arrival = sec)
    job.add_stage(stage=0, duration=15, priority=0)
    job.add_stage(stage=1, duration=15, priority=0)
    job_set.add(id=1, job=job)

    sec =  40
    job = Job(arrival = sec, isTwoHour=True)
    job.add_stage(stage=0, duration=15, priority=-1)
    job.add_stage(stage=1, duration=15, priority=0)
    job_set.add(id=2, job=job)

    #create_jobs()

    env = simpy.Environment()
    stages = [0, 1]

    nb_stage_workers = [1, 1]

    stage_resources = {}
    for idx, stage in enumerate(stages):
        current_stage_workers = WorkerCollection()
        for i in range(nb_stage_workers[idx]):
            current_stage_workers.add(Worker(i, start, end))
        stage_resources[stage] = MyPriorityResource(env, current_stage_workers)


    # a day has 30 seconds, every day stage 2 workers only work between 12-20
    procs = [env.process(load_next_job_set(env, stage_resources))]
    
    procs.append(env.process(break_process(env, stage_resources[0], stage = 0, worker_id=0, start=35, duration = 10)))
    stage = 1
    #procs.append(env.process(break_process(env, stage_resources[stage], stage=stage, worker_id=0, start=60, duration=10)))
    #procs.append(env.process(break_process(env, stage_resources[1], stage=1, worker_id=0, start=20, duration=5)))
    id = 0
    for key, job in job_set.jobs.items():
        specific_worker = None
        if id == 0:
            specific_worker = 1
        #procs.append(env.process(get_my_resource_preemp(env, key, stage_resources, job, specifc_worker=specific_worker)))
        id = id + 1


    env.run()

a = datetime.datetime.now()


jobs()


b = datetime.datetime.now()

r = job_set.get_stat()
print('time elapsed is,', b - a)
#for key, v in r.items():
#    print(key, v)
draw.draw_gannt(r)

# when I all put and get, it is easy to just modify my resources immediately, coz it is hard to know when callback will happen in right order