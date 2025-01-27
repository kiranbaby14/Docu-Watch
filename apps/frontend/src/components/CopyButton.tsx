import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip';

interface CopyButtonProps {
  value: string;
  displayValue?: string;
}

const CopyButton = ({ value, displayValue }: CopyButtonProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            onClick={handleCopy}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleCopy(e as any);
              }
            }}
            className="inline-flex cursor-pointer items-center gap-1 rounded bg-gray-100 px-2 py-1 font-mono text-sm text-gray-600 hover:bg-gray-200"
          >
            <span>{displayValue || value}</span>
            {copied ? (
              <Check className="h-3 w-3 text-green-500" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <div>{copied ? 'Copied!' : 'Copy to clipboard'}</div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default CopyButton;
