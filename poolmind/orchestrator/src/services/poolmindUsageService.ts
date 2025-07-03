import { getPoolMindService } from "./index";
import {
  ContractCallOptions,
  DepositParams,
  WithdrawParams,
  TransferParams,
  UpdateNavParams,
  SetFeeRateParams,
  AdminWithdrawParams,
  AdminDepositParams,
  ContractState,
  TokenInfo,
} from "../types/contract";

/**
 * Service that demonstrates how to use the PoolMind contract service
 * This service provides higher-level functions for common operations
 */
export class PoolMindUsageService {
  private poolMindService = getPoolMindService();

  // ============================
  // USER OPERATIONS
  // ============================

  /**
   * Get user's PoolMind token balance and equivalent STX value
   */
  async getUserPortfolio(userAddress: string): Promise<{
    balance: number;
    stxValue: number;
    nav: number;
  }> {
    const [balanceResult, navResult] = await Promise.all([
      this.poolMindService.getBalance(userAddress),
      this.poolMindService.getNav(),
    ]);

    const balance = balanceResult.balance;
    const nav = navResult.nav;
    const stxValue = nav > 0 ? Math.floor((balance * nav) / 1000000) : 0;

    return {
      balance,
      stxValue,
      nav,
    };
  }

  /**
   * Deposit STX and get preview of shares to be minted
   */
  async depositWithPreview(
    params: DepositParams,
    options: ContractCallOptions,
  ): Promise<{
    estimatedShares: number;
    actualResult: any;
  }> {
    // Get preview of shares to be minted
    const estimatedShares =
      await this.poolMindService.calculateSharesForDeposit(params.amountStx);

    // Execute the deposit
    const actualResult = await this.poolMindService.deposit(params, options);

    return {
      estimatedShares,
      actualResult,
    };
  }

  /**
   * Withdraw with preview of STX to be received
   */
  async withdrawWithPreview(
    params: WithdrawParams,
    options: ContractCallOptions,
  ): Promise<{
    estimatedStx: number;
    actualResult: any;
  }> {
    // Get preview of STX to be received
    const estimatedStx = await this.poolMindService.calculateStxForWithdraw(
      params.amountShares,
    );

    // Execute the withdrawal
    const actualResult = await this.poolMindService.withdraw(params, options);

    return {
      estimatedStx,
      actualResult,
    };
  }

  /**
   * Transfer tokens with validation
   */
  async transferTokens(
    params: TransferParams,
    options: ContractCallOptions,
  ): Promise<any> {
    // Check if transfers are enabled
    const contractState = await this.poolMindService.getContractState();
    if (!contractState.transferable) {
      throw new Error("Token transfers are currently disabled");
    }

    // Check sender balance
    const senderAddress = this.getSenderAddress(options.senderKey);
    const balanceResult = await this.poolMindService.getBalance(senderAddress);

    if (balanceResult.balance < params.amount) {
      throw new Error("Insufficient balance for transfer");
    }

    return await this.poolMindService.transfer(params, options);
  }

  // ============================
  // ADMIN OPERATIONS
  // ============================

  /**
   * Update NAV with validation and history tracking
   */
  async updateNavSafely(
    params: UpdateNavParams,
    options: ContractCallOptions,
  ): Promise<any> {
    if (params.newNav <= 0) {
      throw new Error("NAV must be positive");
    }

    // Get current NAV for comparison
    const currentNav = await this.poolMindService.getNav();
    console.log(`Updating NAV from ${currentNav.nav} to ${params.newNav}`);

    return await this.poolMindService.updateNav(params, options);
  }

  /**
   * Pause contract with safety checks
   */
  async pauseContract(options: ContractCallOptions): Promise<any> {
    const contractState = await this.poolMindService.getContractState();

    if (contractState.paused) {
      throw new Error("Contract is already paused");
    }

    return await this.poolMindService.setPaused(true, options);
  }

  /**
   * Unpause contract with safety checks
   */
  async unpauseContract(options: ContractCallOptions): Promise<any> {
    const contractState = await this.poolMindService.getContractState();

    if (!contractState.paused) {
      throw new Error("Contract is not paused");
    }

    return await this.poolMindService.setPaused(false, options);
  }

