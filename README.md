# Recurring Rule Runner

Run async functions on a schedule defined using RRules from iCalendar RFC.

Example:
```python
import asyncio
from rrule_runner import AsyncRRuleRunner, Freq

runner = AsyncRRuleRunner()

@runner.register(freq=Freq.MINUTELY, interval=5)
async def job():
    print('Hello!')

asyncio.run(runner.run())
```