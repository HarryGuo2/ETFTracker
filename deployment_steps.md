# Quick Deployment Steps for ETF Tracker

Follow these exact steps to deploy your application:

## 1. SSH into your VM

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "Compute Engine" > "VM instances"
3. Click the "SSH" button next to your instance (instance-1)

## 2. Clone and Set Up the Application

Run these commands:

```bash
# Update packages
sudo apt-get update

# Install Git and Python dependencies
sudo apt-get install -y python3-pip python3-venv git

# Create directory
mkdir -p ~/etf-tracker
cd ~/etf-tracker

# Clone the repository
git clone https://github.com/HarryGuo2/ETFTracker.git .

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 3. Verify Firewall Rule

1. In GCP Console, go to "VPC Network" > "Firewall"
2. Verify there's a rule allowing TCP port 8111
3. If not, create a new rule:
   - Name: "allow-flask"
   - Direction: "Ingress"
   - Targets: "All instances in the network"
   - Source: "0.0.0.0/0"
   - Protocols/ports: "TCP: 8111"

## 4. Start the Application

```bash
# Make sure you're in the right directory
cd ~/etf-tracker

# Activate virtual environment if not already active
source venv/bin/activate

# Start application in background with logging
nohup python app.py > flask.log 2>&1 &

# Verify it's running
ps aux | grep python
```

## 5. Access the Application

Open your browser and navigate to:
http://34.23.64.195:8111/

## Troubleshooting

If the application doesn't start or you can't connect:

1. Check logs: `cat flask.log`
2. Verify app is running: `ps aux | grep python`
3. Check if port is in use: `sudo netstat -tulpn | grep 8111`
4. Test connection locally: `curl http://localhost:8111`
5. Make sure app.py binds to 0.0.0.0 (not 127.0.0.1) 