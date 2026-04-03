# Freight SCM Database (Simple Setup)

This directory contains postgres db setup for the freight supply chain project.

## Features
- Schema creation
    - Users table (with hashed passwords)
    - System configuration table
- Examples to add data
- Examples to read data

## Prerequisites
- PostgreSQL installed
- `psql` CLI available

## How to run

Run this command:

```bash
psql -U postgres -f setup.sql