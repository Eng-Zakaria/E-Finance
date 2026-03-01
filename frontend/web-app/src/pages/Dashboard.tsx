import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  CreditCardIcon,
  BanknotesIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Dashboard: React.FC = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-dark-100">Dashboard</h1>
        <p className="text-dark-400 mt-1">Welcome back! Here's your financial overview.</p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <StatCard
          title="Total Balance"
          value="$124,580.00"
          change="+12.5%"
          isPositive
          icon={BanknotesIcon}
          gradient="from-primary-500 to-primary-600"
        />
        <StatCard
          title="Monthly Income"
          value="$8,250.00"
          change="+8.2%"
          isPositive
          icon={ArrowDownIcon}
          gradient="from-success-500 to-success-600"
        />
        <StatCard
          title="Monthly Expenses"
          value="$3,840.00"
          change="-2.4%"
          isPositive={false}
          icon={ArrowUpIcon}
          gradient="from-warning-500 to-warning-600"
        />
        <StatCard
          title="Active Cards"
          value="4"
          change="2 Virtual"
          icon={CreditCardIcon}
          gradient="from-accent-500 to-accent-600"
        />
      </motion.div>

      {/* Charts Row */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Balance History */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-dark-100">Balance History</h3>
            <select className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm text-dark-300">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Last 90 days</option>
            </select>
          </div>
          <div className="h-64">
            <Line
              data={{
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [
                  {
                    label: 'Balance',
                    data: [115000, 118000, 116500, 120000, 122000, 119500, 124580],
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#0ea5e9',
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  x: {
                    grid: { color: 'rgba(51, 65, 85, 0.5)' },
                    ticks: { color: '#94a3b8' },
                  },
                  y: {
                    grid: { color: 'rgba(51, 65, 85, 0.5)' },
                    ticks: {
                      color: '#94a3b8',
                      callback: (value) => `$${(Number(value) / 1000).toFixed(0)}k`,
                    },
                  },
                },
              }}
            />
          </div>
        </div>

        {/* Spending by Category */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-semibold text-dark-100 mb-6">Spending by Category</h3>
          <div className="h-48 flex items-center justify-center">
            <Doughnut
              data={{
                labels: ['Shopping', 'Food', 'Transport', 'Bills', 'Other'],
                datasets: [
                  {
                    data: [30, 25, 15, 20, 10],
                    backgroundColor: [
                      '#0ea5e9',
                      '#d946ef',
                      '#f59e0b',
                      '#10b981',
                      '#64748b',
                    ],
                    borderWidth: 0,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { color: '#94a3b8', padding: 12 },
                  },
                },
              }}
            />
          </div>
        </div>
      </motion.div>

      {/* Recent Transactions */}
      <motion.div variants={itemVariants} className="glass-card overflow-hidden">
        <div className="p-6 border-b border-dark-700/50">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-dark-100">Recent Transactions</h3>
            <button className="btn-ghost text-primary-400">View all</button>
          </div>
        </div>
        <div className="divide-y divide-dark-800">
          {transactions.map((tx, index) => (
            <TransactionRow key={index} transaction={tx} />
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

interface StatCardProps {
  title: string;
  value: string;
  change?: string;
  isPositive?: boolean;
  icon: React.ForwardRefExoticComponent<any>;
  gradient: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  isPositive,
  icon: Icon,
  gradient,
}) => (
  <div className="stat-card group">
    <div className="relative z-10">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {change && (
          <span
            className={`text-sm font-medium ${
              isPositive === undefined
                ? 'text-dark-400'
                : isPositive
                ? 'text-success-500'
                : 'text-danger-500'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      <p className="text-dark-400 text-sm mb-1">{title}</p>
      <p className="text-2xl font-bold text-dark-100">{value}</p>
    </div>
  </div>
);

interface Transaction {
  name: string;
  category: string;
  amount: number;
  date: string;
  status: 'completed' | 'pending' | 'failed';
}

const transactions: Transaction[] = [
  { name: 'Amazon Purchase', category: 'Shopping', amount: -89.99, date: 'Today, 2:30 PM', status: 'completed' },
  { name: 'Salary Deposit', category: 'Income', amount: 5200.00, date: 'Today, 9:00 AM', status: 'completed' },
  { name: 'Netflix Subscription', category: 'Entertainment', amount: -15.99, date: 'Yesterday', status: 'completed' },
  { name: 'Transfer to John', category: 'Transfer', amount: -250.00, date: 'Yesterday', status: 'pending' },
  { name: 'Grocery Store', category: 'Food', amount: -67.50, date: 'Dec 18', status: 'completed' },
];

const TransactionRow: React.FC<{ transaction: Transaction }> = ({ transaction }) => {
  const isCredit = transaction.amount > 0;

  return (
    <div className="table-row flex items-center justify-between px-6 py-4">
      <div className="flex items-center gap-4">
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center ${
            isCredit ? 'bg-success-500/20' : 'bg-dark-700'
          }`}
        >
          {isCredit ? (
            <ArrowDownIcon className="w-5 h-5 text-success-500" />
          ) : (
            <ArrowUpIcon className="w-5 h-5 text-dark-400" />
          )}
        </div>
        <div>
          <p className="font-medium text-dark-100">{transaction.name}</p>
          <p className="text-sm text-dark-400">{transaction.category}</p>
        </div>
      </div>
      <div className="text-right">
        <p className={`font-semibold ${isCredit ? 'text-success-500' : 'text-dark-100'}`}>
          {isCredit ? '+' : ''}{transaction.amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
        </p>
        <p className="text-sm text-dark-400">{transaction.date}</p>
      </div>
    </div>
  );
};

export default Dashboard;

