import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';

interface Contract {
  envelope_id: string;
  status: string;
  subject: string;
  sent_date: string;
  last_modified: string;
}

const ContractsList = () => {
  const { token } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await fetch('http://localhost:8000/contracts', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            // Handle token expiration
            // You might want to redirect to login or refresh the token
            throw new Error('Session expired');
          }
          throw new Error('Failed to fetch contracts');
        }

        const data = await response.json();
        setContracts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchContracts();
    }
  }, [token]);

  if (loading) {
    return <div>Loading contracts...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <div className="grid gap-4">
      {contracts.map((contract) => (
        <div
          key={contract.envelope_id}
          className="rounded-lg border p-4 shadow transition-shadow hover:shadow-md"
        >
          <h3 className="font-semibold">{contract.subject}</h3>
          <div className="mt-2 text-sm text-gray-600">
            <p>Status: {contract.status}</p>
            <p>Sent: {new Date(contract.sent_date).toLocaleDateString()}</p>
            <p>
              Last Modified:{' '}
              {new Date(contract.last_modified).toLocaleDateString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export { ContractsList };
