# healthy-udm

# Healthy UDM (UniFi Dream Machine Monitor)

A lightweight, containerized Python service that monitors a UniFi Dream Machine (UDM) for process degradation and automatically safely restarts the management interface without dropping network traffic.

Two symptoms of degradation are slow UI and mDNS not going across subnets anymore

## 1. The Problem

Over time, the web interface of the UniFi Dream Machine can become extremely sluggish or unresponsive. This is often accompanied by an accumulation of "zombie" processes (processes that have completed execution but still have an entry in the process table) and locked memory resources, typically stemming from the Java-based `unifi-os` controller software.

The brute-force solution is to reboot the entire router. However, a full reboot drops the internet connection, flushes routing tables, and breaks cross-subnet traffic. 

## 2. The Approach

`healthy-udm` takes a nicer approach to router maintenance. Instead of a full reboot, it operates as an isolated Docker container that performs the following automated loop:

1. **Monitors:** Connects to the UDM via SSH on a scheduled interval.
2. **Analyzes:** Scans the Linux process table specifically for the count of zombie (`Z` state) processes.
3. **Acts:** If the zombie count exceeds the defined threshold (default: 2), it executes `unifi-os restart`. This safely restarts the web UI and management services, clearing the locked resources **without** dropping the internet connection or internal network routing.
4. **Alerts:** Writes a record to the UDM's internal syslog and fires off an email notification to the administrator.

## 3. How to Test

This project includes a suite of unit tests using Python's `unittest` framework. The tests use "mocking" to simulate the SSH connection and Mail server, meaning **you can run these tests safely without accidentally restarting your real UDM.**

To run the tests locally:

1. Clone the repository to your machine.
2. Ensure you have Python 3 installed.
3. Navigate to the project root directory and run:

```bash
python3 -m unittest discover -s tests

## 4. Authentication nightmares
#The UDM is a bit weird when it come sto ssh access and teh only way that works both locally (under OSX) and in prod ((Ubuntu) was top use ssh keys )
