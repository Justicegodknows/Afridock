type PageHeaderProps = {
  kicker: string;
  title: string;
};

export function PageHeader({ kicker, title }: PageHeaderProps) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] uppercase tracking-[0.14em] text-accent">{kicker}</div>
      <h2 className="m-0 font-heading text-[26px]">{title}</h2>
    </div>
  );
}
