import React from 'react';
import { motion } from 'framer-motion';
import { PlusIcon, EllipsisHorizontalIcon, ArrowUpRightIcon } from '@heroicons/react/24/outline';

const accounts = [
  {
    id: '1',
    name: 'Main Checking',
    number: '**** 4582',
    type: 'current',
    balance: 45820.50,
    currency: 'USD',
    status: 'active',
    isPrimary: true,
  },
  {
    id: '2',
    name: 'Savings Account',
    number: '**** 7891',
    type: 'savings',
    balance: 78650.00,
    currency: 'USD',
    status: 'active',
    interestRate: 2.5,
  },
  {
    id: '3',
    name: 'Investment Account',
    number: '**** 3456',
    type: 'fixed_deposit',
    balance: 25000.00,
    currency: 'USD',
    status: 'active',
    interestRate: 4.5,
    maturityDate: '2025-06-15',
  },
  {
    id: '4',
    name: 'Euro Account',
    number: '**** 9012',
    type: 'current',
    balance: 12500.00,
    currency: 'EUR',
    status: 'active',
  },
];

const Accounts: React.FC = () => {
  const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100">Accounts</h1>
          <p className="text-dark-400 mt-1">Manage your bank accounts</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <PlusIcon className="w-5 h-5" />
          New Account
        </button>
      </div>

      {/* Total Balance Card */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-card p-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-transparent to-accent-500/10" />
        <div className="relative z-10">
          <p className="text-dark-400 text-sm mb-2">Total Balance</p>
          <h2 className="text-4xl font-bold text-dark-100">
            ${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </h2>
          <p className="text-dark-400 mt-2">{accounts.length} Active Accounts</p>
        </div>
      </motion.div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {accounts.map((account, index) => (
          <motion.div
            key={account.id}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card-hover p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-dark-100">{account.name}</h3>
                  {account.isPrimary && (
                    <span className="badge-info">Primary</span>
                  )}
                </div>
                <p className="text-sm text-dark-400 mt-1">{account.number}</p>
              </div>
              <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                <EllipsisHorizontalIcon className="w-5 h-5 text-dark-400" />
              </button>
            </div>

            <div className="mb-4">
              <p className="text-2xl font-bold text-dark-100">
                {account.currency === 'EUR' ? '€' : '$'}
                {account.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-sm text-dark-400 capitalize">{account.type.replace('_', ' ')}</p>
            </div>

            {account.interestRate && (
              <div className="flex items-center gap-4 pt-4 border-t border-dark-700/50">
                <div>
                  <p className="text-xs text-dark-400">Interest Rate</p>
                  <p className="text-sm font-medium text-success-500">{account.interestRate}% APY</p>
                </div>
                {account.maturityDate && (
                  <div>
                    <p className="text-xs text-dark-400">Maturity</p>
                    <p className="text-sm font-medium text-dark-200">{account.maturityDate}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button className="flex-1 btn-secondary text-sm py-2">
                Details
              </button>
              <button className="flex-1 btn-primary text-sm py-2 flex items-center justify-center gap-1">
                Transfer
                <ArrowUpRightIcon className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default Accounts;

