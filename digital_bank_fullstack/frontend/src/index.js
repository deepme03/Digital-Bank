import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';

const App = () => {
  const [balance, setBalance] = React.useState(null);

  const getBalance = async () => {
    const res = await fetch('http://localhost:3001/balance/1');
    const data = await res.json();
    setBalance(data.balance);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Digital Bank</h2>
      <button onClick={getBalance}>Check Balance</button>
      {balance !== null && <p>Your balance is: ${balance}</p>}
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
