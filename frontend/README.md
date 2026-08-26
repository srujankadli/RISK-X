# RISK-X Frontend

React + Vite frontend for the RISK-X payment risk investigation system.

---

## Directory Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── App.jsx         # Minimal root UI & backend health verification
│   ├── index.css       # Base CSS styling
│   └── main.jsx        # React DOM render entrypoint
├── index.html          # HTML template
├── package.json        # Dependencies and build scripts
├── vite.config.js      # Vite configuration
└── README.md
```

---

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Vite Development Server
```bash
npm run dev
```

The application will run on `http://localhost:5173`.

### 3. Build for Production
```bash
npm run build
```
The output will be generated in the `dist/` directory.
