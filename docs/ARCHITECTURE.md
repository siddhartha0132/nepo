# Architecture

The Vite React client calls FastAPI via `/api`. FastAPI seeds SQLite from committed schema/fixtures. Every priced endpoint calls one budget guard that records an overage negotiation and prevents confirmation until it is resolved. The assistant consumes selected records only.
