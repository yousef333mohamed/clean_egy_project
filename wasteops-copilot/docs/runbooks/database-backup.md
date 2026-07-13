# Database backup
## Symptoms
Scheduled backup is due or a release requires a checkpoint.
## Impact
Missing backups increase recovery point loss.
## Initial checks
Verify backup role, encrypted destination capacity, `age` recipient, retention, and latest restore test.
## Safe response
Run `backup.sh` with `PGPASSFILE`; never place a password on the command line. Upload artifact and checksum privately.
## Escalation
Alert database/security owners on failure, encryption error, or unexpected size.
## Recovery
Correct capacity/connectivity/permissions and rerun without deleting the previous valid artifact.
## Verification
Verify checksum, encryption, inventory timestamp, and scheduled isolated restore.
## Post-incident actions
Record success/failure metric and ticket recurring failures.
