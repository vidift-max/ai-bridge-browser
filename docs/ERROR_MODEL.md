# Browser Error Model

Main-frame navigation errors are visible to the user and do not silently advance automation.

A failed page remains recoverable through reload/navigation. Pending actions remain durable until an explicit policy decides to cancel them.

Future remote control must consume these states rather than bypass them.
