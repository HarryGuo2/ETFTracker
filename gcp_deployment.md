# Deploying ETF Tracker on Google Cloud VM

## Prerequisites

- Google Cloud account with a VM instance running
- VM external IP: 34.23.64.195
- VM zone: us-east1-b
- Project ID: etf-project-part2

## Step 1: Connect to your VM

1. Open the [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "Compute Engine" > "VM instances"
3. Find your VM instance (instance-1)
4. Click the "SSH" button next to your instance to open a browser-based SSH terminal

## Step 2: Update the VM and Install Dependencies

```bash
# Update packages
sudo apt-get update
sudo apt-get upgrade -y

# Install necessary packages
sudo apt-get install -y python3-pip python3-venv postgresql postgresql-contrib git

# Check if PostgreSQL is running
sudo systemctl status postgresql

# If PostgreSQL is not running, start it
sudo systemctl start postgresql
```

## Step 3: Clone Your Repository

```bash
# Create a directory for your application
mkdir -p ~/etf-tracker
cd ~/etf-tracker

# Clone your repository
git clone https://github.com/HarryGuo2/ETFTracker.git .
```

## Step 4: Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Configure Firewall Rules (if not already done)

Ensure port 8111 is open on your VM:

1. In the Google Cloud Console, go to "VPC Network" > "Firewall"
2. Click "CREATE FIREWALL RULE"
3. Name: "allow-flask"
4. Direction of traffic: "Ingress"
5. Targets: "All instances in the network"
6. Source filter: "IPv4 ranges"
7. Source IPv4 ranges: "0.0.0.0/0"
8. Protocols and ports: "Specified protocols and ports"
9. Check "TCP" and enter "8111"
10. Click "CREATE"

## Step 6: Run the Application

```bash
# Make sure you're in the application directory with the virtual environment activated
cd ~/etf-tracker
source venv/bin/activate

# Start the application
nohup python app.py > flask.log 2>&1 &

# Check if the application is running
ps aux | grep python
```

To view application logs:
```bash
tail -f flask.log
```

## Step 7: Access Your Application

Once everything is set up correctly, you should be able to access your application at:
http://34.23.64.195:8111/

## Troubleshooting

### If the application doesn't start:

1. Check application logs:
```bash
cat flask.log
```

2. Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

3. Test database connection:
```bash
python -c "import psycopg2; conn = psycopg2.connect(host='34.148.223.31', port='5432', database='proj1part2', user='hg2736', password='008096'); print('Connection successful')"
```

4. Check if port 8111 is being used:
```bash
sudo netstat -tulpn | grep 8111
```

5. Verify application is binding to the correct IP:
Make sure in app.py, your Flask app is binding to host='0.0.0.0'

### If you can't connect from your browser:

1. Verify VM external IP:
```bash
curl -4 icanhazip.com
```

2. Check firewall rules in GCP console
3. Try connecting from the VM itself:
```bash
curl http://localhost:8111
``` 