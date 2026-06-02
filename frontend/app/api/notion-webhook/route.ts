import { NextRequest, NextResponse } from "next/server";

const N8N_WEBHOOK_URL =
  process.env.N8N_WEBHOOK_URL ||
  "http://localhost:5678/webhook/hscode-request";

// Notion sends webhook when a DB record changes.
// We buffer here and forward to n8n asynchronously so Notion doesn't timeout.
export async function POST(req: NextRequest) {
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  // Extract page info from Notion webhook payload
  const payload = body as Record<string, unknown>;
  const pageId: string =
    (payload.entity as Record<string, unknown>)?.id as string ||
    (payload.page_id as string) ||
    "";

  const properties = (payload.data as Record<string, unknown>)?.properties as Record<string, unknown> || {};
  const tenHangArr = (properties["Tên hàng"] as Record<string, unknown>)?.title as Array<Record<string, unknown>> || [];
  const tenHang: string = (tenHangArr[0]?.plain_text as string) || "";
  const trangThai = ((properties["Trạng thái"] as Record<string, unknown>)?.select as Record<string, unknown>)?.name as string || "";

  // Only process records with status "Chờ xử lý"
  if (trangThai && trangThai !== "Chờ xử lý") {
    return NextResponse.json({ ok: true, skipped: true, reason: "not pending" });
  }

  if (!pageId) {
    return NextResponse.json({ error: "missing page_id" }, { status: 400 });
  }

  // Fire-and-forget to n8n — don't await so Notion gets 200 immediately
  fetch(N8N_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ page_id: pageId, ten_hang: tenHang, raw: payload }),
  }).catch((err) => console.error("[notion-webhook] n8n forward error:", err));

  return NextResponse.json({ ok: true, queued: true, page_id: pageId });
}

// Notion may send GET to verify endpoint
export async function GET() {
  return NextResponse.json({ ok: true, service: "hermes-notion-buffer" });
}
