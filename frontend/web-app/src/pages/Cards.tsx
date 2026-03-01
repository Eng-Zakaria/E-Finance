import React from 'react';
import { motion } from 'framer-motion';
import { PlusIcon, LockClosedIcon, WifiIcon } from '@heroicons/react/24/outline';

const cards = [
  {
    id: '1',
    type: 'debit',
    network: 'visa',
    lastFour: '4582',
    holderName: 'JOHN DOE',
    expiryMonth: 12,
    expiryYear: 27,
    status: 'active',
    isPhysical: true,
    dailyLimit: 5000,
    dailySpent: 1250,
    color: 'from-primary-600 via-primary-500 to-accent-500',
  },
  {
    id: '2',
    type: 'credit',
    network: 'mastercard',
    lastFour: '7891',
    holderName: 'JOHN DOE',
    expiryMonth: 6,
    expiryYear: 26,
    status: 'active',
    isPhysical: true,
    creditLimit: 10000,
    currentBalance: 2340,
    color: 'from-dark-700 via-dark-600 to-dark-700',
  },
  {
    id: '3',
    type: 'virtual',
    network: 'visa',
    lastFour: '3456',
    holderName: 'JOHN DOE',
    expiryMonth: 1,
    expiryYear: 25,
    status: 'active',
    isPhysical: false,
    dailyLimit: 500,
    dailySpent: 89,
    color: 'from-accent-600 via-accent-500 to-primary-500',
  },
];

const Cards: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100">Cards</h1>
          <p className="text-dark-400 mt-1">Manage your debit and credit cards</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <PlusIcon className="w-5 h-5" />
          New Card
        </button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
        {cards.map((card, index) => (
          <motion.div
            key={card.id}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.15 }}
          >
            {/* Card Visual */}
            <div
              className={`relative h-52 rounded-2xl bg-gradient-to-br ${card.color} p-6 shadow-xl overflow-hidden`}
            >
              {/* Background Pattern */}
              <div className="absolute inset-0 opacity-20">
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2" />
              </div>

              {/* Card Content */}
              <div className="relative h-full flex flex-col justify-between">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-white/70 text-xs uppercase tracking-wider mb-1">
                      {card.type} Card
                    </p>
                    {!card.isPhysical && (
                      <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full text-white">
                        Virtual
                      </span>
                    )}
                  </div>
                  <WifiIcon className="w-6 h-6 text-white/80 rotate-90" />
                </div>

                <div>
                  <p className="text-xl font-mono text-white tracking-widest mb-4">
                    •••• •••• •••• {card.lastFour}
                  </p>
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-white/60 text-xs mb-1">Card Holder</p>
                      <p className="text-white font-medium tracking-wide">{card.holderName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-white/60 text-xs mb-1">Expires</p>
                      <p className="text-white font-medium">
                        {String(card.expiryMonth).padStart(2, '0')}/{card.expiryYear}
                      </p>
                    </div>
                    <div className="w-12 h-8">
                      {card.network === 'visa' ? (
                        <span className="text-white text-xl font-bold italic">VISA</span>
                      ) : (
                        <div className="flex">
                          <div className="w-5 h-5 bg-red-500 rounded-full -mr-2 opacity-80" />
                          <div className="w-5 h-5 bg-orange-400 rounded-full opacity-80" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Card Controls */}
            <div className="glass-card mt-4 p-4">
              <div className="flex items-center justify-between mb-4">
                <span className={`badge ${card.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                  {card.status}
                </span>
                <button className="p-2 hover:bg-dark-700 rounded-lg transition-colors">
                  <LockClosedIcon className="w-5 h-5 text-dark-400" />
                </button>
              </div>

              {/* Spending Progress */}
              {card.dailyLimit && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-dark-400">Daily Spending</span>
                    <span className="text-dark-200">
                      ${card.dailySpent} / ${card.dailyLimit}
                    </span>
                  </div>
                  <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full transition-all"
                      style={{ width: `${(card.dailySpent! / card.dailyLimit) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              {card.creditLimit && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-dark-400">Credit Used</span>
                    <span className="text-dark-200">
                      ${card.currentBalance} / ${card.creditLimit}
                    </span>
                  </div>
                  <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-accent-500 rounded-full transition-all"
                      style={{ width: `${(card.currentBalance! / card.creditLimit) * 100}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button className="flex-1 btn-secondary text-sm py-2">Settings</button>
                <button className="flex-1 btn-primary text-sm py-2">View Details</button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default Cards;

