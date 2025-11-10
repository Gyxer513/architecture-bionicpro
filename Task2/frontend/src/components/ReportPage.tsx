import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

const ReportPage: React.FC = () => {
    const { keycloak, initialized } = useKeycloak();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [reportData, setReportData] = useState<any[]>([]);

    const fetchReport = async () => {
        if (!keycloak?.token || !keycloak.tokenParsed) {
            setError('Not authenticated');
            return;
        }

        const userId = keycloak.tokenParsed.sub;

        try {
            setLoading(true);
            setError(null);

            const response = await fetch(
                `${process.env.REACT_APP_API_URL}/reports?user_id=${userId}`,
                {
                    headers: { Authorization: `Bearer ${keycloak.token}` },
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }

            const data = await response.json();
            setReportData(data.records);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    if (!initialized) return <div>Loading...</div>;
    if (!keycloak.authenticated)
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
                <button onClick={() => keycloak.login()} className="px-4 py-2 bg-blue-500 text-white rounded">
                    Login
                </button>
            </div>
        );

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
            <div className="p-8 bg-white rounded shadow-md">
                <h1 className="text-2xl font-bold mb-6">Usage Reports</h1>
                <button
                    onClick={fetchReport}
                    disabled={loading}
                    className={`px-4 py-2 bg-blue-500 text-white rounded ${loading ? 'opacity-50' : 'hover:bg-blue-600'}`}
                >
                    {loading ? 'Loading...' : 'Get Report'}
                </button>
                {error && <div className="mt-4 text-red-600">{error}</div>}

                {reportData.length > 0 && (
                    <table className="mt-6 table-auto border">
                        <thead>
                        <tr>
                            <th className="border px-4 py-2">Order #</th>
                            <th className="border px-4 py-2">Total</th>
                            <th className="border px-4 py-2">Discount</th>
                        </tr>
                        </thead>
                        <tbody>
                        {reportData.map((row) => (
                            <tr key={row.id}>
                                <td className="border px-4 py-2">{row.order_number}</td>
                                <td className="border px-4 py-2">{row.total}</td>
                                <td className="border px-4 py-2">{row.discount}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default ReportPage;