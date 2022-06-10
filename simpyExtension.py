#from simpy.core import *
import simpy
from simpy.resources import resource
from simpy.core import BoundClass, Environment, SimTime
from typing import TYPE_CHECKING, Any, List, Optional, Type
from types import TracebackType
from simpy.resources import base
import copy
from enum import Enum

counter = 0


class WorkerStatus(Enum):
    OnBreak = 1
    OnJob = 2
    Idle = 3


class MyEvent():
    def __init__(self):
        self.start = None
        self.end = None
        self.id = None

class BreakEvent(MyEvent):
    def __init__(self, worker_id: int):
        super(BreakEvent, self).__init__()
        self.start = WorkerStatus.OnBreak
        self.end = WorkerStatus.Idle
        self.id = worker_id


class NewJobEvent(MyEvent):
    def __init__(self, worker_id = None, job_id = None):
        super(NewJobEvent, self).__init__()
        self.start = WorkerStatus.OnJob
        self.end = WorkerStatus.Idle
        self.worker_id = worker_id
        self.job_id = job_id
    def __str__(self):
        return f'job {self.job_id}'


# now lets use call back to change status
class Worker:
    def __init__(self, id, start, end):
        self.start = 0
        self.end = end
        self.free = 0
        self.isFree = True
        self.status = WorkerStatus.Idle
        self.id = id
        self.job_id = None

    def is_free(self, time, duration):
        return time + duration < self.end

    def add_job(self, duration):
        self.free = self.free + duration
        self.isFree = False

    def change_status(self, value: WorkerStatus):
        self.status = value

    def change_status_by_event_start(self, request: 'MyPreemptimeRequest'):
        event = request.event
        print(event.start)
        self.status = event.start

    def change_status_by_event_end(self, request: 'MyPreemptimeRequest'):
        event = request.event
        self.status = event.end

    def __str__(self):
        f = f'worker {self.id} status {self.status} on job {self.job_id}'
        return f

# the event object contains worker information
class MyPreemptimeRequest(resource.PriorityRequest):
    def __init__(
            self, resource: 'MyPriorityResource', event: MyEvent = None, priority: int = 0, preempt: bool = True
    ):
        global counter
        self.id = copy.deepcopy(counter)
        counter = counter + 1
        self.event = event
        super().__init__(resource, priority, preempt=True)
# i can also reqeust a specific resource
    def __str__(self):
        if (isinstance(self.event, NewJobEvent)):
            s = f'job {self.event.job_id} is waiting'
            return s
        return ''


class WorkerCollection:
    def __init__(self):
        self.collection = []
    def add(self, worker: Worker):
        self.collection.append(worker)
    def __getitem__(self, idx):
        return self.collection[idx]
    def len(self):
        return len(self.collection)

    def get_free_worker(self):
        for worker in self.collection:
            if worker.status == WorkerStatus.Idle:
                return worker
        return None





class MyPriorityRequest(resource.PriorityRequest):
    def __init__(
        self, resource: 'MyPriorityResource',  event: MyEvent = None, priority: int = 0, preempt: bool = True
    ):
        global counter
        self.id = copy.deepcopy(counter)
        counter = counter + 1
        self.event = event
        super().__init__(resource, priority, preempt = False)
    def __str__(self):
        if isinstance(self.event, NewJobEvent):
            s = f'priority is {self.priority} for job {self.event.__str__()}'
        else:
            s = f'priority is {self.priority}'
        return  s
    def update_key(self):
        self.key = (self.priority, self.time, not self.preempt)




# relese will call put again for more jobs
class MyRelease(resource.Release):
    worker: Worker
    def __init__(self, resource: 'Resource', request: MyPriorityRequest):
        self.worker = request.value
        super().__init__(resource, request)


