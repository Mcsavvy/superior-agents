import app from "./app";
import http from "http";
import { connectDatabase } from "./config/database";
import { config } from "./config";

const server = http.createServer(app);

// Connect to database and start server
const startServer = async () => {
  try {
    await connectDatabase();

    server.listen(config.server.port, config.server.host, () => {
      console.log(
        `🚀 Server is running on ${config.server.host}:${config.server.port}`,
      );
      console.log(
        `📖 API Documentation available at http://${config.server.host}:${config.server.port}/api-docs`,
      );
      console.log(`🌍 Environment: ${config.server.nodeEnv}`);
      console.log(
        `📊 API Base URL: http://${config.server.host}:${config.server.port}${config.api.baseUrl}`,
      );
    });
  } catch (error) {
    console.error("Failed to start server:", error);
    process.exit(1);
  }
};

startServer();
