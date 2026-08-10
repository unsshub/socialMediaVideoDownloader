# Serve finished files by Job ID, never by user-supplied filename

The web UI links finished Videos through `/download/{job_id}`. The handler looks up the Job, resolves the stored filename against the Download Directory, and verifies the resolved real path stays inside that directory before streaming it.

We deliberately do not expose a `/files/{name}` endpoint that takes a filename from the browser, even with a traversal guard, because the guard is easy to forget on a future route. Resolving by Job ID removes raw path input from the request surface entirely. This is a security boundary on a server that runs as the user and reads arbitrary user-selected folders.
