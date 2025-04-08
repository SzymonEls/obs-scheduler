# obs-scheduler
Video queue for OBS.

# Usage
- Create `.env` file (use `.env.example` as a template), fill it in
- To queue video immediately after previous one, set the start time to one second after the start of the previous video. The player will wait for the previous video to finish before starting the next one.