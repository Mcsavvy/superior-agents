import { request } from '@stacks/connect';
import { Cl } from '@stacks/transactions';

// Contract constants - adjust these to match your deployed contract
const CONTRACT_ADDRESS = import.meta.env.VITE_POOLMIND_CONTRACT_ADDRESS!; // Replace with your actual contract address
const CONTRACT_NAME = import.meta.env.VITE_POOLMIND_CONTRACT_NAME || 'poolmind';
const NETWORK = import.meta.env.VITE_STACKS_NETWORK!;

export interface DepositResult {
  txid: string;
  sharesMinted?: string;
}

export interface WithdrawResult {
  txid: string;
  stxReceived?: string;
}

/**
 * Deposit STX to the pool and receive PoolMind tokens
 */
export const depositToPool = async (amountStx: string): Promise<DepositResult> => {
  try {
    const response = await request('stx_callContract', {
      contract: `${CONTRACT_ADDRESS}.${CONTRACT_NAME}`,
      functionName: 'deposit',
      functionArgs: [Cl.uint(amountStx)],
      network: NETWORK,
    });

    return {
      txid: response.txid || '',
    };
  } catch (error) {
    console.error('Deposit failed:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to deposit');
  }
};

/**
 * Withdraw STX from the pool by burning PoolMind tokens
 */
export const withdrawFromPool = async (amountShares: string): Promise<WithdrawResult> => {
  try {
    const response = await request('stx_callContract', {
      contract: `${CONTRACT_ADDRESS}.${CONTRACT_NAME}`,
      functionName: 'withdraw',
      functionArgs: [Cl.uint(amountShares)],
      network: NETWORK,
    });

    return {
      txid: response.txid || '',
    };
  } catch (error) {
    console.error('Withdraw failed:', error);
    throw new Error(error instanceof Error ? error.message : 'Failed to withdraw');
  }
};