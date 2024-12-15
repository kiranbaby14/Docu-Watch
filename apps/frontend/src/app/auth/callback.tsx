import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function DocuSignCallback() {
  const router = useRouter();

  useEffect(() => {
    const { code } = router.query;
    if (code) {
      // Exchange code for token
      fetch('/api/auth/docusign/callback?code=' + code)
        .then((res) => res.json())
        .then((data) => {
          // Store token
          localStorage.setItem('docusign_token', data.access_token);
          router.push('/contracts');
        });
    }
  }, [router.query]);

  return <div>Processing authentication...</div>;
}
