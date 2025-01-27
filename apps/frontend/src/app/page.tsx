'use client';
import { LoginButton } from '@/components/LoginButton';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { FileText, Brain, Lock, Zap } from 'lucide-react';

const FeatureCard = ({
  icon: Icon,
  title,
  description
}: {
  icon: React.ElementType;
  title: string;
  description: string;
}) => (
  <div className="rounded-xl bg-white p-6 shadow-lg transition-all duration-200 hover:shadow-xl">
    <div className="mb-4 inline-block rounded-lg bg-blue-50 p-3">
      <Icon className="h-6 w-6 text-blue-500" />
    </div>
    <h3 className="mb-2 text-lg font-semibold text-gray-900">{title}</h3>
    <p className="text-sm text-gray-600">{description}</p>
  </div>
);

export default function Home() {
  const { token, accountId, isAuthInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthInitialized && token) {
      router.replace(`${accountId}/dashboard`);
    }
  }, [isAuthInitialized]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center">
          <div className="mb-8 flex items-center justify-center">
            <div className="rounded-2xl bg-blue-500 p-3 shadow-lg">
              <FileText className="h-10 w-10 text-white" />
            </div>
          </div>
          <h1 className="bg-gradient-to-r from-blue-600 to-blue-400 bg-clip-text text-5xl font-bold text-transparent sm:text-6xl">
            DocuWatch
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-gray-600">
            Transform your contract management with AI-powered insights and
            real-time analytics
          </p>

          <div className="mt-8 flex justify-center">
            <LoginButton />
          </div>

          <div className="mt-4 text-sm text-gray-500">
            Secure authentication powered by DocuSign
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20">
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Brain}
              title="AI-Powered Analysis"
              description="Advanced machine learning algorithms analyze your contracts to extract key insights and identify potential risks."
            />
            <FeatureCard
              icon={Zap}
              title="Real-time Processing"
              description="Get instant insights as your documents are processed, with live updates and progress tracking."
            />
            <FeatureCard
              icon={Lock}
              title="Secure & Compliant"
              description="Enterprise-grade security ensures your sensitive contract data is protected at all times."
            />
          </div>
        </div>
      </div>
    </main>
  );
}
