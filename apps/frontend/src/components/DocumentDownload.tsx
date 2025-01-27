import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface DocumentDownloadProps {
  envelopeId: string;
  documentId: string;
  fileName: string;
}

const DocumentDownload: React.FC<DocumentDownloadProps> = ({
  envelopeId,
  documentId,
  fileName
}) => {
  const { token } = useAuth();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent accordion from toggling
    try {
      setDownloading(true);
      setError(null);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/envelopes/${envelopeId}/documents/${documentId}/download`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const contentDisposition = response.headers.get('Content-Disposition');
      const serverFileName = contentDisposition
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : fileName;

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = serverFileName;

      document.body.appendChild(link);
      link.click();

      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
      console.error('Download error:', err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="inline-flex items-center gap-2">
      <div
        role="button"
        tabIndex={0}
        onClick={handleDownload}
        onKeyPress={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleDownload(e as any);
          }
        }}
        className={`inline-flex cursor-pointer items-center gap-2 rounded-md bg-blue-500 px-3 py-2 text-sm font-medium text-white hover:bg-blue-600 ${
          downloading ? 'opacity-50' : ''
        }`}
        aria-disabled={downloading}
      >
        <Download className="h-4 w-4" />
        {downloading ? 'Downloading...' : 'Download'}
      </div>
      {error && <span className="text-sm text-red-500">Download failed</span>}
    </div>
  );
};

export { DocumentDownload };
