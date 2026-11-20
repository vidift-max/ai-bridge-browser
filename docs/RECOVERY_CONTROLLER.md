# Recovery Controller

Recovery recreates the browser runtime from durable metadata.

Recovery order: metadata -> tabs -> URLs -> readiness -> visible state. Pending actions remain queued until policy and readiness permit delivery.