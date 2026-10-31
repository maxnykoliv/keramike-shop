import { NextResponse, type NextRequest } from "next/server";

/** The account requires login. The backend validates the session; this is just a fast redirect when there is no cookie. */
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
