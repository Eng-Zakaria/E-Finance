import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon,
  ArrowDownTrayIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';

const transactions = [
  { id: '1', reference: 'TXN20240119A1B2C3', type: 'transfer_out', amount: -500.00, currency: 'USD', description: 'Transfer to Jane Doe', status: 'completed', date: '2024-01-19T14:30:00' },
  { id: '2', reference: 'TXN20240119D4E5F6', type: 'deposit', amount: 3500.00, currency: 'USD', description: 'Salary Deposit', status: 'completed', date: '2024-01-19T09:00:00' },
  { id: '3', reference: 'TXN20240118G7H8I9', type: 'payment', amount: -125.50, currency: 'USD', description: 'Electric Bill Payment', status: 'completed', date: '2024-01-18T16:45:00' },
  { id: '4', reference: 'TXN20240118J0K1L2', type: 'card_purchase', amount: -89.99, currency: 'USD', description: 'Amazon.com Purchase', status: 'completed', date: '2024-01-18T11:20:00' },
  { id: '5', reference: 'TXN20240117M3N4O5', type: 'transfer_in', amount: 250.00, currency: 'USD', description: 'From Mike Johnson', status: 'completed', date: '2024-01-17T18:30:00' },
  { id: '6', reference: 'TXN20240117P6Q7R8', type: 'atm_withdrawal', amount: -200.00, currency: 'USD', description: 'ATM Withdrawal', status: 'completed', date: '2024-01-17T10:15:00' },
  { id: '7', reference: 'TXN20240116S9T0U1', type: 'crypto_buy', amount: -500.00, currency: 'USD', description: 'Bitcoin Purchase', status: 'pending', date: '2024-01-16T14:00:00' },
  { id: '8', reference: 'TXN20240116V2W3X4', type: 'bnpl_installment', amount: -75.00, currency: 'USD', description: 'BNPL Payment - ElectroMart', status: 'completed', date: '2024-01-16T00:00:00' },
];

const Transactions: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  const filteredTransactions = transactions.filter((tx) => {
    const matchesSearch = 
      tx.reference.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tx.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'all' || tx.type === selectedType;
    return matchesSearch && matchesType;
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      deposit: 'Deposit',
      withdrawal: 'Withdrawal',
      transfer_in: 'Transfer In',
      transfer_out: 'Transfer Out',
      payment: 'Payment',
      card_purchase: 'Card Purchase',
      atm_withdrawal: 'ATM',
      crypto_buy: 'Crypto Buy',
      bnpl_installment: 'BNPL',
    };
    return labels[type] || type;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100">Transactions</h1>
          <p className="text-dark-400 mt-1">View and manage your transaction history</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <ArrowDownTrayIcon className="w-5 h-5" />
          Export
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transactions..."
            className="input-field pl-12"
          />
        </div>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="input-field sm:w-48"
        >
          <option value="all">All Types</option>
          <option value="deposit">Deposits</option>
          <option value="transfer_out">Transfers Out</option>
          <option value="transfer_in">Transfers In</option>
          <option value="payment">Payments</option>
          <option value="card_purchase">Card Purchases</option>
          <option value="crypto_buy">Crypto</option>
        </select>
      </div>

      {/* Transactions Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-dark-800/50">
              <tr>
                <th className="table-header">Transaction</th>
                <th className="table-header">Reference</th>
                <th className="table-header">Type</th>
                <th className="table-header">Status</th>
                <th className="table-header text-right">Amount</th>
                <th className="table-header text-right">Date</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((tx, index) => (
                <motion.tr
                  key={tx.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="table-row cursor-pointer"
                >
                  <td className="table-cell">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        tx.amount > 0 ? 'bg-success-500/20' : 'bg-dark-700'
                      }`}>
                        {tx.amount > 0 ? (
                          <ArrowDownIcon className="w-5 h-5 text-success-500" />
                        ) : (
                          <ArrowUpIcon className="w-5 h-5 text-dark-400" />
                        )}
                      </div>
                      <span className="font-medium text-dark-100">{tx.description}</span>
                    </div>
                  </td>
                  <td className="table-cell">
                    <code className="text-xs text-dark-400 bg-dark-800 px-2 py-1 rounded">
                      {tx.reference}
                    </code>
                  </td>
                  <td className="table-cell">
                    <span className="badge-info">{getTypeLabel(tx.type)}</span>
                  </td>
                  <td className="table-cell">
                    <span className={tx.status === 'completed' ? 'badge-success' : 'badge-warning'}>
                      {tx.status}
                    </span>
                  </td>
                  <td className="table-cell text-right">
                    <span className={`font-semibold ${
                      tx.amount > 0 ? 'text-success-500' : 'text-dark-100'
                    }`}>
                      {tx.amount > 0 ? '+' : ''}
                      ${Math.abs(tx.amount).toFixed(2)}
                    </span>
                  </td>
                  <td className="table-cell text-right text-dark-400">
                    {formatDate(tx.date)}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredTransactions.length === 0 && (
          <div className="text-center py-12">
            <p className="text-dark-400">No transactions found</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Transactions;

