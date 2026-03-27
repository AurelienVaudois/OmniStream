# Dashboard Setup

## Prerequisites
- Node.js 18+ (https://nodejs.org/)

## Initialize the project

```bash
# From the OmniStream root directory, remove this placeholder and create the Next.js app:
rm -rf dashboard
npx create-next-app@latest dashboard --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

# Install additional dependencies
cd dashboard
npm install better-sqlite3 @tremor/react recharts
npm install -D @types/better-sqlite3

# Install Shadcn/ui
npx shadcn@latest init
```

## Key dependencies
- **better-sqlite3**: SQLite driver for Node.js (reads omnistream.db)
- **@tremor/react**: Dashboard components (KPI cards, charts)
- **recharts**: Advanced charts (heatmaps, scatter plots)
- **shadcn/ui**: UI component library (buttons, tables, filters)
