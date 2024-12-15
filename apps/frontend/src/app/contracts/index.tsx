import { useEffect, useState } from 'react';

export default function Contracts() {
  const [contracts, setContracts] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('docusign_token');
    if (token) {
      fetch('/api/contracts', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      })
        .then((res) => res.json())
        .then((data) => setContracts(data));
    }
  }, []);

  return (
    <div>
      <h1>Your Contracts</h1>
      {contracts.map((contract) => (
        <div key={contract.envelopeId}>
          <h2>{contract.emailSubject}</h2>
          <p>Status: {contract.status}</p>
        </div>
      ))}
    </div>
  );
}
