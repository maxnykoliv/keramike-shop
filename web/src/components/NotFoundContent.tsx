import { ButtonLink } from "@/shared/ui";

export function NotFoundContent() {
  return (
    <div className="container-page flex flex-col items-start gap-6 py-24">
      <p className="t-label text-accent-strong">404</p>
      <h1 className="t-h1">Такої сторінки немає</h1>
      <p className="max-w-md text-text-muted">Можливо, товар зняли з продажу або посилання застаріло.</p>
      <div className="flex flex-wrap gap-3">
        <ButtonLink href="/catalog">До каталогу</ButtonLink>
        <ButtonLink href="/" variant="secondary">На головну</ButtonLink>
      </div>
    </div>
  );
}
