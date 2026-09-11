import Footer from "@/components/common/Footer";
import Navbar from "@/components/common/Navbar";
import ConsultationPreview from "@/components/landing/ConsultationPreview";
import FeatureCards from "@/components/landing/FeatureCards";
import Hero from "@/components/landing/Hero";
import HowItWorks from "@/components/landing/HowItWorks";
import TrustSection from "@/components/landing/TrustSection";

export default function Home() {
  return <><Navbar /><main><Hero /><ConsultationPreview /><FeatureCards /><HowItWorks /><TrustSection /></main><Footer /></>;
}
