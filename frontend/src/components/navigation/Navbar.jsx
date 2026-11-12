import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Sparkles,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";

import Button from "../ui/Button";
import Modal from "../ui/Modal";
import MobileMenu from "./MobileMenu";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [mobile, setMobile] = useState(false);

  const navigate = useNavigate();

  const startAs = (role) => {
    setOpen(false);
    navigate(`/${role}/register`);
  };

  const links = [
    ["Features", "#features"],
    ["How It Works", "#how-it-works"],
    ["Security", "#security"],
    ["AI", "#ai"],
  ];

  return (
    <>
      <nav className="sticky top-0 z-40 border-b border-purple-100/60 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">

          <Link to="/" className="flex items-center gap-2">
            <div className="rounded-xl bg-[#7653D6] p-2 text-white">
              <Sparkles size={21} />
            </div>

            <span className="text-xl font-extrabold text-[#242036]">
              Aurevo
            </span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            {links.map(([label, href]) => (
              <a
                key={label}
                href={href}
                className="text-sm font-medium text-[#858096]
                transition hover:text-[#7653D6]"
              >
                {label}
              </a>
            ))}
          </div>

          <div className="hidden items-center gap-3 md:flex">
            <Link
              to="/client/login"
              className="text-sm font-semibold text-[#5535A5]"
            >
              Log in
            </Link>

            <Button onClick={() => setOpen(true)}>
              Get Started
              <ChevronRight size={17} />
            </Button>
          </div>

          <button
            className="md:hidden"
            onClick={() => setMobile(!mobile)}
            aria-label="Toggle navigation"
          >
            {mobile ? <X /> : <Menu />}
          </button>
        </div>

        {mobile && (
          <MobileMenu
            links={links}
            onNavigate={() => setMobile(false)}
            onGetStarted={() => { setMobile(false); setOpen(true); }}
          />
        )}
      </nav>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="How would you like to join?"
      >
        <p className="mb-6 text-sm text-[#858096]">
          Choose the workspace that matches your role.
        </p>

        <div className="space-y-4">

          <button
            onClick={() => startAs("client")}
            className="flex w-full items-center justify-between
            rounded-2xl border border-purple-100 p-5
            text-left transition hover:border-[#7653D6]
            hover:bg-purple-50"
          >
            <div>
              <h3 className="font-bold text-[#242036]">
                Continue as Client
              </h3>
              <p className="mt-1 text-xs text-[#858096]">
                Post projects and hire talented freelancers.
              </p>
            </div>
            <ChevronRight className="text-[#7653D6]" />
          </button>

          <button
            onClick={() => startAs("freelancer")}
            className="flex w-full items-center justify-between
            rounded-2xl border border-purple-100 p-5
            text-left transition hover:border-[#7653D6]
            hover:bg-purple-50"
          >
            <div>
              <h3 className="font-bold text-[#242036]">
                Continue as Freelancer
              </h3>
              <p className="mt-1 text-xs text-[#858096]">
                Discover projects and grow your career.
              </p>
            </div>
            <ChevronRight className="text-[#7653D6]" />
          </button>

        </div>
      </Modal>
    </>
  );
}