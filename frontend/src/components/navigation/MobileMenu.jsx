import { Link } from "react-router-dom";
import Button from "../ui/Button";

export default function MobileMenu({ links, onNavigate, onGetStarted }) {
  return (
    <div className="space-y-4 border-t border-purple-100 bg-white p-5 md:hidden">
      {links.map(([label, href]) => (
        <a key={label} href={href} onClick={onNavigate} className="block text-sm font-medium text-[#5535A5]">
          {label}
        </a>
      ))}
      <div className="flex flex-col gap-3">
        <Link to="/client/login" onClick={onNavigate} className="text-sm font-semibold text-[#5535A5]">Client login</Link>
        <Link to="/freelancer/login" onClick={onNavigate} className="text-sm font-semibold text-[#5535A5]">Freelancer login</Link>
      </div>
      <Button className="w-full" onClick={onGetStarted}>Get Started</Button>
    </div>
  );
}
