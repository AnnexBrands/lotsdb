Deploy lotsdb to production.

Steps:
1. Confirm the current branch is `main` and up to date with origin
2. SSH into the production server and pull latest + restart the service:
   ```
   ssh iq "cd /www/lotsdb && git pull && sudo systemctl restart lotsdb"
   ```
3. Report the result (success or failure)
