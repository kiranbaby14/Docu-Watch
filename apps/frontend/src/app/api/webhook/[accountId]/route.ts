// src/app/api/webhook/route.ts
import { NextRequest } from 'next/server';
import type { StoredWebhookMessage, WebhookMessage } from '@/types/webhook';

// Store messages in a map keyed by account_id
const webhookMessages = new Map<string, StoredWebhookMessage[]>();

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ accountId: string }> }
) {
  try {
    const accountId = (await params).accountId;
    const body = (await request.json()) as WebhookMessage;

    // Add timestamp and store message
    const storedMessage: StoredWebhookMessage = {
      ...body,
      timestamp: new Date().toISOString()
    };

    // Initialize array for this account if it doesn't exist
    if (!webhookMessages.has(accountId)) {
      webhookMessages.set(accountId, []);
    }

    // Add message to account-specific array
    webhookMessages.get(accountId)?.push(storedMessage);

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  } catch (error) {
    console.error('Webhook error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ accountId: string }> }
) {
  const accountId = (await params).accountId;

  const messages = webhookMessages.get(accountId) || [];

  return new Response(JSON.stringify(messages), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ accountId: string }> }
) {
  const accountId = (await params).accountId;

  // Clear the messages for the specified account_id
  webhookMessages.set(accountId, []);

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
}
