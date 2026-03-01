import React from 'react';
import { motion } from 'framer-motion';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, PlusIcon } from '@heroicons/react/24/outline';

const cryptoAssets = [
  { symbol: 'BTC', name: 'Bitcoin', balance: 0.5234, value: 22435.67, change: 2.34, icon: '₿' },
  { symbol: 'ETH', name: 'Ethereum', balance: 3.7891, value: 8965.23, change: -1.12, icon: 'Ξ' },
  { symbol: 'USDT', name: 'Tether', balance: 5000.00, value: 5000.00, change: 0.01, icon: '₮' },
  { symbol: 'SOL', name: 'Solana', balance: 45.5, value: 4234.56, change: 5.67, icon: '◎' },
];

const Crypto: React.FC = () => {
  const totalValue = cryptoAssets.reduce((sum, a) => sum + a.value, 0);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100">Crypto Portfolio</h1>
          <p className="text-dark-400 mt-1">Manage your digital assets</p>
        </div>
        <div className="flex gap-3">
          <button className="btn-secondary">Swap</button>
          <button className="btn-primary flex items-center gap-2">
            <PlusIcon className="w-5 h-5" />
            Buy Crypto
          </button>
        </div>
      </div>

      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass-card p-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-accent-500/10 via-transparent to-primary-500/10" />
        <div className="relative z-10">
          <p className="text-dark-400 text-sm mb-2">Total Portfolio Value</p>
          <h2 className="text-4xl font-bold text-dark-100">
            ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </h2>
          <span className="text-success-500 text-sm font-medium">+$1,234.56 (3.2%) today</span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cryptoAssets.map((asset, index) => (
          <motion.div
            key={asset.symbol}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card-hover p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white text-xl font-bold">
                  {asset.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-dark-100">{asset.name}</h3>
                  <p className="text-sm text-dark-400">{asset.symbol}</p>
                </div>
              </div>
              <div className={`flex items-center gap-1 ${asset.change >= 0 ? 'text-success-500' : 'text-danger-500'}`}>
                {asset.change >= 0 ? <ArrowTrendingUpIcon className="w-4 h-4" /> : <ArrowTrendingDownIcon className="w-4 h-4" />}
                <span className="text-sm font-medium">{Math.abs(asset.change)}%</span>
              </div>
            </div>
            <div className="flex justify-between items-end">
              <div>
                <p className="text-sm text-dark-400">Balance</p>
                <p className="text-lg font-medium text-dark-100">{asset.balance} {asset.symbol}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-dark-400">Value</p>
                <p className="text-lg font-semibold text-dark-100">${asset.value.toLocaleString()}</p>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button className="flex-1 btn-secondary text-sm py-2">Sell</button>
              <button className="flex-1 btn-primary text-sm py-2">Buy</button>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default Crypto;

