import { NextResponse, type NextRequest } from "next/server";

/** Кабінет лише після входу. Саму сесію перевіряє бекенд; тут — швидкий редирект без cookie. */
export function proxy(request: NextRequest) {
  if (!request.cookies.get("kr_session")) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(request.nextUrl.pathname + request.nextUrl.search)}`;
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/account/:path*"] };