class MyPreemptiveResouce(resource.PreemptiveResource):
    def __init__(self, env: simpy.Environment, workers: WorkerCollection):
        self.workers = workers
        capacity = workers.len()
        # when this is true, we will preempt a resource even list is not full if we must use this resource
        self.strickUserChoice = True
        super().__init__(env, capacity)


    def _do_put(  # type: ignore[override] # noqa: F821
        self, event: MyPreemptimeRequest
    ) -> None:
        # if I want a specifc worker, even capcity is not full, I can still preemp
        # how do I know which requet to preemp?
        newRequestEvent = event.event
        newRequestedWorker = None
        preempNotFull = False
        # this can be used as a prefereed user
        if (self.strickUserChoice):
            if newRequestEvent and isinstance(newRequestEvent, NewJobEvent):
                if newRequestEvent.worker_id is not None:
                    # a request is a job as a user
                    id = newRequestEvent.worker_id
                    newRequestedWorker = self.workers[id]
                for preempt in self.users:
                    requestEvent = preempt.event
                    if requestEvent and isinstance(requestEvent, NewJobEvent):
                        currentWorker = preempt._value
                        if newRequestedWorker == currentWorker:
                            if preempt.key > event.key:
                                # this user is busy, but we can inrrupt
                                currentWorker.change_status(requestEvent.end)
                                self.users.remove(preempt)
                                preempt.proc.interrupt(  # type: ignore
                                        resource.Preempted(
                                            by=event.proc,
                                            usage_since=preempt.usage_since,
                                            resource=self,
                                        )
                                    )
                                preempNotFull = True
                                break
        # a normal preempt, onl preempt when  resoures are full
        if not preempNotFull and (len(self.users) >= self.capacity and event.preempt):
            # Check if we can preempt another process
            preempt = sorted(self.users, key=lambda e: e.key)[-1]
            if preempt.key > event.key:
                # need to free the preep user
                print(f'preemp request id is {preempt.id}')
                requestEvent = preempt.event
                if requestEvent and isinstance(requestEvent, BreakEvent):
                    # preemp is a break event, time to change the status here?
                    worker_id = requestEvent.id
                    self.workers[worker_id].change_status(requestEvent.end)
                if requestEvent and isinstance(requestEvent, NewJobEvent):
                    # preemp is a break event, time to change the status here?
                    worker = preempt._value
                    worker.change_status(requestEvent.end)



                self.users.remove(preempt)
                preempt.proc.interrupt(  # type: ignore
                    resource.Preempted(
                        by=event.proc,
                        usage_since=preempt.usage_since,
                        resource=self,
                    )
                )
        # the reqeut contains the event type object
        # event here is a request
        requestEvent = event.event
        preassigned_worker = None
        if requestEvent and isinstance(requestEvent, NewJobEvent):
            if requestEvent.worker_id is not None:
                # I request a specific worker
                id = requestEvent.worker_id
                worker = self.workers[id]

                if worker.status != WorkerStatus.Idle:
                    # this will proceed to next request on the put_queue see if we can satisify next request
                    # if I dont have to use this worker, just find the next free worker
                    # this means this request will wait until this user become free, otherwise it will be on the put_queue forever
                    if self.strickUserChoice:
                        return True
                else:
                    preassigned_worker = worker

        #assert (preassigned_worker == None)
        if len(self.users) < self.capacity:
            self.users.append(event)
            event.usage_since = self._env.now
            # request should know which worker has the job
            # todo
            # choose an idle user, or the best sutible idle worker

            if requestEvent and isinstance(requestEvent, BreakEvent):
                # meet this break request, change status to on break
                worker_id = requestEvent.id
                self.workers[worker_id].change_status(requestEvent.start)
                event.succeed()
            if requestEvent and isinstance(requestEvent, NewJobEvent):
                # if it is a new job event, need to assign the correct worker
                # assign the worker to the request succeed
                if preassigned_worker:
                    w = preassigned_worker

                else:
                    w = self.workers.get_free_worker()
                requestEvent.id = w.id
                event.succeed(w)
                # change status to onjob
                w.change_status(requestEvent.start)

    # odd is here
    def _do_get(self, event: MyRelease) -> None:
        try:
            # change worer state
            # the release should hold the infomration of the worker
            # my release knows the request
            request = event.request
            requestEvent = request.event
            # break is finished
            if (event.request in self.users):
                # at this point, any request will know which worker took the request
                worker_id = requestEvent.id
                self.workers[worker_id].change_status(requestEvent.end)

                #if requestEvent and isinstance(requestEvent, BreakEvent):
                #    worker_id = requestEvent.id
                    # change status to idle
                #    self.workers[worker_id].change_status(requestEvent.end)
                #if requestEvent and isinstance(requestEvent, NewJobEvent):
                    # here the request event also know the worker
                    #worker = request._value
                #    worker = workers[requestEvent.id]
                    # change status to idle
                #    worker.change_status(requestEvent.end)
            self.users.remove(event.request)  # type: ignore
        except ValueError:
            pass
        # relse event know which worker to release
        event.succeed()

    request = BoundClass(MyPreemptimeRequest)
    release = BoundClass(MyRelease)

class MyPriorityResource(simpy.PriorityResource):

    def __init__(self, env: simpy.Environment, workers: 'stage_1_workers'):
        self.workers = workers
        capacity = workers.len()
        super().__init__(env, capacity)

    def _do_put(self, event: MyPriorityRequest) -> None:
        # no preemption, just get most important request


        if len(self.users) < self.capacity:
            self.users.append(event)
            event.usage_since = self._env.now
            requestEvent = event.event
            if requestEvent and isinstance(requestEvent, BreakEvent):
                # meet this break request, change status to on break
                worker_id = requestEvent.id
                self.workers[worker_id].change_status(requestEvent.start)
                event.succeed()  # break event dont need return value
            if requestEvent and isinstance(requestEvent, NewJobEvent):
                # step 1, just get a free worker if possible

                w = self.workers.get_free_worker()
                requestEvent.id = w.id
                event.succeed(w)
                # change status to onjob
                w.change_status(requestEvent.start)

    def _do_get(self, event: MyRelease) -> None:
        try:
            # change worer state
            # the release should hold the infomration of the worker
            # my release knows the request
            request = event.request
            requestEvent = request.event
            # break is finished
            if (event.request in self.users):
                # at this point, any request will know which worker took the request
                worker_id = requestEvent.id
                self.workers[worker_id].change_status(requestEvent.end)

                #if requestEvent and isinstance(requestEvent, BreakEvent):
                #    worker_id = requestEvent.id
                    # change status to idle
                #    self.workers[worker_id].change_status(requestEvent.end)
                #if requestEvent and isinstance(requestEvent, NewJobEvent):
                    # here the request event also know the worker
                    #worker = request._value
                #    worker = workers[requestEvent.id]
                    # change status to idle
                #    worker.change_status(requestEvent.end)
            self.users.remove(event.request)  # type: ignore
        except ValueError:
            pass
        # relse event know which worker to release
        event.succeed()

    request = BoundClass(MyPriorityRequest)
    release = BoundClass(MyRelease)