  /**
   * Admin withdraw with balance validation
   */
  async adminWithdrawSafely(
    params: AdminWithdrawParams,
    options: ContractCallOptions,
  ): Promise<any> {
    const contractState = await this.poolMindService.getContractState();

    if (contractState.stxBalance < params.amount) {
      throw new Error("Insufficient contract balance for withdrawal");
    }

    console.log(`Admin withdrawing ${params.amount} uSTX from contract`);
    return await this.poolMindService.withdrawToAdmin(params, options);
  }

  /**
   * Set fee rates with validation
   */
  async setFeeRates(
    entryFeeRate: number,
    exitFeeRate: number,
    options: ContractCallOptions,
  ): Promise<{ entryResult: any; exitResult: any }> {
    // Validate fee rates (max 10% = 100 per 1000)
    if (entryFeeRate > 100 || exitFeeRate > 100) {
      throw new Error("Fee rates cannot exceed 10%");
    }

    const [entryResult, exitResult] = await Promise.all([
      this.poolMindService.setEntryFeeRate({ rate: entryFeeRate }, options),
      this.poolMindService.setExitFeeRate({ rate: exitFeeRate }, options),
    ]);

    return { entryResult, exitResult };
  }

  // ============================
  // INFORMATION SERVICES
  // ============================

  /**
   * Get comprehensive fund information
   */
  async getFundInfo(): Promise<{
    contractState: ContractState;
    tokenInfo: TokenInfo;
    performance: {
      totalValueLocked: number;
      sharePrice: number;
      totalShares: number;
    };
  }> {
    const [contractState, tokenInfo] = await Promise.all([
      this.poolMindService.getContractState(),
      this.poolMindService.getTokenInfo(),
    ]);

    const performance = {
      totalValueLocked: contractState.stxBalance,
      sharePrice: contractState.nav,
      totalShares: tokenInfo.totalSupply,
    };

    return {
      contractState,
      tokenInfo,
      performance,
    };
  }

  /**
   * Get NAV history for a range of IDs
   */
  async getNavHistory(
    startId: number,
    endId: number,
  ): Promise<
    Array<{
      id: number;
      nav: number;
      timestamp: number;
    } | null>
  > {
    const promises = [];
    for (let id = startId; id <= endId; id++) {
      promises.push(
        this.poolMindService
          .getNavHistoryById(id)
          .then((result) => (result ? { id, ...result } : null)),
      );
    }

    return await Promise.all(promises);
  }

  /**
   * Calculate deposit/withdrawal fees
   */
  async calculateFees(stxAmount: number): Promise<{
    entryFee: number;
    exitFee: number;
    netDepositAmount: number;
    netWithdrawAmount: number;
  }> {
    const contractState = await this.poolMindService.getContractState();

    const entryFee = Math.floor((stxAmount * contractState.entryFee) / 1000);
    const exitFee = Math.floor((stxAmount * contractState.exitFee) / 1000);

    return {
      entryFee,
      exitFee,
      netDepositAmount: stxAmount - entryFee,
      netWithdrawAmount: stxAmount - exitFee,
    };
  }

  // ============================
  // UTILITIES
  // ============================

  /**
   * Get sender address from private key (placeholder - implement based on your crypto library)
   */
  private getSenderAddress(senderKey: string): string {
    // This is a placeholder - implement based on your crypto library
    // For example, using @stacks/transactions:
    // return getAddressFromPrivateKey(senderKey, this.poolMindService.getNetworkName() as any);
    return "ST1PLACEHOLDER"; // Replace with actual implementation
  }

  /**
   * Format amounts for display
   */
  formatAmount(amount: number, decimals: number = 6): string {
    return (amount / Math.pow(10, decimals)).toFixed(decimals);
  }

  /**
   * Convert STX to uSTX
   */
  stxToUstx(stx: number): number {
    return Math.floor(stx * 1000000);
  }

  /**
   * Convert uSTX to STX
   */
  ustxToStx(ustx: number): number {
    return ustx / 1000000;
  }
}
