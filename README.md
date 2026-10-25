# Kolkata Night Sky Brightness: Before and After Diwali 2026

Measuring sky brightness in Kolkata and suburbs with a Canon 200D Mark II

Plan to measure and compare data one week before and after Diwali(8 Nov 2026)

Status: in progress. Code is being written and tested.

## Setup Instructions

1. Clone the repository and navigate to the project folder.
2. Create your local configuration file by copying the config.example.json to config.json:
   ```bash
   cp config.example.json config.json
3. Fill in your own data directory name, location and camera parameters in config.json
4. Create a `data/` folder in the project root containing three subfolders for your `.CR3` images:
   ```text
   data/
   ├── lights/      # Put your zenith raw frames here
   ├── darks/       # Put your dark calibration frames here
   ├── flats/       # Put your flat field frames here
   ├── flat_darks/  # Put your flat darks frames here