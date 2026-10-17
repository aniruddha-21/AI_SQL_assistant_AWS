# AI SQL Assistant on AWS

A Python web application for asking retail analytics questions and inspecting the SQL used to answer them. The application can run on an AWS EC2 instance and be accessed securely through an SSH tunnel.

## Features

- Browser-based query interface
- Rule-based mapping of common natural-language questions to SQL
- Direct execution of read-only `SELECT` and `WITH` queries
- Visible SQL, result rows, and query explanation
- SQLite database initialized with a small retail dataset on first launch
- Python standard library only; no third-party packages required

## AWS Deployment: EC2

### 1. Create an instance

Launch an Ubuntu EC2 instance. In its security group, allow SSH (TCP port 22) only from your current IP address. The web application listens on the instance's loopback interface, so do not add an inbound rule for its application port.

Keep the instance's public IPv4 address and the path to your SSH private key.

### 2. Install and start the application

Connect to the instance from a terminal on your computer:

```powershell
ssh -i .\your-key.pem ubuntu@EC2_PUBLIC_IP
```

Then, in the EC2 shell:

```bash
sudo apt update
sudo apt install -y git python3
git clone https://github.com/aniruddha-21/AI_SQL_assistant_AWS.git
cd AI_SQL_assistant_AWS
python3 app.py
```

Leave this terminal running. The application prints the local address it is listening on, normally `http://127.0.0.1:8012`. It tries ports `8012` through `8022` in order.

### 3. Open the application securely

In a second terminal on your computer, create an SSH tunnel. Use the port printed by the application in both places below:

```powershell
ssh -i .\your-key.pem -L 8012:127.0.0.1:8012 ubuntu@EC2_PUBLIC_IP
```

Keep the tunnel open and visit [http://127.0.0.1:8012](http://127.0.0.1:8012) in your browser. The browser connects through SSH; the application port does not need to be publicly exposed. Press `Ctrl+C` in each terminal to stop the application and tunnel.

## Run Locally

On Windows, open PowerShell in this folder and run:

```powershell
python app.py
```

Open the address printed in the terminal. The application uses the first available port from `8012` through `8022`.

## Architecture and Scope

The browser sends a question to the Python HTTP server. The server maps supported question patterns to SQL, checks submitted SQL for read-only operations, and executes the query against SQLite. On EC2, SSH port forwarding provides private browser access to the application.

The current implementation does not call Amazon Bedrock, Lambda, API Gateway, Athena, RDS, or CloudWatch. Natural-language interpretation is deterministic and limited to the patterns implemented in `generate_sql()` in `app.py`; it is not an LLM integration. The SQLite database and its generated dataset are stored on the machine running the application. Use an appropriate managed database, authentication, authorization, query controls, and monitoring before connecting business data or exposing the service to other users.
