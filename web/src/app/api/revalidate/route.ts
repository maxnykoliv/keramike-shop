import { revalidateTag } from "next/cache";
import { NextResponse, type NextRequest } from "next/server";

import { serverEnv } from "@/env";

/** Lets the backend clear the catalog cache right after a product changes: POST {tag: "catalog"}. */
export async function POST(req: NextRequest) {
  const secret = serverEnv().REVALIDATE_SECRET;
  if (!secret || req.headers.get("x-revalidate-secret") !== secret) {
    return NextResponse.json({ code: "forbidden" }, { status: 403 });
  }
  const { tag } = (await req.json().catch(() => ({}))) as { tag?: string };
  if (!tag || !/^(catalog|product:[\w-]+)$/.test(tag)) {
    return NextResponse.json({ code: "bad_tag" }, { status: 400 });
  }
  revalidateTag(tag, "max");
  return NextResponse.json({ revalidated: tag });
}
