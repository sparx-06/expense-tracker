# Expense Tracker

A self-hosted web application for tracking event-based expenses like birthdays, anniversaries, trips, and holidays. Compare your spending over time and across different years.

## Features

- 📊 Track expenses by category (Birthday, Anniversary, Christmas, Trips, etc.)
- 📈 Compare spending year-over-year
- 💰 View analytics and totals
- 🏷️ Custom categories
- 📱 Responsive design for mobile and desktop
- 🔒 Self-hosted with Docker for privacy

## Quick Start with Docker

### Using Docker Compose

1. Create a `docker-compose.yml` file:

```yaml
services:
  expense-tracker:
    image: ghcr.io/sparx-06/expense-tracker:latest
    container_name: expense-tracker
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
    environment:
      - SQLALCHEMY_DATABASE_URI=sqlite:////app/data/expenses.db
    restart: unless-stopped
```

2. Run:
```bash
docker compose up -d
```

3. Access at `http://localhost:5000`

### Using Docker CLI

```bash
docker run -d \
  --name expense-tracker \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -e SQLALCHEMY_DATABASE_URI=sqlite:////app/data/expenses.db \
  --restart unless-stopped \
  ghcr.io/yourusername/expense-tracker:latest
```

## TrueNAS Installation

1. Create folder: `/mnt/DataStore/Apps/expense-tracker/`
2. Create `compose.yaml` in that folder with the docker-compose content above
3. In TrueNAS Apps → Custom App:
```yaml
include:
  - path: /mnt/DataStore/Apps/expense-tracker/compose.yaml
services: {}
```

## Usage

### Adding Expenses

1. Go to the **Expenses** tab
2. Fill in expense details (description, amount, date, category, notes)
3. Click "Add Expense"

### Viewing Analytics

1. Go to the **Analytics** tab
2. Filter by category (optional)
3. View year-over-year comparisons and totals

### Managing Categories

1. Go to the **Categories** tab
2. Add or delete categories as needed

## Data Persistence

All data is stored in a SQLite database in the mounted `./data` directory. Make sure to back up this directory regularly.

## Building from Source

```bash
git clone https://github.com/yourusername/expense-tracker.git
cd expense-tracker
docker build -t expense-tracker .
```

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Container**: Docker

## License

This project is provided as-is for personal use.
