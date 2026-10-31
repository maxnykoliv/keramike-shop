import Image from "next/image";
import Link from "next/link";

export function Logo({ className }: { className?: string }) {
  return (
    <Link href="/" className={className} aria-label="Keramike — на головну">
      <Image src="/brand/logo.png" alt="Keramike" width={1091} height={177} priority
        className="h-6 w-auto md:h-7" sizes="180px" />
    </Link>
  );
}
