import asyncio
import datetime
from collections.abc import Callable
from typing import Self, Unpack

from dateutil import rrule, tz

from rrule_runner.types import CoroNone, RRuleKwargs


class RRuleSchedule:
    """Defines a recurring schedule using the dateutil rrule system.

    This class wraps an rrule object to calculate time intervals between scheduled
    executions while maintaining optimal performance through cache management.
    """

    def __init__(self, rule: rrule.rrule, timezone: datetime.tzinfo) -> None:
        """Initialize the schedule.

        Prefer to use .from_rrule_kwargs, as that one handles
        setting the `dtstart` properly.
        """
        self.rule = rule
        self.timezone = timezone

    @classmethod
    def from_rrule_kwargs(
        cls, timezone: datetime.tzinfo | None = None, **kwargs: Unpack[RRuleKwargs]
    ) -> Self:
        """Create a schedule from a timestamp and rrule kwargs.

        This function also sets the timezone and dtstart automatically, based
        on the chosen frequency.
        """
        freq = kwargs['freq']

        _timezone = timezone if timezone is not None else tz.tzlocal()
        anchor = datetime.datetime.now(_timezone).replace(microsecond=0)
        if freq <= rrule.SECONDLY:
            anchor = anchor.replace(second=0)
        if freq <= rrule.MINUTELY:
            anchor = anchor.replace(minute=0)

        # cache will be reset whenever we update the dtstart time
        # -> No issues with the cache growing over time
        rule = rrule.rrule(**kwargs, dtstart=anchor, cache=True)
        return cls(rule=rule, timezone=_timezone)

    def next_after_delay(self) -> float | None:
        """Get time in seconds until next scheduled time.

        Also updates the dtstart attribute to ensure the rule.after
        calculation time does not grow. Updating the start also resets
        the cache, so this also keeps the cache small.

        Returns:
            The time in seconds until next scheduled time.
        """
        wall_time_now = datetime.datetime.now(self.timezone)
        wall_time_next = self.rule.after(wall_time_now, inc=False)
        # Update dtstart to be close to current time. This ensures the .after
        # calculation does not slow down and the cache does not grow over time
        new_dtstart: datetime.datetime | None = self.rule.before(
            wall_time_now, inc=True
        )
        if new_dtstart is not None:
            assert isinstance(new_dtstart, datetime.datetime), 'Unknown return type!'  # noqa: S101
            self.rule: rrule.rrule = self.rule.replace(dtstart=new_dtstart)
        if wall_time_next is None:
            return None
        assert isinstance(wall_time_next, datetime.datetime), 'Unknown return type!'  # noqa: S101
        delay = (wall_time_next - wall_time_now).total_seconds()
        return max(delay, 0)


class AsyncRRuleRunner:
    """Cron-like async job runner.

    First register the jobs to be scheduled with the .schedule decorator,
    then run the scheduler with .run.
    """

    def __init__(self) -> None:
        self.funcs: list[tuple[RRuleSchedule, CoroNone]] = []

    async def call_func(self, schedule: RRuleSchedule, func: CoroNone) -> None:
        """Call the function at the given schedule.

        Creates tasks instead of awaiting for the function execution. This
        is more robust with long-running jobs.

        Args:
            schedule: The schedule at which to run the jobs.
            func: The function to run as a job.
        """
        async with asyncio.TaskGroup() as task_group:
            while True:
                delay = schedule.next_after_delay()
                if delay is None:
                    # We don't have a next scheduled time anymore! The job is done.
                    break
                await asyncio.sleep(delay)
                task_group.create_task(func())

    def _register(self, schedule: RRuleSchedule, func: CoroNone) -> None:
        self.funcs.append((schedule, func))

    def register(
        self, timezone: datetime.tzinfo | None = None, **kwargs: Unpack[RRuleKwargs]
    ) -> Callable[[CoroNone], CoroNone]:
        """Register a function as a job to be scheduled.

        Use as a decorator. Kwargs as passed to Schedule.from_rrule_kwargs.

        Returns:
            The wrapped function.
        """
        schedule = RRuleSchedule.from_rrule_kwargs(timezone=timezone, **kwargs)

        def wrapper(func: CoroNone) -> CoroNone:
            self._register(schedule=schedule, func=func)
            return func

        return wrapper

    async def run(self) -> None:
        """Schedule the jobs for execution."""
        async with asyncio.TaskGroup() as task_group:
            for schedule, func in self.funcs:
                task_group.create_task(self.call_func(schedule=schedule, func=func))
