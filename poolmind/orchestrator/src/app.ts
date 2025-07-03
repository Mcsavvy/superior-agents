import express, { Application, Request, Response } from "express";
import path from "path";
import swaggerUi from "swagger-ui-express";
import swaggerSpec from "./docs/swagger";
import mainRouter from "./routes";
import { config } from "./config";

const app: Application = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Determine frontend build path based on environment
const isDevelopment = config.server.nodeEnv === "development";
const frontendBuildPath = isDevelopment
  ? path.join(__dirname, "../src/frontend/dist") // Development: relative to src/
  : path.join(__dirname, "./public"); // Production: frontend copied to dist/public

// Serve static files from the frontend build directory
app.use(express.static(frontendBuildPath));

// Health check endpoint (before API routes)
app.get("/health", (req: Request, res: Response) => {
  res.status(200).send("OK");
});

// Swagger UI
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// OpenAPI JSON schema endpoint for download
app.get("/api-docs.json", (req: Request, res: Response) => {
  res.setHeader("Content-Type", "application/json");
  res.setHeader(
    "Content-Disposition",
    'attachment; filename="poolmind-api-schema.json"',
  );
  res.send(swaggerSpec);
});

// API routes
app.use(config.api.baseUrl, mainRouter);

// Catch-all handler for client-side routing (must be last)
app.get("/*splat", (req: Request, res: Response): void => {
  // Don't serve index.html for API routes, docs, or if file not found
  if (
    req.path.startsWith("/api") ||
    req.path.startsWith("/api-docs") ||
    req.path.startsWith("/health")
  ) {
    res.status(404).json({ error: "Not found" });
    return;
  }

  // For all other routes, serve the React app
  res.sendFile(path.join(frontendBuildPath, "index.html"), (err?: Error) => {
    if (err) {
      res.status(500).json({ error: "Unable to serve frontend" });
    }
  });
});

export default app;
