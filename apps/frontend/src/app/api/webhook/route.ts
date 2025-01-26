// src/app/api/webhook/route.ts
import { NextRequest } from 'next/server';
import type { StoredWebhookMessage, WebhookMessage } from '@/types/webhook';

// Store messages in memory (in production you might want to use a proper storage solution)
let webhookMessages: StoredWebhookMessage[] = [];

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as WebhookMessage;

    // Add timestamp and store message
    const storedMessage: StoredWebhookMessage = {
      ...body,
      timestamp: new Date().toISOString()
    };

    webhookMessages.push(storedMessage);

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

export async function GET(request: NextRequest) {
  return new Response(JSON.stringify(webhookMessages), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
}
