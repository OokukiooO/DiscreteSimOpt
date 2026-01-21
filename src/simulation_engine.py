from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Dict

import simpy

from . import config
from .scheduler import Scheduler


@dataclass
class SimulationResult:
    job_id: int
    job_type: str
    arrival_time: float
    start_time: float
    end_time: float
    due_date: float
    tardiness: float
    machine: str


class JobShop:
    def __init__(self, jobs: List[Dict], strategy: str):
        self.jobs = jobs
        self.strategy = strategy
        self.env = simpy.Environment()
        self.scheduler = Scheduler(strategy=strategy)
        self.a_machine = simpy.PriorityResource(self.env, capacity=config.A_MACHINES)
        self.b_machine = simpy.PriorityResource(self.env, capacity=config.B_MACHINES)
        self.results: List[SimulationResult] = []
        self.h_arrivals = [j["arrival_time"] for j in self.jobs if j["job_type"] == "H"]
        self.h_arrivals.sort()
        self.h_in_b_system = 0

    def _next_h_arrival(self, now: float) -> float | None:
        for t in self.h_arrivals:
            if t > now:
                return t
        return None

    def _sample_process_time(self, job_type: str, machine: str) -> float:
        if machine == "A":
            a, c, b = config.TRIANGULAR_A_N
        else:
            if job_type == "H":
                a, c, b = config.TRIANGULAR_B_H
            else:
                a, c, b = config.TRIANGULAR_B_N
        return random.triangular(a, b, c)

    def _process_job(self, job: Dict):
        now = self.env.now
        next_h = self._next_h_arrival(now)

        a_queue_len = len(self.a_machine.queue)
        b_queue_len = len(self.b_machine.queue)
        a_in_service = self.a_machine.count
        b_in_service = self.b_machine.count

        machine = self.scheduler.decide_machine(
            job=job,
            now=now,
            a_queue_len=a_queue_len,
            a_in_service=a_in_service,
            b_queue_len=b_queue_len,
            b_in_service=b_in_service,
            next_h_arrival=next_h,
            h_in_b_system=self.h_in_b_system,
        )

        resource = self.a_machine if machine == "A" else self.b_machine
        priority = self.scheduler.priority(job, machine, now)

        if job["job_type"] == "H" and machine == "B":
            self.h_in_b_system += 1

        try:
            with resource.request(priority=priority) as req:
                yield req
                start_time = self.env.now
                duration = self._sample_process_time(job["job_type"], machine)
                yield self.env.timeout(duration)
                end_time = self.env.now
        finally:
            if job["job_type"] == "H" and machine == "B":
                self.h_in_b_system -= 1

        tardiness = max(0.0, end_time - job["due_date"])
        self.results.append(SimulationResult(
            job_id=job["job_id"],
            job_type=job["job_type"],
            arrival_time=job["arrival_time"],
            start_time=start_time,
            end_time=end_time,
            due_date=job["due_date"],
            tardiness=tardiness,
            machine=machine,
        ))

    def _job_arrival(self, job: Dict):
        yield self.env.timeout(job["arrival_time"])
        yield self.env.process(self._process_job(job))

    def run(self) -> List[SimulationResult]:
        random.seed(config.RANDOM_SEED)
        for job in self.jobs:
            self.env.process(self._job_arrival(job))
        self.env.run()
        return self.results


def summarize_results(results: List[SimulationResult]) -> Dict[str, float]:
    h_tardiness = [r.tardiness for r in results if r.job_type == "H"]
    n_tardiness = [r.tardiness for r in results if r.job_type == "N"]
    h_mean = sum(h_tardiness) / max(1, len(h_tardiness))
    n_mean = sum(n_tardiness) / max(1, len(n_tardiness))
    return {
        "mean_tardiness_h": h_mean,
        "mean_tardiness_n": n_mean,
    }
