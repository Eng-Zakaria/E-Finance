import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon, ClockIcon, ShoppingBagIcon } from '@heroicons/react/24/outline';

const bnplOrders = [
  {
    id: '1',
    merchant: 'ElectroMart',
    item: 'MacBook Pro 14"',
    totalAmount: 1999.99,
    paidAmount: 500.00,
    remainingAmount: 1499.99,
    installments: 4,
    paidInstallments: 1,
    nextPayment: '2024-02-15',
    status: 'active',
  },
  {
    id: '2',
    merchant: 'Fashion Hub',
    item: 'Winter Collection Bundle',
    totalAmount: 450.00,
    paidAmount: 300.00,
    remainingAmount: 150.00,
    installments: 3,
    paidInstallments: 2,
    nextPayment: '2024-02-01',
    status: 'active',
  },
  {
    id: '3',
    merchant: 'Home Depot',
    item: 'Smart Home Kit',
    totalAmount: 799.00,
    paidAmount: 799.00,
    remainingAmount: 0,
    installments: 4,
    paidInstallments: 4,
    nextPayment: null,
    status: 'completed',
  },
];

const BNPL: React.FC = () => {
  const totalRemaining = bnplOrders.reduce((sum, o) => sum + o.remainingAmount, 0);
  const activeOrders = bnplOrders.filter((o) => o.status === 'active').length;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100">Buy Now, Pay Later</h1>
          <p className="text-dark-400 mt-1">Manage your installment plans</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <ShoppingBagIcon className="w-5 h-5" />
          Shop Now
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="stat-card">
          <p className="text-dark-400 text-sm mb-2">Available Credit</p>
          <p className="text-3xl font-bold text-dark-100">$5,000</p>
        </motion.div>
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }} className="stat-card">
          <p className="text-dark-400 text-sm mb-2">Outstanding Balance</p>
          <p className="text-3xl font-bold text-warning-500">${totalRemaining.toFixed(2)}</p>
        </motion.div>
        <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }} className="stat-card">
          <p className="text-dark-400 text-sm mb-2">Active Plans</p>
          <p className="text-3xl font-bold text-dark-100">{activeOrders}</p>
        </motion.div>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-dark-100">Your Plans</h2>
        {bnplOrders.map((order, index) => (
          <motion.div
            key={order.id}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.1 }}
            className="glass-card-hover p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-dark-100">{order.item}</h3>
                <p className="text-sm text-dark-400">{order.merchant}</p>
              </div>
              <span className={order.status === 'completed' ? 'badge-success' : 'badge-warning'}>
                {order.status === 'completed' ? (
                  <><CheckCircleIcon className="w-3 h-3 mr-1" /> Completed</>
                ) : (
                  <><ClockIcon className="w-3 h-3 mr-1" /> Active</>
                )}
              </span>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-dark-400">Progress</span>
                <span className="text-dark-200">{order.paidInstallments}/{order.installments} payments</span>
              </div>
              <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${order.status === 'completed' ? 'bg-success-500' : 'bg-primary-500'}`}
                  style={{ width: `${(order.paidInstallments / order.installments) * 100}%` }}
                />
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-dark-400">Remaining</p>
                <p className="text-lg font-semibold text-dark-100">${order.remainingAmount.toFixed(2)}</p>
              </div>
              {order.nextPayment && (
                <div className="text-right">
                  <p className="text-sm text-dark-400">Next Payment</p>
                  <p className="text-sm font-medium text-dark-200">{order.nextPayment}</p>
                </div>
              )}
              {order.status === 'active' && (
                <button className="btn-primary text-sm py-2 px-4">Pay Now</button>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default BNPL;

