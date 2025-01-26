// app/api/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Here you can handle the webhook data
    // For example, you might want to:
    // 1. Validate the webhook signature if needed
    // 2. Process the document download status
    // 3. Update your database or client state
    // 4. Trigger any necessary notifications

    console.log('Received webhook:', body);

    // You might want to emit a server-sent event or use websockets
    // to notify the frontend about updates

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// Optional: Handle verification requests if your webhook provider uses them
export async function GET(req: NextRequest) {
  return NextResponse.json({ status: 'ok' }, { status: 200 });
}
