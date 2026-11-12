import Navbar from "../components/navigation/Navbar";
import Footer from "../components/navigation/Footer";

import Hero from "../components/landing/Hero";
import Features from "../components/landing/Features";
import HowItWorks from "../components/landing/HowItWorks";
import PaymentSecurity from "../components/landing/PaymentSecurity";
import AIFeatures from "../components/landing/AIFeatures";
import Testimonials from "../components/landing/Testimonials";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8F7FC]">
      <Navbar />

      <main className="mx-auto max-w-7xl px-5">
        <Hero />
        <Features />
        <HowItWorks />
        <PaymentSecurity />
        <AIFeatures />
        <Testimonials />
      </main>

      <Footer />
    </div>
  );
}