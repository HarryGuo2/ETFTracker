# Deploying ETF Tracker to Google Cloud

This guide will walk you through deploying your ETF Tracker application to Google Cloud Compute Engine.

## Prerequisites

- Google Cloud account with Compute Engine access
- GitHub repository with your ETF Tracker code (https://github.com/HarryGuo2/ETFTracker.git)
- Google Cloud VM instance already created

## Step 1: Make Port 8111 Accessible

1. Go to the Google Cloud Console: https://console.cloud.google.com/
2. Navigate to VPC Network -> Firewall
3. Click "CREATE FIREWALL RULE"
4. Fill in the following details:
   - Name: `allow-flask`
   - Description: `Allow Flask application traffic`
   - Targets: `All instances in the network`
   - Source filter: `IP ranges`
   - Source IP ranges: `0.0.0.0/0` (allows traffic from any IP)
   - Protocols and ports: Select `TCP` and enter `8111`
5. Click "Create"

## Step 2: Note Your VM's IP Address

1. In the Google Cloud Console, go to Compute Engine -> VM instances
2. Note the External IP address of your instance (e.g., 34.123.456.789)

## Step 3: SSH into Your VM

1. In the Google Cloud Console, click the "SSH" button next to your VM instance
2. Alternatively, if you have gcloud CLI set up, run:
   ```
   gcloud compute ssh --project=YOUR_PROJECT_ID --zone=YOUR_ZONE YOUR_VM_NAME
   ```

## Step 4: Set Up the Environment on Your VM

1. Once connected to your VM, activate your virtual environment (which you mentioned is already set up):
   ```
   source ~/env/bin/activate
   ```

2. If this is your first time deploying, clone your repository:
   ```
   git clone https://github.com/HarryGuo2/ETFTracker.git
   cd ETFTracker
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Step 5: Update Your Code

If you've already cloned the repository before, update to the latest version:
```
cd ETFTracker
git pull
```

## Step 6: Verify PostgreSQL is Running

Since your PostgreSQL database is on the same machine, make sure it's running:

```
sudo systemctl status postgresql
```

If it's not running, start it:
```
sudo systemctl start postgresql
```

You may need to verify that your database credentials in app.py match the local PostgreSQL setup. The current connection details are:

```python
DB_HOST = "34.148.223.31"
DB_PORT = "5432"
DB_NAME = "proj1part2"
DB_USER = "hg2736"
DB_PASSWORD = "008096"
DB_SCHEMA = "hg2736"
```

If you need to use different credentials on your VM, modify these settings in app.py.

## Step 7: Set Up the Database Tables (if needed)

If this is your first deployment, run the database setup script:
```
python fix_user_tables.py
```

## Step 8: Run the Application

Launch the Flask application:
```
python app.py
```

The application will run on port 8111.

## Step 9: Access Your Application

Open your web browser and go to:
```
http://YOUR_VM_IP:8111/
```
Replace `YOUR_VM_IP` with the external IP address you noted in Step 2.

## Troubleshooting

1. **Cannot access the application**: Ensure the firewall rule is correctly set up and the application is running.
2. **Database connection errors**: Verify your database connection details in app.py and ensure PostgreSQL is accessible.
3. **Application crashes**: Check the logs in the terminal where you're running the application.

## Keeping Your Application Running

To keep your application running after you disconnect from SSH, use `tmux`:

1. Start a new tmux session:
   ```
   tmux new -s etftracker
   ```

2. Run your application:
   ```
   python app.py
   ```

3. Detach from the session by pressing `Ctrl+B` followed by `D`

To reattach to your session later:
```
tmux attach -t etftracker
```

## Additional Notes

- Do not turn off your VM after deployment to ensure your IP address doesn't change
- Make sure your database credentials are properly set in your app.py file
- Consider setting up a proper web server (like Gunicorn + Nginx) for production use 