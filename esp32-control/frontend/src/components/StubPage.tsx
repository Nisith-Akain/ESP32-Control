import "./StubPage.css";

interface StubPageProps {
  title: string;
  description: string;
}

/** Shared placeholder shell for routes whose real content lands in a later ticket. */
export default function StubPage({ title, description }: StubPageProps) {
  return (
    <section className="stub-page">
      <h1 className="stub-page__title">{title}</h1>
      <p className="stub-page__description">{description}</p>
    </section>
  );
}
