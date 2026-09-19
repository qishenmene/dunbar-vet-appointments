# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Client records: create clients and search active clients by name (DV-01, #1)
- Animal records: record animals (name, species, optional breed) against a
  client and list all animals belonging to one client (DV-03)
- Animal search: find animals by name across every client, returning every
  match with its owner and contact phone (DV-04)
- Property records: create, find, update and remove rural properties per
  client, with locality and gate/key/road access notes (DV-05)

### Planned for the sprint

- Client records: create, find, update, make inactive
- Animals per client: create, list, search by animal name
- Properties per client: create, find, update, remove
- In-clinic consultations: book one animal into a valid 15-minute room slot
- Farm visits: book against a property with start time and estimated hours
- Day views: clinic slot grid, ordered farm run list, per-client appointments
- Cancel/reschedule appointments with cancelled bookings kept visible

## [0.1.0] - 2026-09-13

### Added

- Flask application factory with environment-based configuration
  (`development`, `testing`, `production`) and `.env.example`
- SQLite database initialisation (`flask --app run.py init-db`)
- Health check endpoint (`/healthz`) and home page
- pytest setup with scaffold tests
- GitHub Actions CI (Python 3.11 / 3.12 / 3.13)
- Clean-checkout setup and deployment scripts for Windows and macOS/Linux
- Documentation: branching strategy, configuration management, deployment

[Unreleased]: https://github.com/qishenmene/dunbar-vet-appointments/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/qishenmene/dunbar-vet-appointments/releases/tag/v0.1.0
