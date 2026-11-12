import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-[#242036] px-5 py-14 text-white">
      <div className="mx-auto grid max-w-7xl gap-10 md:grid-cols-3">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="text-[#B9A5F5]" />
            <span className="text-xl font-bold">Aurevo</span>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-7 text-purple-200">
            Bringing clarity to freelance projects, communication and payments.
          </p>
        </div>

        <div>
          <h3 className="font-bold">Platform</h3>
          <div className="mt-4 space-y-3 text-sm text-purple-200">
            <a href="#features" className="block hover:text-white">Features</a>
            <a href="#how-it-works" className="block hover:text-white">How It Works</a>
            <a href="#security" className="block hover:text-white">Payment Security</a>
            <a href="#ai" className="block hover:text-white">AI Features</a>
          </div>
        </div>

        <div>
          <h3 className="font-bold">Join Aurevo</h3>
          <div className="mt-4 space-y-3 text-sm text-purple-200">
            <Link className="block hover:text-white" to="/client/register">For Clients</Link>
            <Link className="block hover:text-white" to="/freelancer/register">For Freelancers</Link>
            <Link className="block hover:text-white" to="/client/login">Client Login</Link>
            <Link className="block hover:text-white" to="/freelancer/login">Freelancer Login</Link>
          </div>
        </div>
      </div>

      <div className="mx-auto mt-12 max-w-7xl border-t border-white/10 pt-6 text-xs text-purple-300">
        © {new Date().getFullYear()} Aurevo. All rights reserved.
      </div>
    </footer>
  );
}