import { Router } from "express";
import { BalanceController } from "../controllers/balanceController";
import { authenticateToken, requireWallet } from "../middleware/auth";

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Balance
 *   description: API endpoints for retrieving authenticated user's token and wallet balances
 */

/**
 * Get authenticated user's PLMD token balance
 * GET /api/v1/balance/plmd
 */
router.get(
  "/plmd",
  authenticateToken,
  requireWallet,
  BalanceController.getPlmdBalance,
);

/**
 * Get authenticated user's STX wallet balance
 * GET /api/v1/balance/stx
 */
router.get(
  "/stx",
  authenticateToken,
  requireWallet,
  BalanceController.getStxBalance,
);

/**
 * Get authenticated user's complete balance information (PLMD and STX)
 * GET /api/v1/balance/all
 */
router.get(
  "/all",
  authenticateToken,
  requireWallet,
  BalanceController.getAllBalances,
);

export default router;
