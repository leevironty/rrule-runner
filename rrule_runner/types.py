from collections.abc import Callable, Coroutine, Iterable
from enum import IntEnum
from typing import Required, TypedDict

from dateutil import rrule

type CoroNone = Callable[[], Coroutine[None, None, None]]

Weekday = rrule.weekday


class Freq(IntEnum):
    SECONDLY = rrule.SECONDLY
    MINUTELY = rrule.MINUTELY
    HOURLY = rrule.HOURLY


class Weekdays:
    MO = rrule.MO
    TU = rrule.TU
    WE = rrule.WE
    TH = rrule.TH
    FR = rrule.FR
    SA = rrule.SA
    SU = rrule.SU


class RRuleKwargs(TypedDict, total=False):
    freq: Required[Freq]
    interval: int
    wkst: Weekday | int | None
    bysetpos: int | Iterable[int] | None
    bymonth: int | Iterable[int] | None
    bymonthday: int | Iterable[int] | None
    byyearday: int | Iterable[int] | None
    byeaster: int | Iterable[int] | None
    byweekno: int | Iterable[int] | None
    byweekday: int | Weekday | Iterable[int] | Iterable[Weekday] | None
    byhour: int | Iterable[int] | None
    byminute: int | Iterable[int] | None
    bysecond: int | Iterable[int] | None
