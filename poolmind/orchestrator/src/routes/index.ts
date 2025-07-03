import { Router } from "express";
import authRoutes from "./auth.routes";
import balanceRoutes from "./balance.routes";

const router = Router();

// Authentication routes
router.use("/auth", authRoutes);

// Balance routes
router.use("/balance", balanceRoutes);

export default router;
