# LZ Celery Restart Tasks Automatically

## First attempt

At first it appeared that turning on [CELERY_TASK_ACKS_LATE](https://docs.celeryproject.org/en/latest/userguide/configuration.html#task-acks-late) and [CELERY_TASK_REJECT_ON_WORKER_LOST](https://docs.celeryproject.org/en/latest/userguide/configuration.html#task-reject-on-worker-lost) should do the trick. `CELERY_TASK_ACKS_LATE` means messages aren't acknowledged by workers until the job actually terminates, and `CELERY_TASK_REJECT_ON_WORKER_LOST` ensures that when a worker is killed with SIGKILL or SIGINT that the task will be rejected and re-queued. 

Unfortunately, what seems to happen in practice is that when you kill celery (and all docker services), when they come back up, those unacknowledged messages never get sent back out to workers. This seems to be a known issue with no fix other than "use rabbitmq": 

https://github.com/celery/celery/issues/3541
https://github.com/celery/celery/issues/4984
https://github.com/celery/celery/issues/5106

There is possibly one fix, but it didn't work for me, and could result in unwanted behavior - decreasing `visibility_timeout` for redis broker: 

https://stackoverflow.com/questions/41577723/if-celery-worker-dies-hard-does-job-get-retried

Unfortunately, if `task_acks_late` is enabled, it means workers do not ack messages until after the work completes. But if the work doesn't complete within visibility timeout, it will be sent out again. That seems like a Bad Thing ™. 

## Second attempt

Trying switching to RabbitMQ to see if this solves the issue. RabbitMQ seems to be the preferred and default broker for celery. One potentially gotcha to be aware of is that the rabbitmq-server apparently does not like to be killed forcefully, which is exactly what happens if it does not shut down within the default 10 second timeout that docker-compose gives services to shut down. 

After a very quick stab at this, it also does not seem to work.
